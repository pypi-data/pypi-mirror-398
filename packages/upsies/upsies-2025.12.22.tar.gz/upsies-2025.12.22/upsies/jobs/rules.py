"""
Tracker rules
"""

import asyncio

from .. import errors
from . import JobBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class RulesJob(JobBase):
    """
    Check if a particulare release does not violate tracker rules

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``checking``
            Emitted when a rule is checked. Registered callbacks get the :class:`~.TrackerRuleBase`
            subclass as a positional argument.

        ``checked``
            Emitted when a rule was checked. Registered callbacks get the :class:`~.TrackerRuleBase`
            subclass and a :class:`~.RuleBroken` instance or `None` as positional arguments.
    """

    name = 'rules'
    label = 'Rules'

    # TODO: Can we cache this?
    cache_id = None

    @property
    def tracker(self):
        """Instance of a :class:`~.TrackerBase` subclass"""
        return self._tracker_jobs.tracker

    @property
    def tracker_jobs(self):
        """Instance of a :class:`~.TrackerJobsBase` subclass"""
        return self._tracker_jobs

    @property
    def release_name(self):
        """:class:`~.ReleaseName` instance"""
        return self._tracker_jobs.release_name

    # This job produces no output, only errors or warnings.
    no_output_is_ok = True

    # Errors and warnings are displayed even for hidden jobs.
    hidden = True

    def initialize(self, *, tracker_jobs, only_warn=False):
        """
        Set internal state

        :param tracker_jobs: Instance of a :class:`~.TrackerJobsBase` subclass

        :param bool only_warn: Exceptions from broken rules are passed to :meth:`~.JobBase.warn`
            instead of :meth:`~.JobBase.error` (i.e. allow submissions with broken rules)
        """
        self._tracker_jobs = tracker_jobs
        self._only_warn = only_warn
        self._rules_checked = {}
        self.signal.add('checking')
        self.signal.add('checked')

    async def run(self):
        await asyncio.gather(*(
            self.check_rule(TrackerRule)
            for TrackerRule in self.tracker.rules
        ))

    async def check_rule(self, TrackerRule):
        rule = TrackerRule(self.tracker_jobs)
        self.signal.emit('checking', rule)
        try:
            await rule.check()
        except errors.RuleBroken as e:
            _log.debug('%s: Rule broken: %r', TrackerRule.__name__, e)
            if self._only_warn:
                self.warn(e)
            else:
                self.error(e)
        else:
            _log.debug('%s: Rule obeyed', TrackerRule.__name__)
        self.signal.emit('checked', rule)
