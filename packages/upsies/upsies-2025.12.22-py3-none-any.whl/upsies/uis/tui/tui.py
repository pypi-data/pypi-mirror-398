"""
Interactive text user interface and job manager
"""

import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window, to_container
from prompt_toolkit.output import create_output

from ...jobs import JobRunner
from . import jobwidgets, style

import logging  # isort:skip
_log = logging.getLogger(__name__)


class TUI:
    def __init__(self):
        self._jobrunner = JobRunner(id='TUI')
        self._widgets = {}     # Map job names to JobWidgetBase instances.
        self._containers = {}  # Map job names to prompttoolkit.Container instances.
        self._focused_job_name = None
        self._app = self._make_app()
        self._loop = asyncio.get_event_loop()
        self._unhandled_exception = None
        self._loop.set_exception_handler(self._handle_exception)

    def _handle_exception(self, loop, context):
        exception = context.get('exception')
        if exception:
            _log.debug('Caught unhandled exception: %r', exception)
            _log.debug('Unhandled exception context: %r', context)
            if not self._unhandled_exception:
                self._unhandled_exception = exception
                self._jobrunner.terminate(reason=f'Unhandled exception: {exception!r}')

    def _make_app(self):
        self._jobs_container = HSplit(
            # FIXME: Layout does not accept an empty list of children, so we add an initial empty
            #        Window that doesn't display anything.
            #        https://github.com/prompt-toolkit/python-prompt-toolkit/issues/1257
            children=[Window()],
            style='class:default',
        )
        self._layout = Layout(self._jobs_container)

        kb = KeyBindings()

        @kb.add('escape')
        @kb.add('c-g')
        @kb.add('c-q')
        @kb.add('c-c')
        def _(_event, self=self):
            self._jobrunner.terminate(reason='User terminated application')

        @kb.add('escape', 'I')
        def _(_event, self=self):
            _log.debug('=== CURRENT JOBS ===')
            for job in self._jobrunner.all_jobs:
                _log.debug(' %s (%d tasks):', job, len(job._tasks))
                for task in job._tasks:
                    _log.debug('   %r', task)

            _log.debug('Focused job: %r: %r', self._focused_job_name, self._focused_job)
            _log.debug('Focused widget [layout ]: %r', self._layout.current_control)
            _log.debug('Focused widget [focused]: %r', self._widgets.get(self._focused_job_name, None))
            _log.debug('Focused container: %r', self._containers.get(self._focused_job_name, None))
            _log.debug('Layout.has_focus(%r): %r', self._layout.current_control,
                       self._layout.has_focus(self._layout.current_control))

        return Application(
            # Write TUI to stderr if stdout is redirected. This is useful for allowing the user to
            # make decisions in the TUI (e.g. selecting an item from search results) while
            # redirecting the final output (e.g. an IMDb ID).
            output=create_output(always_prefer_tty=True),
            layout=self._layout,
            key_bindings=kb,
            style=style.style,
            full_screen=False,
            erase_when_done=False,
            mouse_support=False,
            # Determine the currently active job *after* Application was invalidated. At the time of
            # this writing, this is important so we don't try to focus widgets from a job that has
            # just finished, which can result in RuntimeErrors because signals cannot be emitted on
            # finished jobs.
            before_render=self._update_jobs_container,
        )

    def _add_jobs(self, jobs):
        for job in jobs:
            self._add_job(job)

        # Add job widgets to the main container widget.
        self._update_jobs_container()

        # Register signal callbacks. It's probably best to do this after all jobs were added so that
        # signals aren't emitted before all jobs are available.
        self._connect_jobs(jobs)

    def _add_job(self, job):
        self._jobrunner.add(job)
        self._widgets[job.name] = jobwidgets.JobWidget(job, self._app)
        _log.debug('Job widget: %r: widget=%r', job.name, self._widgets[job.name])
        self._containers[job.name] = to_container(self._widgets[job.name])
        _log.debug('Job widget: %r: container=%r', job.name, self._containers[job.name])

    def _connect_jobs(self, jobs):
        for job in jobs:
            # Every time a job finishes, other jobs can become enabled due to the dependencies on
            # other jobs or other conditions. We also want to display the next interactive job when
            # an interactive job is done.
            job.signal.register('finished', self._handle_job_finished)

            # A job can also signal explicitly that we should update the job widgets, e.g. to start
            # previously disabled jobs.
            job.signal.register('refresh_ui', self._refresh)

    def _handle_job_finished(self, finished_job):
        assert finished_job.is_finished, f'{finished_job.name} is actually not finished'

        # Start enabled but not yet started jobs and display the next interactive job. This also
        # generates the regular output if output from all jobs was read from cache and the TUI exits
        # immediately.
        self._refresh()

        # Terminate all jobs and exit if job finished with non-zero exit code.
        if finished_job.exit_code != 0:
            self._jobrunner.terminate(reason=f'Job failed: {finished_job.name}: {finished_job.raised!r}')

    def _refresh(self):
        self._jobrunner.start_more_jobs()
        self._update_jobs_container()
        self._app.invalidate()

    @property
    def _focused_job(self):
        if self._focused_job_name:
            return self._jobrunner[self._focused_job_name]

    # We accept one argument because `before_render` calls this method with the Application
    # instance.
    def _update_jobs_container(self, _=None):
        # Unfocus focused job if it is finished.
        if self._focused_job and self._focused_job.is_finished:
            # _log.debug('UPDATE JOB CONTAINER: Unfocusing: %r', self._focused_job_name)
            self._focused_job_name = None

        enabled_jobs = self._jobrunner.enabled_jobs
        # _log.debug('UPDATE JOB CONTAINER: Enabled jobs: %r', [job.name for job in enabled_jobs])

        # Don't change focus if we already have a focused job. If another job becomes interactive
        # asynchronously (e.g. because a background job finished), it must not steal focus from the
        # currently focused job.
        if not self._focused_job_name:
            # Focus next interactive job.
            for job in enabled_jobs:
                if (
                        job.is_started
                        and not job.is_finished
                        and self._widgets[job.name].is_interactive
                ):
                    # _log.debug('UPDATE JOB CONTAINER: Focusing next interactive job: %s', job.name)
                    self._focused_job_name = job.name
                    break
        #     else:
        #         _log.debug('UPDATE JOB CONTAINER: No focusable widget found: %r', [
        #             {
        #                 'name': job.name,
        #                 'is_started': job.is_started,
        #                 'is_finished': job.is_finished,
        #                 'is_interactive': self._widgets[job.name].is_interactive,
        #             }
        #             for job in enabled_jobs
        #         ])
        # else:
        #     _log.debug('UPDATE JOB CONTAINER: Preserving focus: %r', self._focused_job_name)

        # Display focused job, finished jobs and all background jobs.
        self._jobs_container.children[:] = (
            self._containers[job.name]
            for job in enabled_jobs
            if (
                job.name == self._focused_job_name
                or job.is_finished
                or not self._widgets[job.name].is_interactive
            )
        )

        if self._focused_job_name:
            # Actually focus the focused job.
            try:
                self._layout.focus(self._containers[self._focused_job_name])
            except ValueError:
                # A job may hardcode `is_interactive = True` even though it currently is not
                # focusable. This happens, for example, if the job is still autodetecting before the
                # user can fix or confirm the autodetected value. In that case, we can either wait
                # for the job to become focusable or focus another interactive job in the meantime.
                pass

    async def run(self, jobs):
        """
        Block while `jobs` are running and the user interface is up

        :param jobs: Iterable of :class:`~.jobs.base.JobBase` instances

        :raise: any :class:`Exception` from any job or the user interface

        :return: :attr:`~.JobBase.exit_code` from the first failed job or ``0`` if all jobs
            succeeded
        """
        # Run the TUI in a background task that can be cancelled. This makes it easier to terminate
        # self._app.run_async() and get an exception from it.
        self._app_task = self._loop.create_task(
            self._app.run_async(set_exception_handler=False)
        )
        _log.debug('============ TUI is now running ============')

        # Add jobs to our JobRunner and create TUI widgets for them.
        self._add_jobs(jobs)

        # Start initially enabled jobs. This must be done asynchronously because we need a running
        # asyncio event loop for JobBase.add_task(), which is called by JobBase.start().
        self._jobrunner.start_more_jobs()

        # Wait for jobs to finish.
        await self._jobrunner.wait()
        _log.debug('All jobs finished:')
        for job in self._jobrunner.all_jobs:
            _log.debug(' * %r', job)

        # Wait for application task.
        self._app_task.cancel()
        try:
            await self._app_task
        except asyncio.CancelledError:
            pass
            # self._jobrunner.terminate(reason=f'Application was cancelled: {self._app_task!r}')
        _log.debug('============ TUI has stopped running ============')

        # Raise any stored exception.
        self._maybe_raise_exception()

        # Return application exit code (e.g. 0=success, 1=failure).
        return self._get_exit_code()

    def _maybe_raise_exception(self):
        if self._unhandled_exception:
            # Some task raised an exception that wasn't handled properly.
            _log.debug('Raising unhandled exception: %r', self._unhandled_exception)
            raise self._unhandled_exception

        if self._jobrunner.exceptions:
            # One or more jobs raised an exception via JobBase.exception().
            _log.debug('Raising first job exception: %r', self._jobrunner.exceptions)
            raise self._jobrunner.exceptions[0]

    def _get_exit_code(self):
        for job in self._jobrunner.all_jobs:
            _log.debug('Exit code of %r: %r', job.name, job.exit_code)

        # First non-zero exit_code is the application exit_code
        for job in self._jobrunner.all_jobs:
            if job.exit_code not in (0, None):
                _log.debug('Exiting with exit code from %s: %r', job.name, job.exit_code)
                return job.exit_code

        return 0
