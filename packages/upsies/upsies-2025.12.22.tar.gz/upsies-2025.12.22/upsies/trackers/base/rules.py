"""
Classes for checking if a release violates the tracker's rules
"""

import abc

from ... import errors, utils

import logging  # isort:skip
_log = logging.getLogger(__name__)


class TrackerRuleBase(abc.ABC):
    """
    Abstract base class that checks a release against one rule

    :param tracker_jobs: Instance of a :class:`~.TrackerJobsBase` subclass
    """

    required_jobs = ()
    """
    Sequence of :class:`~.TrackerJobsBase` attribute names that resolve to :class:`~.JobBase`
    instances

    All required jobs must finish before :meth:`check` is called.
    """

    def __init__(self, tracker_jobs):
        self._tracker_jobs = tracker_jobs

    @property
    def tracker_jobs(self):
        """:class:`~.TrackerJobsBase` instance"""
        return self._tracker_jobs

    @property
    def release_name(self):
        """:class:`~.ReleaseName` instance"""
        return self._tracker_jobs.release_name

    @property
    def tracker(self):
        """:class:`~.TrackerBase` instance"""
        return self._tracker_jobs.tracker

    async def _wait_for_required_jobs(self):
        """Block until all :attr:`~.required_jobs` are finished"""
        jobs = tuple(
            getattr(self.tracker_jobs, job_name)
            for job_name in self.required_jobs
        )
        _log.debug('Rule %s: Waiting for required jobs: %s', type(self).__name__, tuple(j.name for j in jobs))
        for job in jobs:
            await job.wait_finished()
        _log.debug('Rule %s: Done waiting for required jobs: %s', type(self).__name__, tuple(j.name for j in jobs))

    async def check(self):
        """
        Wait for :attr:`required_jobs` and check if rule is broken

        The actual checking is done in :meth:`_check`, which must be implemented by the subclass and
        raise :class:`~.RuleBroken` if the rule is broken.
        """
        await self._wait_for_required_jobs()
        await self._check()

    @abc.abstractmethod
    async def _check(self):
        """Check if rule is broken"""


class BannedGroup(TrackerRuleBase):
    """Check if release group is not allowed"""

    banned_groups = set()
    """
    :class:`set` of banned group names

    Groups specified here are always banned. To ban groups conditionally (e.g. ban only encodes from
    a certain group), override :meth:`_check_custom`.
    """

    def is_group(self, group_name):
        """
        Return whether `group_name` is equal to the :attr:`~.ReleaseName.group` of
        :attr:`~.TrackerRuleBase.release_name`
        """
        return self.release_name.group.lower() == group_name.lower()

    async def _check(self):
        await self._check_custom()

        # Case-insensitively match group name against `banned_groups`.
        for banned_group in self.banned_groups:
            if self.is_group(banned_group):
                raise errors.BannedGroup(banned_group)

    async def _check_custom(self):
        """
        Called by :meth:`check` before simple group name matching is done

        This method should be implemented by subclasses to ban certain groups only in some cases.

        :raise RuleBroken: if the group is banned
        """


class HdOnly(TrackerRuleBase):
    """Check if release is HD"""

    allow_sd_disc = False
    """Whether SD Blu-rays and DVDs are allowed"""

    allow_sd_remux = False
    """Whether SD remuxes are allowed"""

    allow_sd_webdl = False
    """Whether SD WEB-DLs are allowed"""

    @property
    def message(self):
        """Error message if release is not HD"""
        parts = ['Not an HD release']
        if self.allow_sd_disc:
            parts.append('or disc')
        if self.allow_sd_remux:
            parts.append('or remux')
        if self.allow_sd_webdl:
            parts.append('or WEB-DL')
        return ' '.join(parts)

    async def _check(self):
        is_hd = utils.mediainfo.video.get_resolution_int(self.release_name.path) >= 720
        is_disc = utils.disc.is_disc(self.release_name.path)
        is_remux = 'remux' in self.release_name.source.lower()
        is_webdl = 'web-dl' in self.release_name.source.lower()
        if (
                not is_hd
                and not (is_disc and self.allow_sd_disc)
                and not (is_remux and self.allow_sd_remux)
                and not (is_webdl and self.allow_sd_webdl)
        ):
            raise errors.RuleBroken(self.message)


class FhdOnly(TrackerRuleBase):
    """Check if release is Full HD"""

    message = 'Not a Full HD release'
    """Error message if release is not Full HD"""

    async def _check(self):
        if utils.mediainfo.video.get_resolution_int(self.release_name.path) < 1080:
            raise errors.RuleBroken(self.message)
