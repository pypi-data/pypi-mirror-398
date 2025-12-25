"""
Abstract base class for jobs
"""

import abc
import asyncio
import collections
import functools
import os
import pickle
import re

import unidecode

from .. import constants, uis, utils

import logging  # isort:skip
_log = logging.getLogger(__name__)


def unless_job_is_finished(method):
    """
    Decorator for :class:`~.JobBase` methods that blocks calls to the decorated method if the
    job :attr:`~.JobBase.is_finished`

    If a job gets terminated early, the :class:`~.DaemonProcess` is usually still running and can be
    reporting information back to the main process by calling a callback method. If the callback
    method calls :meth:`~.JobBase.add_output`, for example, this raises a :class:`RuntimeError`
    because adding output on a finished job is a bad idea.

    This should only happen in error cases, and ignoring callbacks should be fine because we are
    only interested in shutting everyting down in a somewhat controlled manner.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.is_finished:
            return method(self, *args, **kwargs)

    return wrapper


def raise_if_finished(method):
    """
    Decorator for :class:`~.JobBase` methods that raises :class:`RuntimeError`
    if the job :attr:`~.JobBase.is_started` and :attr:`~.JobBase.is_finished`
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.is_started and self.is_finished:
            raise RuntimeError(f'Do not call {method.__name__}() if job is already finished: {self.name}')
        else:
            return method(self, *args, **kwargs)

    return wrapper


def raise_if_started(method):
    """
    Decorator for :class:`~.JobBase` methods that raises :class:`RuntimeError`
    if the job :attr:`~.JobBase.is_started`
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.is_started:
            raise RuntimeError(f'Do not call {method.__name__}() after job is started: {self.name}')
        else:
            return method(self, *args, **kwargs)

    return wrapper


def raise_if_terminated(method):
    """
    Decorator for :class:`~.JobBase` methods that raises :class:`RuntimeError` if the job
    :attr:`~.JobBase.is_terminated`
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.is_terminated:
            raise RuntimeError(f'Do not call {method.__name__}() after job is terminated: {self.name}')
        else:
            return method(self, *args, **kwargs)

    return wrapper


