"""
Share generated metadata
"""

from .. import errors, trackers
from . import JobBase, JobRunner

import logging  # isort:skip
_log = logging.getLogger(__name__)


class SubmitJob(JobBase):
    """
    Submit torrent file and other metadata to tracker

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``submitting``
            Emitted when attempting to upload metadata. Registered callbacks get no arguments.

        ``submitted``
            Emitted when upload attempt ended. Registered callbacks get the torrent page URL of the
            submitted torrent as a positional argument or a :class:`~.RequestError` if the upload
            failed.
    """

    name = 'submit'
    label = 'Submit'

    # Don't cache output.
    cache_id = None

    def initialize(self, *, tracker_jobs):
        """
        Set internal state

        :param TrackerBase tracker: Return value of :func:`~.trackers.tracker`
        :param TrackerJobsBase tracker_jobs: Instance of :attr:`~.TrackerBase.TrackerJobs`
        """
        assert isinstance(tracker_jobs, trackers.TrackerJobsBase), f'Not a TrackerJobsBase: {tracker_jobs!r}'
        self._tracker_jobs = tracker_jobs
        self._tracker = tracker_jobs.tracker

        # Custom signals.
        self.signal.add('submitting')
        self.signal.add('submitted')

        # Pass through signals from TrackerBase subclass.
        self._tracker.signal.register('warning', self.warn)
        self._tracker.signal.register('error', self.error)
        self._tracker.signal.register('exception', self.exception)

    async def run(self):
        # Collect all the required metadata.
        await self._wait_for_jobs_before_upload()

        # Don't submit if self._tracker_jobs thinks that's a bad idea, e.g. if we only want the
        # release description.
        if self._tracker_jobs.submission_ok:
            await self._submit()

        await self._start_jobs_after_upload()

    async def _submit(self):
        _log.debug('Submitting')
        try:
            self.signal.emit('submitting')
            torrent_page_url = await self._tracker.upload(self._tracker_jobs)
            _log.debug('Torrent page url: %r', torrent_page_url)
            if torrent_page_url:
                self.add_output(torrent_page_url)
            self.signal.emit('submitted', torrent_page_url)
        except errors.RequestError as e:
            self.error(e)
        finally:
            _log.debug('Done submitting')

    async def _wait_for_jobs_before_upload(self):
        runner = JobRunner(self._tracker_jobs.jobs_before_upload, id='submit')
        await runner.wait()

    async def _start_jobs_after_upload(self):
        for job in self._tracker_jobs.jobs_after_upload:
            if job is not None:
                _log.debug('Starting job after upload: %r', job)
                job.start()

    @property
    def _enabled_jobs_before_upload(self):
        """
        Sequence of jobs to do before submission

        This is the same as :attr:`.TrackerJobsBase.jobs_before_upload` but with all `None` values
        and disabled jobs filtered out.
        """
        return tuple(
            job
            for job in self._tracker_jobs.jobs_before_upload
            if job and job.is_enabled
        )

    @property
    def hidden(self):
        """
        Hide this job if :attr:`~.TrackerJobsBase.submission_ok` is falsy

        If :attr:`~.TrackerJobsBase.submission_ok` is falsy, that usually means we are only
        generating some metadata that is not supposed to be submitted.

        It also should mean this job is not displayed until all
        :attr:`~.TrackerJobsBase.jobs_before_upload` have finished successfully.
        """
        return not self._tracker_jobs.submission_ok

    @property
    def _main_job(self):
        # Return object that provides `output` and `exit_code`.
        #
        # If submission is prevented by `TrackerJobsBase.submission_ok`, this is the last job of
        # `TrackerJobsBase.jobs_before_upload` if all those jobs are finished.
        #
        # Otherwise, return a :class:`super` instance, meaning we are using the parent class
        # (`JobBase`) to get `output` and `exit_code`.
        if not self._tracker_jobs.submission_ok:
            enabled_jobs = self._enabled_jobs_before_upload
            # Because jobs can enable/disable each other, we can't know the main job until all jobs
            # are either finished or disabled.
            if enabled_jobs and all(job.is_finished for job in enabled_jobs):
                return enabled_jobs[-1]
        return super()

    @property
    def output(self):
        """Output from :attr:`_main_job`"""
        return self._main_job.output

    @property
    def exit_code(self):
        """
        Exit code from last enabled job in :attr:`~.TrackerJobsBase.jobs_before_upload` if not
        :attr:`~.TrackerJobsBase.submission_ok`

        :attr:`.JobBase.exit_code` otherwise.
        """
        return self._main_job.exit_code
