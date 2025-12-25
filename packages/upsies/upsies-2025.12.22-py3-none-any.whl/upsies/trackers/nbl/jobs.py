"""
Concrete :class:`~.TrackerJobsBase` subclass for NBL
"""

import functools

from ... import jobs, utils
from .. import base

import logging  # isort:skip
_log = logging.getLogger(__name__)


class NblTrackerJobs(base.TrackerJobsBase):
    @functools.cached_property
    def jobs_before_upload(self):
        return (
            # Interactive jobs
            self.tvmaze_job,
            self.category_job,

            # Background jobs
            self.create_torrent_job,
            self.mediainfo_job,
            self.rules_job,
        )

    @functools.cached_property
    def category_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('category'),
            label='Category',
            precondition=self.make_precondition('category_job'),
            options=(
                ('Season', '3'),
                ('Episode', '1'),
            ),
            autodetected=self.autodetected_category,
            **self.common_job_args(),
        )

    @functools.cached_property
    def autodetected_category(self):
        if self.release_name.type is utils.release.ReleaseType.season:
            return 'Season'
        else:
            # Sometimes a series is continued or finalized as one or more
            # movies. We submit them as episodes.
            # TODO: Once the API supports it, we should add the special tag.
            # Example: https://www.tvmaze.com/shows/3646/alien-nation/episodes
            return 'Episode'

    @property
    def post_data(self):
        return {
            'api_key': self.options['apikey'],
            'category': self.get_job_attribute(self.category_job, 'choice'),
            'tvmazeid': self.get_job_output(self.tvmaze_job, slice=0),
            'mediainfo': self.get_job_output(self.mediainfo_job, slice=0),
            'anonymous': '1' if self.options.get('anonymous', False) else None,
        }
