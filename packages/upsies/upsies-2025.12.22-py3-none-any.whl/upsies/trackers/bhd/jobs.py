"""
Concrete :class:`~.TrackerJobsBase` subclass for BHD
"""

import functools
import io
import re

from ... import jobs, utils
from ..base import TrackerJobsBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class BhdTrackerJobs(TrackerJobsBase):

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
            self.type_job,
            self.source_job,
            self.scene_check_job,
            self.tags_job,

            # Background jobs
            self.create_torrent_job,
            self.mediainfo_job,
            self.bdinfo_job,
            self.screenshots_job,
            self.upload_screenshots_job,
            self.description_job,
            self.rules_job,
            self.nfo_job,
        )

    @property
    def isolated_jobs(self):
        """
        Sequence of job attribute names (e.g. "imdb_job") that were singled
        out by the user, e.g. with a CLI argument
        """
        if self.options.get('only_description', False):
            return self.get_job_and_dependencies(self.description_job)
        elif self.options.get('only_title', False):
            return self.get_job_and_dependencies(
                self.release_name_job,
                # `release_name_job` doesn't depend on `imdb_job` (or any other
                # webdb), but we want the correct name, year, etc in the release
                # name.
                self.imdb_job,
            )
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
                ('Movie', '1'),
                ('TV', '2'),
            ),
            **self.common_job_args(),
        )

    _autodetect_category_map = {
        'Movie': lambda release_name: release_name.type is utils.release.ReleaseType.movie,
        'TV': lambda release_name: release_name.type in (utils.release.ReleaseType.season,
                                                         utils.release.ReleaseType.episode)
    }

    def autodetect_category(self, _):
        approved_release_name = self.release_name
        _log.debug('Autodetecting category: Approved release type: %r', approved_release_name.type)
        for label, is_match in self._autodetect_category_map.items():
            if is_match(approved_release_name):
                return label

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
                ('UHD 100', 'UHD 100'),
                ('UHD 66', 'UHD 66'),
                ('UHD 50', 'UHD 50'),
                ('UHD Remux', 'UHD Remux'),
                ('BD 50', 'BD 50'),
                ('BD 25', 'BD 25'),
                ('BD Remux', 'BD Remux'),
                ('2160p', '2160p'),
                ('1080p', '1080p'),
                ('1080i', '1080i'),
                ('720p', '720p'),
                ('576p', '576p'),
                ('540p', '540p'),
                ('DVD 9', 'DVD 9'),
                ('DVD 5', 'DVD 5'),
                ('DVD Remux', 'DVD Remux'),
                ('480p', '480p'),
                ('Other', 'Other'),
            ),
            focused='Other',
            **self.common_job_args(),
        )

    _autodetect_type_map = {
        # Directory trees / Images
        'UHD 100': lambda release_name: (
            release_name.source == 'BD100'
            and release_name.resolution == '2160p'
        ),
        'UHD 66': lambda release_name: (
            release_name.source == 'BD66'
            and release_name.resolution == '2160p'
        ),
        'UHD 50': lambda release_name: (
            release_name.source == 'BD50'
            and release_name.resolution == '2160p'
        ),
        'BD 50': lambda release_name: release_name.source == 'BD50',
        'BD 25': lambda release_name: release_name.source == 'BD25',
        'DVD 9': lambda release_name: release_name.source == 'DVD9',
        'DVD 5': lambda release_name: release_name.source == 'DVD5',

        # Remuxes
        'DVD Remux': lambda release_name: release_name.source.lower() == 'dvd remux',
        'UHD Remux': lambda release_name: (
            'remux' in release_name.source.lower()
            and release_name.resolution == '2160p'
        ),
        'BD Remux': lambda release_name: (
            'remux' in release_name.source.lower()
            and release_name.resolution == '1080p'
        ),

        # Encodes
        '2160p': lambda release_name: release_name.resolution == '2160p',
        '1080p': lambda release_name: release_name.resolution == '1080p',
        '1080i': lambda release_name: release_name.resolution == '1080i',
        '720p': lambda release_name: release_name.resolution == '720p',
        '576p': lambda release_name: release_name.resolution == '576p',
        '540p': lambda release_name: release_name.resolution == '540p',
        '480p': lambda release_name: release_name.resolution == '480p',
    }

    async def autodetect_type(self, _):
        # Because "source" in `self.release_name` translates "BD25/50/..." to "Blu-ray", we must
        # make a new `ReleaseName` instance.
        rn = utils.release.ReleaseName(self.content_path)
        _log.debug('Autodetecting type: %r: resolution: %r, source: %r', self.content_path, rn.resolution, rn.source)
        for label, is_match in self._autodetect_type_map.items():
            if is_match(rn):
                return label

    _autodetect_sources_map = {
        'Blu-ray': re.compile(r'(?i:blu-?ray|bd(?:25|50|66|100))'),  # (UHD) BluRay|BD(25|50|66|100) (Remux)
        'HD-DVD': re.compile(r'(?i:hd-?dvd)'),  # HD(-)DVD
        'WEB': re.compile(r'^(?i:web)'),  # WEB(-DL|Rip)
        'HDTV': re.compile(r'(?:hd-?|)(?i:tv)'),  # HD(-)TV
        'DVD': re.compile(r'^(?i:dvd)'),  # DVD(5|9|...)
    }

    @functools.cached_property
    def source_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('source'),
            label='Source',
            precondition=self.make_precondition('source_job'),
            prejobs=(
                self.release_name_job,
            ),
            autodetect=self.autodetect_source,
            autofinish=True,
            options=tuple(self._autodetect_sources_map),
            **self.common_job_args(),
        )

    async def autodetect_source(self, _):
        approved_release_name = self.release_name
        _log.debug('Autodetecting source: Approved source: %r', approved_release_name.source)
        for label, regex in self._autodetect_sources_map.items():
            if regex.search(approved_release_name.source):
                return label

    release_name_english_title_before_original = True

    def _translate_video_format(video_format, release_name):
        rn = release_name

        # Translate (x|H(.))264 to AVC/HEVC, but only for remux and BDMV.
        # if re.search(r'(?i:REMUX|BD\d{2,})', rn.source, flags=re.IGNORECASE):
        if re.search(r'(?:REMUX|Blu-ray)', rn.source, flags=re.IGNORECASE):
            if re.search(r'^(?i:x|H\.?)264$', video_format, flags=re.IGNORECASE):
                return 'AVC'
            elif re.search(r'^(?i:x|H\.?)265$', video_format, flags=re.IGNORECASE):
                return 'HEVC'

    def _translate_group(group, release_name):
        if group == 'NOGROUP' and (
                release_name.source.endswith('Blu-ray')
                or release_name.source.endswith('DVD')
        ):
            return ''

    release_name_translation = {
        'source': {
            re.compile(r'(?i:remux)'): 'REMUX',
            re.compile(r'(?i:hybrid)'): 'HYBRID',
            re.compile(r'(?i:hddvd)'): 'HD-DVD',
            re.compile(r'(?i:bd\d+)'): 'Blu-ray',
            re.compile(r'(?i:dvd\d+)'): 'DVD',
        },
        'video_format': _translate_video_format,
        'group': _translate_group,
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
            vertical_spacer='\n\n\n',
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

    @functools.cached_property
    def tags_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('tags'),
            label='Tags',
            precondition=self.make_precondition('tags_job'),
            prejobs=(
                self.release_name_job,
                self.scene_check_job,
            ),
            text=self.generate_tags,
            finish_on_success=True,
            read_only=True,
            **self.common_job_args(),
        )

    async def generate_tags(self):
        assert self.release_name_job.is_finished
        assert self.scene_check_job.is_finished

        # Any additional tags separated by comma(s). (Commentary, 2in1, Hybrid,
        # OpenMatte, 2D3D, WEBRip, WEBDL, 3D, 4kRemaster, DualAudio, EnglishDub,
        # Personal, Scene, DigitalExtras, Extras)
        tags = []
        if 'WEBRip' in self.release_name.source:
            tags.append('WEBRip')
        elif 'WEB-DL' in self.release_name.source:
            tags.append('WEBDL')
        if 'Hybrid' in self.release_name.source:
            tags.append('Hybrid')
        if self.release_name.has_commentary:
            tags.append('Commentary')
        if self.release_name.has_dual_audio:
            tags.append('DualAudio')
        if 'Open Matte' in self.release_name.edition:
            tags.append('OpenMatte')
        if '2in1' in self.release_name.edition:
            tags.append('2in1')
        if '4k Remastered' in self.release_name.edition:
            tags.append('4kRemaster')
        if self.get_job_attribute(self.scene_check_job, 'is_scene_release'):
            tags.append('Scene')
        if self.options['personal_rip']:
            tags.append('Personal')

        # TODO: 2D3D
        # TODO: 3D
        # TODO: EnglishDub
        # TODO: DigitalExtras
        # TODO: Extras

        return '\n'.join(tags)

    @property
    def post_data(self):
        return {
            'name': self.get_job_output(self.release_name_job, slice=0),
            'category_id': self.get_job_attribute(self.category_job, 'choice'),
            'type': self.get_job_attribute(self.type_job, 'choice'),
            'source': self.get_job_attribute(self.source_job, 'choice'),
            'imdb_id': self.get_job_output(self.imdb_job, slice=0),
            'tmdb_id': self.post_data_tmdb_id,
            'description': self.get_job_output(self.description_job, slice=0),
            'edition': self.post_data_edition,
            'custom_edition': self.options['custom_edition'],
            'tags': ','.join(self.get_job_output(self.tags_job, slice=0).split('\n')),
            'nfo': self.nfo_text,
            'pack': self.post_data_pack,
            'sd': self.post_data_sd,
            'special': self.post_data_special,
            'anon': '1' if self.options['anonymous'] else '0',
            'live': '0' if self.options['draft'] else '1',
        }

    @functools.cached_property
    def post_data_tmdb_id(self):
        # TMDb ID may be 0 for non-existing shows
        if self.tmdb_job.output:
            return self.get_job_output(self.tmdb_job, slice=0).split('/')[1]
        else:
            return 0

    @functools.cached_property
    def post_data_edition(self):
        # The edition of the uploaded release. (Collector, Director, Extended,
        # Limited, Special, Theatrical, Uncut or Unrated)
        edition = self.release_name.edition
        _log.debug('Approved edition: %r', edition)
        if "Collector's Edition" in edition:
            return 'Collector'
        elif "Director's Cut" in edition:
            return 'Director'
        elif 'Extended Cut' in edition:
            return 'Extended'
        elif 'Limited' in edition:
            return 'Limited'
        elif 'Special Edition' in edition:
            return 'Special'
        elif 'Theatrical Cut' in edition:
            return 'Theatrical'
        elif 'Uncut' in edition or 'Uncensored' in edition:
            return 'Uncut'
        elif 'Unrated' in edition:
            return 'Unrated'

    @property
    def post_data_pack(self):
        # The TV pack flag for when the torrent contains a complete season.
        # (0 = No TV pack or 1 = TV Pack). Default is 0
        if self.release_name.type is utils.release.ReleaseType.season:
            return '1'
        else:
            return '0'

    @property
    def post_data_sd(self):
        # The SD flag. (0 = Not Standard Definition, 1 = Standard Definition).
        # Default is 0
        try:
            height = int(self.release_name.resolution[:-1])
        except ValueError:
            return '0'
        else:
            return '1' if height < 720 else '0'

    @property
    def post_data_special(self):
        # The TV special flag for when the torrent contains a TV special. (0 =
        # Not a TV special, 1 = TV Special). Default is 0
        if (
                self.release_name.type is utils.release.ReleaseType.episode
                and self.options['special']
        ):
            return '1'
        else:
            return '0'

    # TODO
    # @property
    # def post_data_region(self):
    #     # The region in which the disc was released. Only for discs! (AUS,
    #     # CAN, CEE, CHN, ESP, EUR, FRA, GBR, GER, HKG, ITA, JPN, KOR, NOR,
    #     # NLD, RUS, TWN or USA)

    @property
    def mediainfo_filehandle(self):
        if self.is_bdmv_release:
            info = self.get_job_attribute(self.bdinfo_job, 'quick_summaries')[0]
        else:
            info = self.get_job_output(self.mediainfo_job, slice=0)
        return io.BytesIO(bytes(info, 'utf-8'))

    def add_torrent_precondition(self):
        """Don't add the torrent to a client if it was submitted as a draft"""
        return not self.options['draft']
