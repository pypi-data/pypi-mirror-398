"""
Abstract base class for all tracker-specific stuff
"""

import abc
import asyncio
import collections
import functools
import inspect
import os
import types

from ... import __project_name__, errors, utils
from ._howto import Howto
from .rules import TrackerRuleBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class TrackerBase(abc.ABC):
    """
    Base class for tracker-specific operations, e.g. uploading

    :param options: User configuration options for this tracker,
        e.g. authentication details, announce URL, etc
    :type options: :class:`dict`-like
    """

    @property
    @abc.abstractmethod
    def TrackerJobs(self):
        """Subclass of :class:`~.TrackerJobsBase`"""

    @property
    @abc.abstractmethod
    def TrackerConfig(self):
        """Subclass of :class:`~.TrackerConfigBase`"""

    cli_arguments = {}
    """CLI argument definitions (see :attr:`.CommandBase.cli_arguments`)"""

    rules = None
    """
    Sequence of :class:`~.TrackerRuleBase` subclasses or `None`

    For convenience, this may also be a :class:`~.ModuleType` that provides
    :class:`~.TrackerRuleBase` subclasses.
    """

    def __init_subclass__(cls):
        super().__init_subclass__()

        # Turn cls.rules into sequence of TrackerRileBase subclasses.
        if isinstance(cls.rules, types.ModuleType):
            cls.rules = utils.subclasses(TrackerRuleBase, modules=(cls.rules,))
        elif isinstance(cls.rules, collections.abc.Iterable):
            cls.rules = tuple(cls.rules)
        elif cls.rules is None:
            cls.rules = ()
        else:
            raise TypeError(f'Invalid {cls.__name__}.rules: {cls.rules!r}')

    def __init__(self, options=None):
        self._options = options or {}
        self._signal = utils.signal.Signal(
            id=f'{self.name}-tracker',
            signals=(
                'warning',
                'error',
                'exception',
                'logging_in', 'login_failed', 'logged_in',
                'logging_out', 'logout_failed', 'logged_out',
            ),
        )

    @property
    @abc.abstractmethod
    def name(self):
        """Lower-case tracker name abbreviation for internal use"""

    @property
    @abc.abstractmethod
    def label(self):
        """User-facing tracker name abbreviation"""

    @property
    @abc.abstractmethod
    def torrent_source_field(self):
        """
        Torrents for this tracker get a ``source`` field with this value

        This is usually the same as :attr:`label`.
        """

    setup_howto_template = 'Nobody has written a setup howto yet.'
    """
    Step-by-step guide that explains how to make your first upload

    .. note:: This MUST be a class attribute and not a property.

    The following placeholders can be used in f-string format:

        - ``howto`` - :class:`~._howto.Howto` instance
        - ``tracker`` - :class:`~.TrackerBase` subclass
        - ``executable`` - Name of the executable that runs the application
    """

    @classmethod
    def generate_setup_howto(cls):
        """Fill in any placeholders in :attr:`setup_howto_template`"""
        return utils.string.evaluate_fstring(
            cls.setup_howto_template,
            howto=Howto(tracker_cls=cls),
            tracker=cls,
            executable=__project_name__,
        )

    @property
    def options(self):
        """
        Configuration options provided by the user

        This is the :class:`dict`-like object from the initialization argument
        of the same name.
        """
        return self._options

    @functools.cached_property
    def _tasks(self):
        return []

    def attach_task(self, coro, callback=None):
        """
        Run awaitable `coro` in background task

        :param coro: Any awaitable

        :param callback: Callable that is called with the task after `coro` returned

            .. warning:: `callback` must handle any exception raised by the task or it will be
                ignored.
        """
        def callback_(task):
            # We don't have to await this task in `await_tasks()`.
            self._tasks.remove(task)

            # Give `callback` the opportunity to handle task result/exception. Otherwise raise
            # exception, which will be handled by whatever asyncio's "unhandled exception" routine
            # (e.g. set_exception_handler()).
            if callback:
                callback(task)
            elif exception := task.exception():
                raise exception

        task = utils.run_task(coro, callback=callback_)
        self._tasks.append(task)
        _log.debug('%s: Attached task: %r', self.name, task)
        return task

    async def await_tasks(self):
        """Wait for all awaitables passed to :meth:`attach_task`"""
        for task in self._tasks:
            await task

    async def login(self, **credentials):
        """
        End user session by calling :attr:`_login`, which must be implemented by the subclass

        Set :attr:`is_logged_in` to `True` or `False`. Emit `logged_in` :attr:`signal` on success.

        Any keyword arguments are passed on to :meth:`_login`, e.g. to provide a 2FA one-time
        password.

        :meth:`_login` should raise :class:`~.TfaRequired` to get called again with a `tfa_otp`
        keyword argument. The `tfa_otp` value will be from a user prompt that asks for a 2FA
        one-time password. (See :meth:`~.TrackerJobsBase.login_job`.)

        :raise errors.RequestError: on failure
        :raise errors.TfaRequired: if login failed due to missing second factor
        """
        async with self._session_lock:
            # Check internal flag.
            if not self.is_logged_in:
                self.signal.emit('logging_in')
                try:
                    await self._login(**credentials)
                    await self.confirm_logged_in()
                except errors.RequestError as e:
                    _log.debug('Login failed: %r', e)
                    self._is_logged_in = False
                    self.signal.emit('login_failed', e)
                    raise
                else:
                    _log.debug('Logged in successfully')
                    self._is_logged_in = True
                    self.signal.emit('logged_in')

    async def still_logged_in(self):
        """
        Return whether we have a valid user session stored in :attr:`cookies_filepath`

        If no :attr:`cookies_filepath` is specified, return `None`.

        Otherwise, catch :class:`~.RequestError` from :meth:`confirm_logged_in` to check if we are
        logged in.

        If we are not logged in, call :meth:`delete_cookies_filepath`, emit the ``login_failed``
        :attr:`~.signal` and return `False`.

        If we are logged in, emit the ``logged_in`` :attr:`~.signal` and return `True`.
        """
        if self.cookies_filepath:
            try:
                await self.confirm_logged_in()
            except errors.RequestError as e:
                _log.debug('Failed to validate stored user session: %r: %r', self.cookies_filepath, e)
                self.delete_cookies_filepath()
                self._is_logged_in = False
                self.signal.emit('login_failed', f'Session is no longer valid: {e}')
                return False
            else:
                _log.debug('User session is still valid: %r', self.cookies_filepath)
                self._is_logged_in = True
                self.signal.emit('logged_in')
                return True
        else:
            _log.debug('No user session was stored: %r', self.cookies_filepath)

    async def logout(self, *, force=False):
        """
        End user session by calling :attr:`_logout`, which must be implemented by the subclass

        Set :attr:`is_logged_in` to `False` and emit `logged_out` :attr:`signal`, even if the logout
        request fails for some reason.

        If a :attr:`cookies_filepath` is provided, do nothing unless `force` is `True`.

        :raise errors.RequestError: on failure
        """
        if self.cookies_filepath and not force:
            _log.debug('%s: Not logging out because user session is stored: %r', self.name, self.cookies_filepath)
        else:
            async with self._session_lock:
                if self.is_logged_in:
                    caller = inspect.currentframe().f_back.f_code
                    _log.debug('%s: Logging out on behalf of %r', self.name, caller)
                    self.signal.emit('logging_out')
                    try:
                        await self._logout()
                    except errors.RequestError as e:
                        _log.debug('Logout failed: %r', e)
                        self.signal.emit('logout_failed', e)
                        raise
                    finally:
                        _log.debug('Logged out successfully')
                        self._is_logged_in = False
                        self.signal.emit('logged_out')

    @abc.abstractmethod
    async def _login(self):
        """
        Start user session

        :raise errors.RequestError: on any kind of failure
        """

    @abc.abstractmethod
    async def confirm_logged_in(self):
        """
        Check if we are logged in by doing a website request

        This method is called by :meth:`login` to make sure whatever :meth:`_login` did worked. It
        is also called by :meth:`still_logged_in`, which is used check if a stored user session is
        still working or if a new session must be started (e.g. because the cookie expired).

        :raise errors.RequestError: if we are not logged in
        """

    @abc.abstractmethod
    async def _logout(self):
        """
        End user session

        :raise errors.RequestError: on any kind of failure
        """

    @functools.cached_property
    def _session_lock(self):
        # Prevent multiple simultaneous login/logout attempts
        return asyncio.Lock()

    @property
    def is_logged_in(self):
        """
        Whether a user session is active

        This is a boolean flag that is set by :meth:`login` and :meth:`logout`.
        """
        return getattr(self, '_is_logged_in', False)

    @property
    def cookies_filepath(self):
        """
        User-defined file path that stores login session cookie(s) or `None` if no such file is
        specified

        Subclasses must include this in requests made to the tracker website if the tracker
        implementation uses traditional user sesssions via the website for submissions.

        If the tracker implementation uses an API, cookies should not be used in requests and this
        property can be ignored.
        """
        cookies_filepath = self.options.get('cookies_filepath')
        if cookies_filepath:
            return os.path.expanduser(cookies_filepath)

    def delete_cookies_filepath(self):
        """Delete :attr:`cookies_filepath` if it is provided and exists"""
        cookies_filepath = self.cookies_filepath
        if cookies_filepath:
            try:
                os.remove(cookies_filepath)
            except FileNotFoundError:
                pass
            else:
                _log.debug('%s: Cookies removed: %r', self.name, cookies_filepath)

    @abc.abstractmethod
    async def get_announce_url(self):
        """
        Get announce URL from :attr:`options` or tracker website

        .. warning:: You should expect that :meth:`login` was called first when implementing this
                     method and raise :class:`RuntimeError` if :attr:`is_logged_in` is `False`.

        :raise errors.RequestError: on any kind of failure
        """

    calculate_piece_size = None
    """
    :class:`staticmethod` that takes a torrent's content size and returns
    the corresponding piece size

    If this is `None`, the default implementation is used.
    """

    calculate_piece_size_min_max = None
    """
    :class:`staticmethod` that takes a torrent's content size and returns
    the corresponding allowed minimum and maximum piece sizes

    If this is `None`, the default implementation is used.
    """

    @abc.abstractmethod
    async def upload(self, tracker_jobs):
        """
        Upload torrent and other metadata from jobs

        :param TrackerJobsBase tracker_jobs: :attr:`TrackerJobs` instance
        """

    @property
    def signal(self):
        """
        :class:`~.signal.Signal` instance with the following signals:

        ``warning``
            Emitted when :meth:`warn` is called. Registered callbacks get the provided `warning`
            argument.

        ``error``
            Emitted when :meth:`error` is called. Registered callbacks get the provided `error`
            argument.

        ``exception``
            Emitted when :meth:`exception` is called. Registered callbacks get the provided
            `exception` argument.

        ``logging_in``
            Emitted by :meth:`login` when login is attempted. Registered callbacks get no arguments.

        ``login_failed``
            Emitted by :meth:`login` when login failed. Registered callbacks get a
            :class:`~.RequestError` exception.

        ``logged_in``
            Emitted by :meth:`login` when login succeeded. Registered callbacks get no arguments.

        ``logging_out``
            Emitted by :meth:`logout` when logout is attempted. Registered callbacks get no
            arguments.

        ``logout_failed``
            Emitted by :meth:`logout` when logout failed. Registered callbacks get a
            :class:`~.RequestError` exception.

        ``logged_out``
            Emitted by :meth:`logout` when logout succeeded. Registered callbacks get no arguments.
        """
        return self._signal

    def warn(self, warning):
        """
        Emit ``warning`` signal (see :attr:`signal`)

        Emit a warning for any non-critical issue that the user can choose to
        ignore or fix.
        """
        self.signal.emit('warning', warning)

    def error(self, error):
        """
        Emit ``error`` signal (see :attr:`signal`)

        Emit an error for any critical but expected issue that can't be
        recovered from (e.g. I/O error).
        """
        self.signal.emit('error', error)

    def exception(self, exception):
        """
        Emit ``exception`` signal (see :attr:`signal`)

        Emit an exception for any critical and unexpected issue that should be
        reported as a bug.
        """
        self.signal.emit('exception', exception)