def raise_if_not_started(method):
    """
    Decorator for :class:`~.JobBase` methods that raises :class:`RuntimeError`
    if the job was not started
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.is_started:
            raise RuntimeError(f'Do not call {method.__name__}() before job is started: {self.name}')
        else:
            return method(self, *args, **kwargs)

    return wrapper


class JobBase(abc.ABC):
    """
    Base class for all jobs

    :param str home_directory: Directory that is used to store created files
    :param str cache_directory: Directory that is used to cache output
    :param str cache_id: See :attr:`cache_id`
    :param str ignore_cache: Whether cached output and previously created files
        should not be re-used
    :param bool no_output_is_ok: Whether the job can succeed without any
        :attr:`output`
    :param hidden: Whether to hide the job's output in the UI

        This can be a :class:`bool` or callable that takes no arguments and returns a :class:`bool`.
    :param bool autostart: Whether this job is started automatically
    :param bool guaranteed: Whether this job should run and finish even if other jobs fail
    :param precondition: Callable that gets no arguments and returns whether
        this job is enabled or disabled
    :param prejobs: Sequence of :attr:`prerequisite jobs <prejobs>`
    :param callbacks: Mapping of :attr:`signal` names to callable or sequence of
        callables to :meth:`~.signal.Signal.register` for that signal

    Any additional keyword arguments are passed on to :meth:`initialize`.

    If possible, arguments should be validated before creating a job instance.
    This means we can fail early before any sibling jobs have started doing
    expensive work (e.g. torrent creation) that has to be cancelled.
    """

    @property
    @abc.abstractmethod
    def name(self):
        """Internal name (e.g. for the cache file name)"""

    @property
    @abc.abstractmethod
    def label(self):
        """User-facing name"""

    def __repr__(self):
        infos = []

        state = []
        if not self.is_enabled:
            state.append('disabled')
        state.extend(
            name
            for name in ('enabled', 'started', 'terminated', 'finished')
            if getattr(self, f'is_{name}')
        )
        infos.append('+'.join(state))

        if self.exit_code is not None:
            infos.append(f'exit_code={self.exit_code!r}')

        if self.raised:
            infos.append(f'raised={self.raised!r}')

        return f'<{type(self).__name__} {self.name} {" ".join(infos)}>'

    @property
    def home_directory(self):
        """
        Directory that is used to store files (e.g. generated screenshots,
        torrent files, etc) or empty string

        The directory is guaranteed to exist.
        """
        if self._home_directory and not os.path.exists(self._home_directory):
            utils.fs.mkdir(self._home_directory)
        return self._home_directory

    @functools.cached_property
    def cache_directory(self):
        """
        Path to existing directory that stores :attr:`cache_file`

        Subclasses may use this directory for storing custom cache files.

        This directory is guaranteed to exist.
        """
        if not os.path.exists(self._cache_directory):
            utils.fs.mkdir(self._cache_directory)
        return self._cache_directory

    @property
    def ignore_cache(self):
        """Whether cached output and previously created files should not be re-used"""
        return self._ignore_cache

    @property
    def no_output_is_ok(self):
        """Whether the job can succeed without any :attr:`output`"""
        return self._no_output_is_ok

    @property
    def hidden(self):
        """
        Whether to hide this job's output in the UI

        This can also be set to a callable that takes no arguments and returns
        a :class:`bool` value.
        """
        if callable(self._hidden):
            return bool(self._hidden())
        else:
            return bool(self._hidden)

    @hidden.setter
    def hidden(self, hidden):
        self._hidden = hidden

    @property
    def kwargs(self):
        """Keyword arguments from instantiation as :class:`dict`"""
        return self._kwargs

    @property
    def autostart(self):
        """
        Whether this job is started automatically by the UI

        The UI must check this value before calling :attr:`start`.

        If this value is falsy, :meth:`start` must be called manually.
        """
        return self._autostart

    @property
    def is_guaranteed(self):
        """
        Whether this job should run and finish even if other jobs fail

        In effect, this means that calling :meth:`terminate` on a guaranteed job has no effect.
        """
        return self._is_guaranteed

    @property
    def precondition(self):
        """
        Callable that gets no arguments and returns whether this job should
        be :meth:`started <start>`

        See also :attr:`is_enabled`.
        """
        return self._precondition

    @precondition.setter
    def precondition(self, function):
        if self.is_started:
            raise RuntimeError('Cannot set precondition after job has been started')

        if not callable(function):
            raise TypeError(f'Not callable: {function!r}')
        self._precondition = function

    @property
    def prejobs(self):
        """
        Sequence of prerequisite :class:`jobs <upsies.jobs.base.JobBase>`

        All prejobs must be either :attr:`finished <is_finished>` or
        :attr:`disabled <is_enabled>` before this job can start.

        See also :attr:`is_enabled`.
        """
        return self._prejobs

    @prejobs.setter
    def prejobs(self, prejobs):
        if self.is_started:
            raise RuntimeError('Cannot set prejobs after job has been started')
        # Filter out jobs that are `None`.
        self._prejobs = tuple(prejob for prejob in prejobs if prejob)

    @property
    def is_enabled(self):
        """
        Whether this job is allowed to :meth:`start`

        A job is enabled if :attr:`precondition` returns anything truthy and all :attr:`prejobs` are
        either finished or disabled.

        This property must be checked by the UI every time any job finishes and when the
        `refresh_ui` :attr:`signal` is emitted. If this property is `True`, this job must be
        :meth:`started <start>` and displayed (unless it is :attr:`hidden`).
        """
        return (
            # Prejobs
            all(
                (prejob.is_finished or not prejob.is_enabled)
                for prejob in self.prejobs
            )
            # Precondition
            and self.precondition()
        )

    @property
    def signal(self):
        """
        :class:`~.signal.Signal` instance

        The following signals are added by the base class. Subclasses can add
        their own signals.

        ``started``
            Emitted by :meth:`start` if job is not disabled. Unlike ``running``, this signal is also
            emitted if output is read from cache and :meth:`run` is not called. Registered callbacks
            get the job instance as a positional argument.

        ``running``
            Emitted when a task for :meth:`run` was created by :meth:`start`. Unlike ``started``,
            this signal is only called if no cached output is read. Registered callbacks get the job
            instance as a positional argument.

        ``finished``
            Emitted when a job :attr:`is_finished`. A job is finished when all
            its tasks are done or cancelled or if cached output from a previous
            run is successfully read. Registered callbacks get the job
            instance as a positional argument.

        ``output``
            Emitted when :meth:`send` is called or when output is read from
            cache. Registered callbacks get the value passed to :meth:`send` as
            a positional argument.

        ``info``
            Emitted when :attr:`info` is set. Registered callbacks get the new
            :attr:`info` as a positional argument.

        ``warning``
            Emitted when :meth:`warn` is called. Registered callbacks get the
            value passed to :meth:`warn` as a positional argument.

        ``error``
            Emitted when :meth:`error` is called. Registered callbacks get the
            value passed to :meth:`error` as a positional argument.

        ``prompt``
            Emitted when :meth:`add_prompt` is called. Registered callbacks
            get the :class:`~.Prompt` instance passed to :meth:`add_prompt` as
            a positional argument. The user interface MUST subscribe to this
            signal and present dialogs to the user when it is emitted.

        ``refresh_ui``
            Emitted when the user interface should update the focused widget,
            remove any finished jobs, start the next interactive job, etc. The
            UI usually only does this when a job finishes. This signal allows
            a job to force the refresh immediately. For example, emitting this
            signal may be necessary when a series of :class:`~.uis.prompts`
            are added by the same job. Registered callbacks get no arguments.
        """
        return self._signal

    _siblings = []

    @property
    def siblings(self):
        """Map job names to job instances for all instantiated jobs"""
        return {
            job.name: job
            for job in type(self)._siblings
        }

    def receive_all(self, job_name, signal, *, only_posargs=False):
        """
        Iterate over `signal` emissions from another job

        This is a convenience wrapper around :attr:`siblings` and :meth:`~.Signal.receive_all`.

        These calls are mostly equivalent:

        .. code::

            job.siblings['other_job'].receive_all('some_signal')
            job.receive_all('other_job, 'some_signal')

        :raise ValueError: if no job has the name `job_name`
        """
        try:
            other_job = self.siblings[job_name]
        except KeyError as e:
            raise ValueError(f'No such job: {job_name!r}') from e
        else:
            return other_job.signal.receive_all(signal, only_posargs=only_posargs)

    def receive_one(self, job_name, signal, *, only_posargs=False):
        """
        Return the first `signal` emission from another job

        This is a convenience wrapper around :attr:`siblings` and :meth:`~.Signal.receive_one`.

        .. note:: Because this will always only return the first emission, you probably shouldn't
                  use this to receive signals that are emitted multiple times.

        These calls are equivalent:

        .. code::

            job.siblings['other_job'].receive_one('some_signal')
            job.receive_one('other_job, 'some_signal')

        :raise ValueError: if no job has the name `job_name`
        """
        try:
            other_job = self.siblings[job_name]
        except KeyError as e:
            raise ValueError(f'No such job: {job_name!r}') from e
        else:
            return other_job.signal.receive_one(signal, only_posargs=only_posargs)

    async def wait_for(self, job_name, signal):
        """
        Wait for `signal` from `job_name`

        This is a convenience wrapper around :attr:`siblings` and :meth:`~.Signal.wait_for`.

        .. note:: Because this will always only return the first emission, you probably shouldn't
                  use this to receive signals that are emitted multiple times.

        These calls are equivalent:

        .. code::

            job.siblings['other_job'].wait_for('some_signal')
            job.wait_for('other_job, 'some_signal')

        :raise ValueError: if no job has the name `job_name`
        """
        await self.receive_one(job_name, signal)

    def __init__(self, *, home_directory=None, cache_directory=None, cache_id='',
                 ignore_cache=False, no_output_is_ok=False, hidden=False, autostart=True,
                 guaranteed=False, precondition=None, prejobs=(), callbacks={}, **kwargs):

        # Internal state
        self._run_was_called = False
        self._is_started = False
        self._is_terminated = False
        self._exception = None
        self._output = []
        self._warnings = []
        self._errors = []
        self._info = ''
        self._tasks = []
        self._finalize_event = None

        # Arguments
        self._kwargs = kwargs
        self._home_directory = home_directory if home_directory else ''
        self._cache_directory = cache_directory if cache_directory else constants.DEFAULT_CACHE_DIRECTORY
        self._cache_id = cache_id
        self._ignore_cache = bool(ignore_cache)
        self._no_output_is_ok = bool(no_output_is_ok)
        self._hidden = hidden
        self._autostart = bool(autostart)
        self._is_guaranteed = bool(guaranteed)
        self.precondition = precondition if precondition is not None else (lambda: True)
        self.prejobs = prejobs

        self._signal = utils.signal.Signal(
            signals=(
                'started',
                'running',
                'output',
                'info',
                'warning',
                'error',
                'finished',
                'prompt',
                'refresh_ui',
            ),
        )
        self._signal.register('output', lambda output: self._output.append(str(output)))
        self._signal.register('warning', lambda warning: self._warnings.append(warning))
        self._signal.register('error', lambda error: self._errors.append(error))
        self._signal.record('output')

        type(self)._siblings.append(self)

        self.initialize(**kwargs)

        # Sometimes initialize() set self.name, so we have to call that first before we can set
        # self.signals.id.
        self.signal.id = f'{self.name}-job'

        # Add signal callbacks after `initialize` had the chance to add custom
        # signals.
        for signal_name, callback in callbacks.items():
            if callable(callback):
                self._signal.register(signal_name, callback)
            else:
                for cb in callback:
                    self._signal.register(signal_name, cb)

    def initialize(self):
        """
        Called by :meth:`__init__` with additional keyword arguments

        This method should handle its arguments and return quickly.
        """

    @abc.abstractmethod
    async def run(self):
        """
        Do the work

        This method is called by :meth:`start`. Its coroutine is passed to
        :meth:`add_task`.

        Any keyword arguments passed to :meth:`initialize` are available via
        :attr:`kwargs`.

        The job :attr:`is_finished` when all :meth:`added tasks
        <upsies.jobs.base.JobBase.add_task>` are done or cancelled. (See also
        :meth:`finalize` and :meth:`finalization`.)

        This method may call :meth:`add_task` if more tasks are required.
        """

    def start(self):
        """
        Load cached output if available, otherwise call :meth:`run`

        This method must be called by the UI if :attr:`autostart` is `True`.

        Nothing is done if the job is already
        :attr:`started <upsies.jobs.base.JobBase.is_started>`,
        :attr:`finished <upsies.jobs.base.JobBase.is_finished>`,
        :attr:`terminated <upsies.jobs.base.JobBase.is_terminated>`.
        or not :attr:`enabled <upsies.jobs.base.JobBase.is_enabled>`,
        """
        if self.is_started:
            # _log.debug('%s: Not starting already started job', self.name)
            return
        elif self.is_finished:
            # _log.debug('%s: Not starting finished job', self.name)
            return
        elif self.is_terminated:
            # _log.debug('%s: Not starting terminated job', self.name)
            return
        elif not self.is_enabled:
            # Job is waiting for prejob, precondition, etc
            # _log.debug(
            #     '%s: Not executing disabled job: prejobs=%s, precondition=%s',
            #     self.name,
            #     [f'{prejob.name}:' + 'finished' if prejob.is_finished else 'running' for prejob in self.prejobs],
            #     self.precondition(),
            # )
            return
        else:
            self._is_started = True
            self.signal.emit('started', self)

            cache_was_read = self._read_cache()
            if cache_was_read:
                _log.debug('%s: Using cached output', self.name)
                self._finish()
            else:
                _log.debug('%s: Running', self.name)
                self._run_was_called = True
                # Because self._tasks is empty and self.is_started is True,
                # we are technically finished (see is_finished property), so
                # we need to add the first task with _add_task(), which is
                # allowed to add tasks while the job is finished.
                self._add_task(self.run())
                self.signal.emit('running', self)

    @property
    def is_started(self):
        """
        Whether :meth:`start` was called while this job :attr:`is_enabled`

        .. note:: This does not mean that :meth:`run` was called. A job is
                  also considered to be started if output is read from cache.
        """
        return self._is_started

    # Adding tasks before start() is called is problematic because start()
    # determines if we are using cached output. If we are using cached output,
    # the job is finished immediately by start() and no added task is going to
    # be awaited.
    @raise_if_not_started
    @raise_if_finished
    @raise_if_terminated
    def add_task(self, coro, callback=None):
        """
        Run asynchronous coroutine in background task

        The job :attr:`is_finished` when all added tasks are done or cancelled.

        Any exceptions from `coro` are raised by :meth:`wait_finished` or made
        available via :attr:`raised`.

        :param coro: Any awaitable object
        :param callback: Callable that is called with the return value or
            exception of `coro`

            `callback` is not called if the task was cancelled.

        :return: :class:`asyncio.Task` instance
        """
        return self._add_task(coro, callback=callback)

    def _add_task(self, coro, callback=None):
        def callback_(task):
            try:
                # Remove task reference (this may finish the job)
                self._tasks.remove(task)

                # _finish() MUST be called. We don't want to do that in wait_finished() because it
                # may not be called at all. Doing it via add_done_callback() has the upside that it
                # is guaranteed to run. The downside is that this code is running after every task
                # is done, but it's cheap enough.
                if self.is_finished:
                    self._finish()

                # Get return value or exception from task.
                result = exception = None
                try:
                    exception = task.exception()
                except asyncio.CancelledError:
                    _log.debug('%s: Task was cancelled: %r', self.name, task)
                    task_was_cancelled = True
                else:
                    task_was_cancelled = False
                    if exception:
                        # Store exception to raise it later, e.g. in wait().
                        self.exception(exception)
                    else:
                        # Getting the result should not raise if
                        # task.exception() returned None.
                        result = task.result()

                _log.debug('%s: %d remaining tasks', self.name, len(self._tasks))
                # for task in self._tasks:
                #     _log.debug('   - %r', task)

                # Unless task was cancelled, call callback and store its exception.
                if callback and not task_was_cancelled:
                    _log.debug('%s: Calling %s callback %r with %r', self.name,
                               task.get_coro().__qualname__, callback, result or exception)
                    try:
                        callback(result or exception)
                    except BaseException as e:
                        _log.debug('%s: Handling exception from callback %r: %r', self.name, callback, e)
                        self.exception(e)

            except BaseException as e:
                # Exceptions from task callbacks seem to be completely ignored,
                # even if asyncio.get_event_loop().set_exception_handler() is
                # set.
                self.exception(e)

        task = utils.run_task(coro, callback=callback_)
        self._tasks.append(task)
        _log.debug('%s: Added task: %r', self.name, task)
        return task

    @raise_if_not_started
    @raise_if_finished
    @raise_if_terminated
    def add_prompt(self, prompt):
        """
        Create a dialog in the user interface

        :param prompt: :class:`~.prompts.Prompt` object that specifies the
            dialog and handles callbacks

        :return: `prompt` so the :meth:`add_prompt` call can be conveniently
            awaited to get the :attr:`~.prompts.Prompt.result`
        """
        _log.debug('%s: Adding prompt: %r', self.name, prompt)
        assert isinstance(prompt, uis.prompts.Prompt), f'Not a Prompt instance: {prompt!r}'
        self.add_task(prompt.wait())
        self.signal.emit('prompt', prompt)
        # If a single job adds multiple prompts one after the other, we must
        # refresh the UI or there can be focus issues.
        self.signal.emit('refresh_ui')
        return prompt

    async def wait_started(self):
        """
        Block until :meth:`start` is called successfully

        This is a convenience wrapper around :meth:`~.Signal.receive_one` that waits for the
        emission of the ``started`` :attr:`signal`.

        See :attr:`signal`.
        """
        await self.signal.wait_for('started')

    async def wait_running(self):
        """
        Block until :meth:`run` is called

        This is a convenience wrapper around :meth:`~.Signal.receive_one` that waits for the
        emission of the ``running`` :attr:`signal`.

        See :attr:`signal`.
        """
        await self.signal.wait_for('running')

    async def wait_finished(self):
        """
        Block until all :meth:`added tasks <upsies.jobs.base.JobBase.add_task>` are either done
        or cancelled and job :attr:`is_finished`

        But first, wait for any :attr:`prejobs` to finish and then check if :attr:`precondition`
        returns anything truthy. Then :meth:`wait_started` is called, so it is ok to call this
        method if the job was not started yet.

        If :meth:`finalization` was called, :meth:`finalize` must be called before this method
        returns.

        Any exception raised by tasks are ignored here. It can be accessed via :attr:`raised`.
        """
        # Wait for required jobs to finish first.
        for prejob in self.prejobs:
            if prejob.is_enabled:
                _log.debug('%s.wait_finished(): Waiting for prejob: %s', self.name, prejob.name)
                await prejob.wait_finished()
                _log.debug('%s.wait_finished(): Done waiting for prejob: %s', self.name, prejob.name)
            else:
                _log.debug('%s.wait_finished(): Not waiting for disabled prejob: %s', self.name, prejob.name)

        # Make sure the job is started before we wait for its tasks. If start() was not called yet,
        # there are no tasks and we return immediately before the job was even started. But if our
        # precondition isn't met, start() will not add any tasks and we also return immediately. If
        # the job is already started, `wait_started()` returns immediately.
        if self.precondition():
            await self.wait_started()

        # Every time we've awaited all tasks, we must check if someone added more tasks.
        while self._tasks:
            # We must yield control to the event loop here so self._add_task().callback_() can be
            # called, which removes tasks from self._tasks. This prevents an infinite loop where we
            # are gathering tasks that are done but can't be removed because we are always busy
            # gathering them.
            await asyncio.sleep(0)

            # Exceptions from tasks are handled in the task callback (see _add_task()). We can
            # safely ignore them here.
            # _log.debug('%s: Gathering %d tasks: %r', self.name, len(self._tasks), self._tasks)
            results = await asyncio.gather(*self._tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, BaseException):
                    _log.debug('%s: Ignoring exception while gathering tasks: %r', self.name, result)
        _log.debug('%s: All tasks gathered: %r', self.name, self._tasks)

        # If anyone is waiting for finalize() to be called, we are not finished until it is called.
        if self._finalize_event:
            await self._finalize_event.wait()

    def _finish(self):
        # This function must be called after all tasks are done and finalize() was called if anyone
        # is awaiting finalization(). This function must be called after the cache was read
        # successfully. This function must be called regardless of success or raised exceptions.
        _log.debug('%s: Finishing', self.name)

        # Some sanity checks
        assert self.is_finished, f'Job is not finished yet: {self._finalize_event=}, {self._tasks=}'
        emissions = dict(self.signal.emissions)
        assert 'finished' not in emissions, f'"finished" signal was already emitted: {emissions["finished"]}'

        _log.debug('%s: Emitting finished signal', self.name)
        self.signal.emit('finished', self)

        # Inform everyone that there won't be any further signals from this job.
        self.signal.stop()

        self._write_cache()

    def terminate(self, reason=None):
        """
        Cancel all :meth:`added tasks <upsies.jobs.base.JobBase.add_task>`

        Do nothing if job :attr:`is_finished` or :attr:`is_terminated`.

        :param reason: Why this job is terminated (only used for debugging)

        .. note: The tasks are still running after this method returns. If you need to wait for this
                 job to finish, call :meth:`wait_finished`.

        .. note: If this method is called from a task, the calling task is not cancelled. Therefore,
                 any task that calls :meth:`terminate` should terminate on its own soon and must not
                 rely on getting cancelled.
        """
        if not self.is_finished and not self._is_terminated:
            if self.is_guaranteed:
                _log.debug('%s: Not terminating guaranteed job (reason: %s)', self.name, reason)
            else:
                _log.debug('%s: Terminating (reason: %s)', self.name, reason)
                self._is_terminated = True

                # If this method is called by a task, we must make sure that task isn't cancelled
                # itself so it can keep cancelling other tasks. It is the calling task's
                # responsibility to properly terminate itself after calling terminate().
                try:
                    current_task = asyncio.current_task()
                except RuntimeError as e:
                    if 'no running event loop' in str(e).casefold():
                        current_task = None
                    else:
                        raise

                for task in self._tasks:
                    if task is not current_task:
                        _log.debug('%s: Cancelling %r', self.name, task)
                        task.cancel()
                    else:
                        _log.debug('%s: Not cancelling myself: %r', self.name, task)

                # Calling terminate() means the job has failed in some way and anyone awaiting
                # finalization() must not be left hanging. This includes any finalizaion() calls
                # that are made in the future!
                self.finalize()

    @property
    def is_terminated(self):
        """Whether :meth:`terminate` was called to end this job prematurely"""
        return self._is_terminated

    def finalize(self):
        """Unblock any calls awaiting :meth:`finalization` or :meth:`wait_finished`"""
        # NOTE: It must be possible to call finalize() before awaiting
        #       finalization() (which then returns immediately).
        if not self._finalize_event:
            self._finalize_event = asyncio.Event()

        if not self._finalize_event.is_set():
            _log.debug('%s: Finalizing', self.name)
            self._finalize_event.set()
        else:
            _log.debug('%s: Already finalized', self.name)

    async def finalization(self):
        """
        Block until :meth:`finalize` is called

        This is useful for interactive jobs that don't have running tasks at
        all times. You can simply ``await self.finalization()`` in :meth:`run`
        and call :meth:`finalize` later to finish the job.

        .. warning: It is important to await finalization in :meth:`run` or
            any other :meth:`added task <upsies.jobs.base.JobBase.add_task>`.
        """
        if not self._finalize_event:
            self._finalize_event = asyncio.Event()
        _log.debug('%s: Awaiting finalization', self.name)
        await self._finalize_event.wait()

    @property
    def is_finished(self):
        """
        Whether all tasks are done

        If :meth:`finalization` is awaited, :meth:`finalize` must also be
        called.

        Before this job is started, `None` is returned.
        """
        if self.is_started:
            return (
                # All tasks are done and removed by their callbacks.
                len(self._tasks) <= 0
                and (
                    # Nobody is waiting for finalize() to be called.
                    not self._finalize_event
                    # Someone was waiting for finalize() to be called and it was
                    # called.
                    or (
                        self._finalize_event
                        and self._finalize_event.is_set()
                    )
                )
            )

    @property
    def exit_code(self):
        """
        `0` if job was successful, ``> 0`` otherwise,
        `None` before job :attr:`is_finished`
        """
        if self.is_finished:
            if (
                    self.errors
                    or self.raised
                    or (not self.output and not self.no_output_is_ok)
            ):
                return 1
            else:
                return 0

    @raise_if_not_started
    @raise_if_finished
    @raise_if_terminated
    def add_output(self, output):
        """
        Append `output` to :attr:`output` and emit ``output`` signal

        .. note:: All output is converted to :class:`str`.
        """
        self.signal.emit('output', str(output))

    @property
    def output(self):
        """Immutable sequence of strings passed to :meth:`send`"""
        return tuple(self._output)

    @property
    def info(self):
        """
        String that is only displayed while the job is running and not part of the
        job's output

        Setting this property emits the ``info`` signal.
        """
        return self._info

    @info.setter
    def info(self, info):
        self._info = str(info)
        self.signal.emit('info', info)

    def warn(self, warning):
        """Append `warning` to :attr:`warnings` and emit ``warning`` signal"""
        self.signal.emit('warning', str(warning))

    @property
    def warnings(self):
        """
        Sequence of non-critical error messages the user can override or resolve

        Unlike :attr:`errors`, warnings do not imply failure.
        """
        return tuple(self._warnings)

    def clear_warnings(self):
        """Empty :attr:`warnings`"""
        self._warnings.clear()

    def error(self, error):
        """
        Append `error` to :attr:`errors`, emit ``error`` signal and
        :meth:`terminate` this job
        """
        self.signal.emit('error', error)
        self.terminate(reason=error)

    @property
    def errors(self):
        """
        Sequence of critical errors (strings or exceptions)

        By default, :attr:`exit_code` is non-zero if any errors were reported.
        """
        return tuple(self._errors)

    def exception(self, exception):
        """
        Make `exception` available as :attr:`raised` unless it is already set

        .. warning:: This method is mostly for internal use. Setting an exception
                     means you want to throw a traceback at the user.

        :param Exception exception: Exception instance (nothing is done if
            this argument is falsy)
        """
        if not exception:
            _log.debug('%s: Not setting exception: %r', self.name, exception)
        elif self._exception:
            _log.debug(
                '%s: Not setting exception: %r - Exception already set: %r',
                self.name, exception, self._exception,
            )
        else:
            _log.debug('%s: Setting exception: %r', self.name, exception)
            _log.exception(exception)
            self._exception = exception
            self.terminate(reason=exception)

    @property
    def raised(self):
        """Exception passed to :meth:`exception`"""
        return self._exception

    def _write_cache(self):
        """
        Store recorded signals in :attr:`cache_file`

        Emitted signals are serialized with :meth:`_serialize_cached`.

        :raise RuntimeError: if writing :attr:`cache_file` fails
        """
        if (
                # Only cache if we have produced fresh output.
                self._run_was_called
                # We have nothing to cache if no cached signals were fired yet.
                and self.signal.emissions_recorded
                # Do not cache failed jobs.
                and self.exit_code == 0
                # Do not cache if we have no place to store it.
                and self.cache_file
        ):
            emissions_serialized = self._serialize_cached(self.signal.emissions_recorded)
            _log.debug('%s: Caching emitted signals: %r', self.name, self.signal.emissions_recorded)
            try:
                with open(self.cache_file, 'wb') as f:
                    f.write(emissions_serialized)
                    f.write(b'\n')
            except OSError as e:
                msg = e.strerror if e.strerror else str(e)
                raise RuntimeError(f'Unable to write cache {self.cache_file}: {msg}') from e

    def _read_cache(self):
        """
        Read cached :attr:`~.signal.Signal.emissions_recorded` from :attr:`cache_file`

        Emitted signals are deserialized with :meth:`_deserialize_cached`.

        :raise RuntimeError: if :attr:`cache_file` exists and is unreadable

        :return: `True` if cache file was read, `False` otherwise
        """
        if not self.ignore_cache and self.cache_file and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    emissions_serialized = f.read()
            except OSError as e:
                msg = e.strerror if e.strerror else str(e)
                raise RuntimeError(f'Unable to read cache {self.cache_file}: {msg}') from e
            else:
                emissions_deserialized = self._deserialize_cached(emissions_serialized)
                _log.debug('%s: Replaying cached signals: %r', self.name, emissions_deserialized)
                if emissions_deserialized:
                    self.signal.replay(emissions_deserialized)
                    return True
        return False

    def _serialize_cached(self, emissions):
        """
        Convert emitted signals to cache format

        :param emissions: See :attr:`Signal.emissions`

        :return: :class:`bytes`
        """
        return pickle.dumps(emissions, protocol=0, fix_imports=False)

    def _deserialize_cached(self, emissions_serialized):
        """
        Convert return value of :meth:`_serialize_cached` back to emitted signals

        :param emissions_serialized: :class:`bytes` object

        :return: See :attr:`Signal.emissions`
        """
        return pickle.loads(emissions_serialized)

    _max_filename_len = 255

    @functools.cached_property
    def cache_file(self):
        """
        File path in :attr:`cache_directory` to store cached :attr:`output` in

        If this property returns `None`, cache is not read or written.
        """
        cache_id = self.cache_id
        if cache_id is None:
            return None
        elif not cache_id:
            filename = f'{self.name}.out'
        else:
            # Avoid file name being too long. 255 bytes seems common.
            # https://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits
            max_len = self._max_filename_len - len(self.name) - len('..out')
            cache_id_str = self._cache_id_as_string(cache_id)
            if len(cache_id_str) > max_len:
                cache_id_str = ''.join((
                    cache_id_str[:int(max_len / 2 - 1)],
                    '…',
                    cache_id_str[-int(max_len / 2 - 1):],
                ))
            filename = f'{self.name}.{cache_id_str}.out'
            filename = utils.fs.sanitize_filename(filename)
        return os.path.join(self.cache_directory, filename)

    @functools.cached_property
    def cache_id(self):
        """
        Any object that makes a job's output unique

        If this property returns `None`, :attr:`cache_file` is not read or
        written.

        If this property returns any other object, it is converted to a string
        and appended to :attr:`name`. Multibyte characters and directory
        delimiters are replaced.

        By default, the `cache_id` argument from initialization is used, which
        is an empty string by default.
        """
        return self._cache_id

    _object_without_str_regex = re.compile(r'^<.*>$')

    def _cache_id_as_string(self, value):
        # Mapping (dict, etc)
        if isinstance(value, collections.abc.Mapping):
            return ','.join((
                f'{self._cache_id_as_string(k)}={self._cache_id_as_string(v)}'
                for k, v in value.items()
            ))

        # Iterable / Sequence (list, tuple, etc)
        elif isinstance(value, collections.abc.Iterable) and not isinstance(value, str):
            return ','.join(
                self._cache_id_as_string(v)
                for v in value
            )

        # Use same cache file for absolute and relative paths if path exists
        elif (
                isinstance(value, (str, os.PathLike))
                and os.path.exists(value)
                and not os.path.isabs(value)
        ):
            return self._cache_id_as_string(os.path.realpath(value))

        else:
            value_string = str(value)
            if self._object_without_str_regex.search(value_string):
                # `value` has no proper string representation, which results in
                # random cache IDs. We don't want "<foo.bar object at 0x<RANDOM
                # ADRESS>>" in our cache ID.
                raise RuntimeError(f'{type(value)!r} has no string representation')
            else:
                # Convert non-ASCII characters to ASCII, i.e. use the same cache
                # file for "Foo" and "Föó" and "Fǫò".
                return unidecode.unidecode(value_string)
