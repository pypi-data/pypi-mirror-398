"""
Concrete :class:`~.TrackerJobsBase` subclass for CBR
"""

import functools
import io
import re

from ... import jobs, utils
from ..base import TrackerJobsBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class CbrTrackerJobs(TrackerJobsBase):

    # Only generate mediainfo/bdinfo reports and screenshots for the first/main video file/playlist.
    document_all_videos = False

    release_name_english_title_before_original = False

    image_host_config = {
        'common': {'thumb_width': 400},
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
            self.category_job,
            self.season_job,
            self.episode_job,
            self.type_job,
            self.quality_job,

            # Background jobs
            self.create_torrent_job,
            self.mediainfo_job,
            self.bdinfo_job,
            self.nfo_job,
            self.screenshots_job,
            self.upload_screenshots_job,
            self.description_job,
            self.rules_job,
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
                # `release_name_job` doesn't depend on `imdb_job` (or any other
                # webdb), but we want the correct name, year, etc in the release
                # name.
                self.imdb_job,
                self.tmdb_job,
            )

        # Activate all jobs in jobs_before/after_upload
        return ()

    @functools.cached_property
    def season_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('season'),
            label='Season',
            precondition=self.make_precondition('season_job'),
            prejobs=(
                self.release_name_job,
                self.category_job,
            ),
            hidden=self.season_job_is_hidden,
            text=self.autodetect_season,
            normalizer=self.normalize_season,
            validator=self.validate_season,
            finish_on_success=True,
            **self.common_job_args(),
        )

    def season_job_is_hidden(self):
        return self.release_name.type not in (
            utils.release.ReleaseType.season,
            utils.release.ReleaseType.episode,
        )

    async def autodetect_season(self):
        if self.season_job_is_hidden():
            return ''

        _log.debug('Autodetected season: type: %r', self.release_name.type)
        if self.release_name.only_season:
            _log.debug('Autodetected season: only_season: %r', self.release_name.only_season)
            return self.release_name.only_season

        return None

    def normalize_season(self, text):
        return text.strip()

    def validate_season(self, text):
        if text:
            try:
                season = int(text)
            except ValueError as e:
                raise ValueError('Season must be a number.') from e
            else:
                # NOTE: Season 0 is ok for pilots, specials, etc.
                if not 0 <= season <= 100:
                    raise ValueError('Season is not reasonable.')

    @functools.cached_property
    def episode_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('episode'),
            label='Episode',
            precondition=self.make_precondition('episode_job'),
            prejobs=(
                self.release_name_job,
                self.category_job,
            ),
            hidden=self.episode_job_is_hidden,
            text=self.autodetect_episode,
            normalizer=self.normalize_episode,
            validator=self.validate_episode,
            finish_on_success=True,
            **self.common_job_args(),
        )

    def episode_job_is_hidden(self):
        return self.release_name.type is not utils.release.ReleaseType.episode

    async def autodetect_episode(self):
        # Use episode 0 for season pack (required).
        if self.release_name.type is utils.release.ReleaseType.season:
            return '0'
        elif self.release_name.type is not utils.release.ReleaseType.episode:
            return ''

        # If episodes as flat list contains only one episode (e.g. "S03E04"), we have our
        # episode. If there are multiple episodes (e.g. "S03E00E01"), we don't do any autodetection
        # and the user must enter the episode.
        all_episode_numbers = tuple(
            episode_number
            for episode_numbers in self.release_name.episodes_dict.values()
            for episode_number in episode_numbers
        )
        if len(all_episode_numbers) == 1:
            _log.debug('Autodetected episode: %r', all_episode_numbers[0])
            return all_episode_numbers[0]

    def normalize_episode(self, text):
        return text.strip()

    def validate_episode(self, text):
        if text:
            try:
                episode = int(text)
            except ValueError as e:
                raise ValueError('Episode must be a number.') from e
            else:
                # NOTE: Episode 0 is ok for pilots, specials, etc.
                if not episode >= 0:
                    raise ValueError('Episode is not reasonable.')

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
            autofinish=self.release_name.type is utils.release.ReleaseType.movie,
            options=(
                ('Filmes', '1'),
                ('Series', '2'),
                ('Animes', '4'),
                # ('Esportes', '8'),
                # ('Jogos', '5'),
                # ('Programas', '9'),
                # ('HQs/Mangas', '10'),
                # ('Livros', '11'),
                # ('Cursos', '12'),
                # ('Revistas', '13'),
            ),
            **self.common_job_args(),
        )

    _autodetect_category_map = {
        'Filmes': lambda release: release.type is utils.release.ReleaseType.movie,
        'Animes': lambda release: release.type in (
            utils.release.ReleaseType.season,
            utils.release.ReleaseType.episode,
        ) and release.service in (
            'CR',
            'HIDI',
            'Bili',
            'AO',  # anime onegai
            'B-Global', 'B Global',
        ),
        'Series': lambda release: release.type in (
            utils.release.ReleaseType.season,
            utils.release.ReleaseType.episode,
        ),
    }

    def autodetect_category(self, _):
        _log.debug('Autodetected category: type: %r', self.release_name.type)
        _log.debug('Autodetected category: service: %r', self.release_name.service)
        for label, is_match in self._autodetect_category_map.items():
            if is_match(self.release_name):
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
                ('Full Disc', '1'),
                ('Remux', '2'),
                ('Encode', '3'),
                ('WEB-DL', '4'),
                ('WEBRip', '5'),
                ('HDTV', '6'),
            ),
            focused='WEB-DL',
            **self.common_job_args(),
        )

    _autodetect_type_map = {
        'Full Disc': lambda release: release.source in (
            'DVD5', 'DVD9', 'Blu-ray',
        ),
        'Remux': lambda release: 'REMUX' in release.source,
        'Encode': lambda release: release.source in (
            'HD-DVD', 'BluRay',
        ),
        'WEB-DL': lambda release: 'WEB-DL' in release.source,
        'WEBRip': lambda release: 'WEBRip' in release.source,
        'HDTV': lambda release: 'HDTV' in release.source,
    }

    async def autodetect_type(self, _):
        _log.debug('Autodetected type: source: %r', self.release_name.source)
        for label, is_match in self._autodetect_type_map.items():
            if is_match(self.release_name):
                return label

    @functools.cached_property
    def quality_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('quality'),
            label='Quality',
            precondition=self.make_precondition('quality_job'),
            autodetect=self.autodetect_quality,
            autofinish=True,
            options=(
                *self._quality_map.items(),
                ('Other', '10'),
            ),
            focused='Other',
            **self.common_job_args(),
        )

    _quality_map = {
        '4320p': '1',
        '2160p': '2',
        '1080p': '3',
        '1080i': '4',
        '720p': '5',
        '576p': '6',
        '576i': '7',
        '480p': '8',
        '480i': '9',
    }

    async def autodetect_quality(self, _):
        resolution = utils.mediainfo.video.get_resolution(self.content_path)
        _log.debug('Autodetected quality: %s', resolution)
        if resolution in self._quality_map:
            return resolution

    def translate_video_format(video_format, release_name):
        """
        AVC/HEVC for REMUX/BDMV
        Add DUAL (audio) to the very end (not for BDMV)
        eg: H.264 DUAL-NoGrp
        """
        video_codec = video_format
        if re.search(r'(?:REMUX|Blu\-ray)', release_name.source, flags=re.IGNORECASE):
            if re.search(r'^(?:x|H\.?)264$', video_format, flags=re.IGNORECASE):
                video_codec = 'AVC'
            elif re.search(r'^(?:x|H\.?)265$', video_format, flags=re.IGNORECASE):
                video_codec = 'HEVC'

        if release_name.source != 'Blu-ray' and release_name.has_dual_audio:
            # only tag DUAL if it has Portuguese
            audio_languages = utils.mediainfo.audio.get_audio_languages(
                release_name.path,
                exclude_commentary=True,
            )
            if any(language == 'pt' for language in audio_languages):
                return f'{video_codec} DUAL'

        return video_codec

    def translate_audio_format(audio_format, release_name):
        """
        Remove space between channels for: DD, DDP, AAC
        Move Atmos after channels
        eg: AAC2.0 / DDP5.1 / DDP5.1 Atmos / TrueHD 5.1 Atmos
        """
        channels = utils.mediainfo.audio.get_audio_channels(release_name.path)
        match = re.search(r'(DDP?|AAC|TrueHD)(?: (Atmos))?', audio_format, flags=re.IGNORECASE)

        if match:
            # TrueHD has space (for some reason)
            if match.group(1) == 'TrueHD':
                audio_codec = ' '.join((match.group(1), channels))
            else:
                audio_codec = ''.join((match.group(1), channels))

            return ' '.join((audio_codec, match.group(2) or '')).rstrip()

        # just append channel for the rest, no changes
        return ' '.join((audio_format, channels))

    def translate_audio_channels(audio_channels, release_name):
        # Channel is included by translate_audio_format().
        return ''

    release_name_translation = {
        'source': {
            re.compile(r'(?i:remux)'): 'REMUX',
            re.compile(r'(?i:hybrid)'): 'Hybrid',
            re.compile(r'(?i:bd(?:25|50|66|100))'): 'Blu-ray',
            # Remove UHD if not REMUX/BDMV
            re.compile(r'(?i:uhd (?!.*(Blu-ray|remux)))'): '',
        },
        'video_format': translate_video_format,
        'hdr_format': {
            # HDR10 -> HDR / HDR10+ -> HDR10+
            re.compile(r'(?i:HDR10)(?!\+)'): 'HDR',
        },
        'edition': {
            # DUAL is moved to translate_video_format
            re.compile(r'(?i:dual audio)'): '',
        },
        'group': {
            re.compile(r'^NOGROUP$'): 'NoGroup',
        },
        'audio_format': translate_audio_format,
        'audio_channels': translate_audio_channels,
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

        thumb_width = self.image_host_config['common']['thumb_width']
        return ' '.join(
            f'[url={screenshot}][img={thumb_width}]{screenshot}[/img][/url]'
            for screenshot in self.upload_screenshots_job.uploaded_images
        )

    @property
    def post_data(self):
        return {
            'api_token': self.options['apikey'],
            'name': self.get_job_output(self.release_name_job, slice=0),
            'category_id': self.get_job_attribute(self.category_job, 'choice'),
            'type_id': self.get_job_attribute(self.type_job, 'choice'),
            'resolution_id': self.get_job_attribute(self.quality_job, 'choice'),
            'season_number': self.get_job_output(self.season_job, slice=0),
            'episode_number': self.get_job_output(self.episode_job, slice=0),
            'sd': self.post_data_sd,
            'tmdb': self.post_data_tmdb_id,
            'imdb': self.post_data_imdb_id,
            'description': self.get_job_output(self.description_job, slice=0),
            'mediainfo': self.post_data_mediainfo,
            'bdinfo': self.post_data_bdinfo,
            'anonymous': '1' if self.options['anonymous'] else '0',
            'personal_release': '1' if self.options['personal_rip'] else '0',
            'mod_queue_opt_in': '1' if self.options['queue'] else '0',
            # next fields are required
            'tvdb': '0',
            'mal': '0',
            'igdb': '0',
            'stream': '0',  # stream optimized
        }

    @functools.cached_property
    def post_data_sd(self):
        # The SD flag. (0 = Not Standard Definition, 1 = Standard Definition).
        # Default is 0
        try:
            height = int(self.release_name.resolution[:-1])
        except ValueError:
            return '0'
        else:
            return '1' if height < 720 else '0'

    @functools.cached_property
    def post_data_tmdb_id(self):
        # TMDb ID may be 0 for non-existing shows
        if self.tmdb_job.output:
            return self.get_job_output(self.tmdb_job, slice=0).split('/')[1]

        return '0'

    @functools.cached_property
    def post_data_imdb_id(self):
        # numbers only
        if self.imdb_job.output:
            imdb_id = self.get_job_output(self.imdb_job, slice=0)
            match = re.search(r'^(?:tt|)(\d+)$', imdb_id)
            if match:
                return match.group(1)

        return '0'

    @functools.cached_property
    def post_data_nfo(self):
        if nfo := self.read_nfo(strip=True):
            return io.BytesIO(bytes(nfo, 'utf-8'))

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
                'mimetype': 'application/x-bittorrent',
            }
        }

        if self.post_data_nfo:
            files['nfo'] = {
                'file': self.post_data_nfo,
                'filename': 'nfo',
                'mimetype': 'text/plain',
            }

        return files
