"""
Concrete :class:`~.TrackerJobsBase` subclass for FLD
"""

import functools
import re

from ... import jobs, utils
from ..base import TrackerJobsBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class FldTrackerJobs(TrackerJobsBase):

    @functools.cached_property
    def jobs_before_upload(self):
        # NOTE: Keep in mind that the order of jobs is important for
        #       isolated_jobs: The final job is the overall result, so if
        #       upload_screenshots_job is listed after description_job,
        #       --only-description is going to print the list of uploaded
        #       screenshot URLs.
        return (
            # Interactive jobs
            self.playlists_job,
            self.tmdb_job,
            self.imdb_job,
            self.release_name_job,
            self.category_job,

            # Background jobs
            self.create_torrent_job,
            self.mediainfo_job,
            self.bdinfo_job,
            self.screenshots_job,
            self.upload_screenshots_job,
            self.description_job,
            self.rules_job,
        )

    @property
    def isolated_jobs(self):
        """
        Sequence of job attribute names (e.g. "imdb_job") that were singled
        out by the user, e.g. with a CLI argument
        """
        if self.options.get('only_description', False):
            return self.get_job_and_dependencies(self.description_job)
        else:
            # Activate all jobs in jobs_before/after_upload
            return ()

    @functools.cached_property
    def tmdb_job(self):
        tmdb_job = super().tmdb_job
        tmdb_job.no_id_ok = True
        return tmdb_job

    @functools.cached_property
    def category_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('category'),
            label='Category',
            precondition=self.make_precondition('category_job'),
            prejobs=(
                self.release_name_job,
            ),
            autodetect=self.autodetect_category,
            autofinish=True,
            options=(
                ('Movie', 'movie'),
                ('TV Season', 'show_season'),
                ('TV Episode', 'show_episode'),
            ),
            **self.common_job_args(),
        )

    _autodetect_category_map = {
        'Movie': lambda release_name: release_name.type is utils.release.ReleaseType.movie,
        'TV Season': lambda release_name: release_name.type is utils.release.ReleaseType.season,
        'TV Episode': lambda release_name: release_name.type is utils.release.ReleaseType.episode,
    }

    def autodetect_category(self, _):
        approved_release_name = self.release_name
        _log.debug('Autodetecting category: Approved release type: %r', approved_release_name.type)
        for label, is_match in self._autodetect_category_map.items():
            if is_match(approved_release_name):
                return label

    release_name_english_title_before_original = True
    release_name_translation = {
        'source': {
            re.compile(r'(?i:remux)'): 'REMUX',
            re.compile(r'(?i:hybrid)'): 'HYBRID',
        },
    }

    @functools.cached_property
    def description_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('description'),
            label='Description',
            precondition=self.make_precondition('description_job'),
            prejobs=(
                self.playlists_job,
                self.mediainfo_job,
                self.bdinfo_job,
                self.screenshots_job,
                self.upload_screenshots_job,
            ),
            text=self.generate_description,
            hidden=True,
            finish_on_success=True,
            read_only=True,
            **self.common_job_args(ignore_cache=True),
        )

    image_host_config = {
        'common': {'thumb_width': 350},
    }

    def generate_description(self):
        screenshots = self._generate_description_screenshots()
        mediainfos = self._generate_description_mediainfos()

        description_parts = [
            '[center]\n'
            + screenshots
            + '\n[/center]'
        ]

        if mediainfos:
            # Include mediainfos if there are multiple (e.g. for IFO/VOB or if `document_all_videos`
            # is True)
            description_parts.append(
                '\n[center][h3]Mediainfo[/h3][/center]\n'
                + mediainfos
            )

        if promo := self.generate_promotion_bbcode():
            description_parts.append(f'\n\n\n{promo}')

        return ''.join(description_parts)

    def _generate_description_screenshots(self):
        assert self.upload_screenshots_job.is_finished
        return utils.bbcode.screenshots_grid(
            screenshots=self.upload_screenshots_job.uploaded_images,
            columns=2,
            horizontal_spacer='   ',
            vertical_spacer='\n\n',
        )

    def _generate_description_mediainfos(self):
        mediainfo_tags = []
        for video_filepath, mediainfo in self._description_mediainfos.items():
            filetitle = self.get_relative_file_path(video_filepath)
            mediainfo_tags.append(
                f'[hide={filetitle}][code]{mediainfo}[/code][/hide]'
            )
        return '\n'.join(mediainfo_tags)

    # Only generate mediainfo/bdinfo reports and screenshots for the first/main video file/playlist.
    document_all_videos = False

    @property
    def _description_mediainfos(self):
        # mediainfo_job should be disabled for BDMV releases. In that case, the BDInfo report is
        # passed normally in place of the mediainfo report. (See mediainfo_filehandle.)
        if self.mediainfo_job.is_enabled:
            assert self.mediainfo_job.is_finished

            # For VIDEO_TS releases, there should be one mediainfo report for a .IFO and another for
            # a .VOB file. The .IFO report should always be passed separately, but we include them
            # both in the description for ease of access.
            mediainfos_by_file = self.mediainfo_job.reports_by_file
            if len(mediainfos_by_file) >= 2:
                return mediainfos_by_file

        return {}

    @property
    def post_data(self):
        return {
            'name': self.get_job_output(self.release_name_job, slice=0),
            'media_type': self.get_job_attribute(self.category_job, 'choice'),
            'media_info': self.get_job_output(self.mediainfo_job, slice=0),
            'imdb_id': self.get_job_output(self.imdb_job, slice=0),
            'tmdb_id': self.get_job_output(self.tmdb_job, slice=0),
            'description': self.get_job_output(self.description_job, slice=0),
            'anonymous': self.options['anonymous'],
        }
