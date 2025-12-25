"""
Manage a bunch of jobs
"""

import collections

import logging  # isort:skip
_log = logging.getLogger(__name__)


class JobRunner(collections.abc.Mapping):
    """
    Wrapper around a bunch of :class:`~.JobBase` subclasses to manage them collectively

    This class subclasses :class:`~.collections.abc.Mapping` for easy access to jobs. Keys are job
    :attr:`~.JobBase.name`\\ s and values are the :class:`~.JobBase` instances.

    :param jobs: :class:`collections.abc.Iterable` of :class:`~.JobBase` subclasses
    :param str id: Any identifier (only used for debugging)
    """

    def __init__(self, jobs=(), id='anonymous'):
        self._id = str(id)
        self._jobs = {}
        self.add(*jobs)

    def __getitem__(self, job_name):
        return self._jobs[job_name]

    def __iter__(self):
        return iter(self._jobs)

    def __len__(self):
        return len(self._jobs)

    def add(self, *jobs):
        """
        Add `jobs`

        Every job must have a unique :class:`~.JobBase.name`.

        :param jobs: :class:`~.JobBase` subclasses
        """
        for job in jobs:
            if job.name in self._jobs:
                if job is not self._jobs[job.name]:
                    raise RuntimeError(f'Conflicting job name: {job.name!r}')
            else:
                _log.debug('%s: Adding job: %r', self._id, job)
                self._jobs[job.name] = job

    @property
    def all_jobs(self):
        """All :meth:`add`\\ ed jobs as a flat sequence"""
        return tuple(self._jobs.values())

    @property
    def enabled_jobs(self):
        """Same as :attr:`all_jobs`, but without any jobs that are not :attr:`~.JobBase.is_enabled`"""
        return tuple(job for job in self._jobs.values() if job.is_enabled)

    def start_more_jobs(self):
        """
        :meth:`~.JobBase.start` all jobs that are ready to start

        Jobs that have :attr:`~.JobBase.autostart` unset are not started.

        Jobs may also not be started if they are :attr:`disabled
        <upsies.jobs.base.JobBase.is_enabled>` or otherwise unstartable. See
        :meth:`~.JobBase.start`.

        .. note:: This method must be called while an asyncio event loop is running because
            JobBase.start() calls JobBase.add_task(), and a task must be added to a loop to run.
        """
        for job in self.all_jobs:
            if job.autostart:
                job.start()

    async def wait(self):
        """
        Wait for all jobs that are started and not finished

        .. note:: This does not raise exceptions from jobs. See :attr:`exceptions` after calling
            this method.
        """
        def get_running_jobs():
            return tuple(
                job
                for job in self.all_jobs
                if job.is_started and not job.is_finished
            )

        while running_jobs := get_running_jobs():
            _log.debug('%s: Waiting for running jobs:', self._id)
            for job in running_jobs:
                _log.debug('%s:    * %r', self._id, job)
            for job in running_jobs:
                await job.wait_finished()
                _log.debug('%s: Job finished: %r', self._id, job)
        _log.debug('%s: All running jobs finished', self._id)

    def terminate(self, reason=None):
        """Terminate :attr:`all_jobs`"""
        _log.debug('%s: Terminating all jobs', self._id)
        for job in self.all_jobs:
            job.terminate(reason=reason)

    @property
    def all_jobs_finished(self):
        """Whether all :attr:`enabled_jobs` are finished"""
        return all(job.is_finished for job in self.enabled_jobs)

    @property
    def exceptions(self):
        """Sequence of :class:`Exception` instances :attr:`~.JobBase.raised` by any job"""
        return tuple(
            job.raised
            for job in self.all_jobs
            if job.raised
        )
