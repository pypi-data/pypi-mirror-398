"""
Concrete :class:`~.TrackerJobsBase` subclass for RFX
"""

import functools
import io
import re

from ... import jobs, utils
from ..base import TrackerJobsBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class RfxTrackerJobs(TrackerJobsBase):

    # Only generate mediainfo/bdinfo reports and screenshots for the first/main video file/playlist.
    document_all_videos = False

    release_name_english_title_before_original = False

    image_host_config = {
        'common': {'thumb_width': 350},
    }

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
            self.type_job,
            self.resolution_job,

            # Background jobs
            self.create_torrent_job,
            self.mediainfo_job,
            self.bdinfo_job,
            self.nfo_job,
            self.screenshots_job,
            self.upload_screenshots_job,
            self.description_job,
        )

    @functools.cached_property
    def isolated_jobs(self):
        """
        Sequence of job attribute names (e.g. "description_job") that were
        singled out by the user, e.g. with --only-description
        """
        if self.options.get('only_description', False):
            return self.get_job_and_dependencies(self.description_job)
        elif self.options.get('only_title', False):
            return self.get_job_and_dependencies(
                self.release_name_job,
                # `release_name_job` doesn't depend on `imdb_job` (or any other webdb), but we want
                # the correct name, year, etc in the release name.
                self.imdb_job,
            )

        # Activate all jobs in jobs_before/after_upload
        return ()

    @functools.cached_property
    def type_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('type'),
            label='Type',
            precondition=self.make_precondition('type_job'),
            prejobs=(
                self.release_name_job,
            ),
            autodetect=self.autodetect_type,
            autofinish=True,
            options=(
                ('Full Disc', '43'),
                ('Remux', '40'),
                ('Encode', '41'),
                ('WEB-DL', '42'),
                ('WEBRip', '45'),
                ('HDTV', '35'),
            ),
            focused='Encode',
            **self.common_job_args(),
        )

    _autodetect_type_map = {
        'Remux': lambda release: bool(re.search(r'(?i:Remux)', release.source)),
        'Full Disc': lambda release: bool(re.search(r'^(?i:DVD|BD)', release.source)),
        'Encode': lambda release: bool(re.search(r'^(?i:BluRay|HD-?DVD)', release.source)),
        'WEB-DL': lambda release: bool(re.search(r'^(?i:WEB-DL)', release.source)),
        'WEBRip': lambda release: bool(re.search(r'^(?i:WEBRip)', release.source)),
        'HDTV': lambda release: bool(re.search(r'^(?i:HD-?TV)', release.source)),
    }

    async def autodetect_type(self, _):
        _log.debug('Autodetected type: source: %r', self.release_name.source)
        for label, is_match in self._autodetect_type_map.items():
            if is_match(self.release_name):
                return label

    @functools.cached_property
    def resolution_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('resolution'),
            label='Resolution',
            precondition=self.make_precondition('resolution_job'),
            autodetect=self.autodetect_resolution,
            autofinish=True,
            options=(
                *self._resolution_map.items(),
                ('Other', '10'),
            ),
            focused='Other',
            **self.common_job_args(),
        )

    _resolution_map = {
        '4320p': '1',
        '2160p': '2',
        '1080p': '3',
        '1080i': '4',
        '720p': '5',
        '576p': '6',
        '576i': '7',
        '540p': '11',
        '480p': '8',
        '480i': '9',
    }

    async def autodetect_resolution(self, _):
        resolution = utils.mediainfo.video.get_resolution(self.content_path)
        _log.debug('Autodetected resolution: %s', resolution)
        if resolution in self._resolution_map:
            return resolution

    @functools.cached_property
    def description_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('description'),
            label='Description',
            precondition=self.make_precondition('description_job'),
            prejobs=(
                self.screenshots_job,
                self.upload_screenshots_job,
            ),
            text=self.generate_description,
            hidden=True,
            finish_on_success=True,
            read_only=True,
            **self.common_job_args(ignore_cache=True),
        )

    def generate_description(self):
        screenshots = self.generate_description_screenshots()
        parts = [
            (
                f'[center]{screenshots}[/center]'
                if screenshots else
                ''
            ),
        ]

        if promo := self.generate_promotion_bbcode(format='[right][size=1]{message}[/size][/right]'):
            parts.append(promo)

        return '\n\n'.join(part for part in parts if part)

    def generate_description_screenshots(self):
        assert self.upload_screenshots_job.is_finished
        return utils.bbcode.screenshots_grid(
            screenshots=self.upload_screenshots_job.uploaded_images,
            columns=(2, 3),
            horizontal_spacer=' ',
            vertical_spacer='\n',
        )

    @property
    def post_data(self):
        return {
            'name': self.get_job_output(self.release_name_job, slice=0),
            'description': self.get_job_output(self.description_job, slice=0),
            'mediainfo': self.post_data_mediainfo,
            'bdinfo': self.post_data_bdinfo,
            'category_id': '1',
            'type_id': self.get_job_attribute(self.type_job, 'choice'),
            'resolution_id': self.get_job_attribute(self.resolution_job, 'choice'),
            'tmdb': self.post_data_tmdb_id,
            'imdb': self.post_data_imdb_id,
            'anonymous': '1' if self.options['anonymous'] else '0',
            'personal_release': '1' if self.options['personal_release'] else '0',
        }

    @functools.cached_property
    def post_data_tmdb_id(self):
        return self.get_job_output(self.tmdb_job, slice=0).split('/')[1]

    @functools.cached_property
    def post_data_imdb_id(self):
        return self.get_job_output(self.imdb_job, slice=0)

    @functools.cached_property
    def post_data_mediainfo(self):
        if not self.is_bdmv_release:
            return self.get_job_output(self.mediainfo_job, slice=0)

    @functools.cached_property
    def post_data_bdinfo(self):
        if self.is_bdmv_release:
            return self.get_job_attribute(self.bdinfo_job, 'quick_summaries')[0]

    @functools.cached_property
    def post_files(self):
        files = {
            'torrent': {
                'file': self.torrent_filepath,
                'mimetype': 'application/octet-stream',
            },
        }

        if nfo := self.read_nfo(strip=True):
            files['nfo'] = {
                'file': io.BytesIO(nfo.encode('utf-8')),
                'mimetype': 'text/plain',
            }

        return files
