"""
Concrete :class:`~.TrackerJobsBase` subclass for UHD
"""

import functools
import re
import urllib.parse
from datetime import datetime

import unidecode

from ... import errors, jobs, utils
from ..base import TrackerJobsBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class UhdTrackerJobs(TrackerJobsBase):

    @functools.cached_property
    def jobs_before_upload(self):
        # Don't start poster_job until we have an IMDb ID.
        self.poster_job.prejobs += (self.imdb_job,)

        return (
            self.login_job,

            # Interactive jobs
            self.imdb_job,
            self.type_job,
            self.season_job,
            self.year_job,
            self.quality_job,
            self.version_job,
            self.source_job,
            self.codec_job,
            self.hdr_format_job,
            self.tags_job,
            self.poster_job,
            self.trailer_job,
            self.automerge_group_job,
            self.scene_check_job,

            # Background jobs
            self.create_torrent_job,
            self.mediainfo_job,
            self.screenshots_job,
            self.upload_screenshots_job,
            self.description_job,
            self.rules_job,
        )

    @property
    def isolated_jobs(self):
        """
        Sequence of job attribute names (e.g. "description_job") that were
        singled out by the user, e.g. with --only-description
        """
        if self.options.get('only_description', False):
            return self.get_job_and_dependencies(self.description_job)
        else:
            # Activate all jobs in jobs_before/after_upload
            return ()

    @functools.cached_property
    def type_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('type'),
            label='Type',
            precondition=self.make_precondition('type_job'),
            autodetect=self.autodetect_type,
            autofinish=True,
            options=(
                ('Movie', '0'),
                # ("Music", '1'),  # Not supported
                ('TV', '2'),
            ),
            **self.common_job_args(),
        )

    async def autodetect_type(self, _):
        await self.imdb_job.wait_finished()
        if self.imdb_job.selected.get('type') is utils.release.ReleaseType.movie:
            return 'Movie'
        elif self.imdb_job.selected.get('type') in (
                utils.release.ReleaseType.season,
                utils.release.ReleaseType.episode,
        ):
            return 'TV'

    @property
    def user_confirmed_type(self):
        # Get type from type_job, which got its type from imdb_job, which is
        # guaranteed to be correct because we asked the user.
        if self.type_job.is_finished and self.type_job.output:
            text = self.type_job.output[0]
            return {
                'Movie': utils.release.ReleaseType.movie,
                'TV': utils.release.ReleaseType.season,
            }[text]

    @functools.cached_property
    def year_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('year'),
            label='Year',
            precondition=self.make_precondition('year_job'),
            prejobs=(
                self.imdb_job,
            ),
            text=self.autodetect_year,
            warn_exceptions=(
                errors.RequestError,
            ),
            normalizer=self.normalize_year,
            validator=self.validate_year,
            finish_on_success=True,
            **self.common_job_args(),
        )

    async def autodetect_year(self):
        assert self.imdb_job.is_finished

        json = await self._tracker.get_uhd_info(self.imdb_id)
        year = json.get('year', None)
        _log.debug('Autodetected UHD year: %r', year)
        if year:
            return year

        year = await self.imdb.year(self.imdb_id)
        if year:
            _log.debug('Autodetected IMDb year: %r', year)
            return year

    def normalize_year(self, text):
        return text.strip()

    def validate_year(self, text):
        if not text:
            raise ValueError('Year must not be empty.')
        try:
            year = int(text)
        except ValueError as e:
            raise ValueError('Year must be a number.') from e
        else:
            if not 1800 < year < datetime.now().year + 10:
                raise ValueError('Year is not reasonable.')

    @functools.cached_property
    def season_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('season'),
            label='Season',
            precondition=self.make_precondition('season_job'),
            prejobs=(
                self.imdb_job,
                self.type_job,
            ),
            hidden=self.season_job_is_hidden,
            text=self.autodetect_season,
            normalizer=self.normalize_season,
            validator=self.validate_season,
            finish_on_success=True,
            **self.common_job_args(),
        )

    def season_job_is_hidden(self):
        return self.user_confirmed_type not in (
            utils.release.ReleaseType.season,
            utils.release.ReleaseType.episode,
        )

    async def autodetect_season(self):
        if self.user_confirmed_type in (
                utils.release.ReleaseType.season,
                utils.release.ReleaseType.episode,
        ):
            _log.debug('Autodetected season: %r', self.release_name.only_season)
            if self.release_name.only_season:
                return self.release_name.only_season
            else:
                return None
        else:
            # Empty string for movies. This finishes the job successfully.
            return ''

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

    @property
    def season_number(self):
        output = self.get_job_output(self.season_job, slice=0, default=())
        if output:
            return int(output)

    @functools.cached_property
    def quality_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('quality'),
            label='Quality',
            precondition=self.make_precondition('quality_job'),
            autodetect=self.autodetect_quality,
            autofinish=True,
            options=(
                ('mHD', 'mHD'),
                ('720p', '720p'),
                ('1080p', '1080p'),
                ('1080i', '1080i'),
                ('2160p', '2160p'),
                ('Other', 'Others'),
            ),
            focused='Other',
            **self.common_job_args(),
        )

    async def autodetect_quality(self, _):
        resolution = utils.mediainfo.video.get_resolution(self.content_path)
        _log.debug('Autodetecting quality: %s', resolution)
        if resolution in ('2160p', '1080i', '1080p', '720p'):
            return resolution

    @functools.cached_property
    def version_job(self):
        return jobs.custom.CustomJob(
            name=self.get_job_name('version'),
            label='Version',
            precondition=self.make_precondition('version_job'),
            worker=self.autodetect_version,
            # Non-special releases produce no output, which is not an error.
            no_output_is_ok=True,
            **self.common_job_args(),
        )

    async def autodetect_version(self, _):
        versions = []

        for version, is_version in self.version_map.items():
            if not is_version:
                _log.debug('Unsupported autodetection for %r', version)
            elif is_version(self.release_name):
                _log.debug('Autodetected version: %r', version)
                versions.append(version)

        # HACK: VP9 is not officially supported, but we may upload it with an empty "codec" field
        #       and indicating VP9 as a "version": forums.php?action=viewthread&threadid=2081
        if self.release_name.video_format == 'VP9':
            versions.append('VP9')

        return tuple(versions)

    version_map = {
        "Director's Cut": lambda release: "Director's Cut" in release.edition,
        'Theatrical': lambda release: 'Theatrical Cut' in release.edition,
        'Extended': lambda release: 'Extended Cut' in release.edition,
        'IMAX': lambda release: 'IMAX' in release.edition,
        'Uncut': lambda release: 'Uncut' in release.edition,
        'TV Cut': None,  # Unsupported
        'Unrated': lambda release: 'Unrated' in release.edition,
        'Remastered': lambda release: 'Remastered' in release.edition,
        '4K Remaster': lambda release: '4k Remastered' in release.edition,
        '4K Restoration': lambda release: '4k Restored' in release.edition,
        'B&W Version': None,  # Unsupported
        'Criterion': lambda release: 'Criterion Collection' in release.edition,
        '2in1': lambda release: '2in1' in release.edition,
        '3in1': lambda release: '3in1' in release.edition,
        'Hybrid': lambda release: 'Hybrid' in release.source,
        '10-bit': lambda release: utils.mediainfo.video.get_bit_depth(release.path, default=None) == 10,
        'Extras': None,  # Unsupported
    }

    # On the website, this is called "Media".
    @functools.cached_property
    def source_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('source'),
            label='Source',
            precondition=self.make_precondition('source_job'),
            autodetect=self.autodetect_source,
            autofinish=True,
            options=(
                ('Blu-ray', 'Blu-ray'),
                ('Remux', 'Remux'),
                ('Encode', 'Encode'),
                ('WEB-DL', 'WEB-DL'),
                ('WEBRip', 'WEBRip'),
                ('HDRip', 'HDRip'),
                ('HDTV', 'HDTV'),
                ('Other', 'Others'),
            ),
            focused='Other',
            **self.common_job_args(),
        )

    async def autodetect_source(self, _):
        for source, is_source in self.source_map.items():
            if is_source(self.release_name):
                _log.debug('Autodetected source: %r', source)
                return source

    source_map = {
        'Remux': lambda release: 'Remux' in release.source,
        'Encode': lambda release: any(
            source in release.source
            for source in (
                'BluRay',
                'HD-DVD',
            )
        ),
        'WEB-DL': lambda release: 'WEB-DL' in release.source,
        'WEBRip': lambda release: 'WEBRip' in release.source,
        'HDTV': lambda release: 'HDTV' in release.source,
        # Not sure what "HDRip" is exactly and how to detect it.
        'HDRip': lambda release: 'Rip' in release.source,
    }

    @functools.cached_property
    def codec_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('codec'),
            label='Codec',
            precondition=self.make_precondition('codec_job'),
            autodetect=self.autodetect_codec,
            autofinish=True,
            options=(
                ('x264', 'x264'),
                ('x265', 'x265'),
                ('x266', 'x266'),
                ('H.264', 'H.264'),  # AVC aka H.264
                ('H.265', 'HEVC'),   # HEVC aka H.265
                ('AV1', 'AV1'),
                # HACK: VP9 is not officially supported, but we may upload it with an empty "codec" field
                #       and indicating VP9 as a "version": forums.php?action=viewthread&threadid=2081
                ('VP9', ''),
                ('VC-1', 'VC-1'),
                ('MPEG-2', 'MPEG-2'),
            ),
            **self.common_job_args(ignore_cache=True),
        )

    async def autodetect_codec(self, _):
        for codec, is_codec in self.codec_map.items():
            if is_codec(self.release_name):
                _log.debug('Autodetected video codec: %r', codec)
                return codec

    codec_map = {
        # TODO: Add support for commented-out codecs in utils.video and ReleaseName.
        'x264': lambda release: release.video_format == 'x264',
        'x265': lambda release: release.video_format == 'x265',
        # 'x266': lambda release: release.video_format == 'x266',
        'H.264': lambda release: release.video_format == 'H.264',
        'H.265': lambda release: release.video_format == 'H.265',
        # 'AV1': lambda release: release.video_format == 'AV1',
        'VP9': lambda release: release.video_format == 'VP9',
        # 'VC-1': lambda release: release.video_format == 'VC-1',
        # 'MPEG-2': lambda release: release.video_format == 'MPEG-2',
    }

    @functools.cached_property
    def hdr_format_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('hdr-format'),
            label='HDR',
            precondition=self.make_precondition('hdr_format_job'),
            autodetect=self.autodetect_hdr_format,
            autofinish=True,
            options=(
                ('No', 'No'),
                ('HDR10', 'HDR10'),
                ('HDR10+', 'HDR10+'),
                ('Dolby Vision', 'DoVi'),
            ),
            **self.common_job_args(),
        )

    async def autodetect_hdr_format(self, _):
        for hdr_format, is_hdr_format in self.hdr_format_map.items():
            if is_hdr_format(self.release_name):
                _log.debug('Autodetected HDR format from %r: %r', self.release_name.hdr_format, hdr_format)
                return hdr_format

    hdr_format_map = {
        'Dolby Vision': lambda release: 'DV' in release.hdr_format,
        'HDR10+': lambda release: 'HDR10+' in release.hdr_format,
        'HDR10': lambda release: 'HDR10' in release.hdr_format,
        'No': lambda release: release.hdr_format == '',
    }

    @functools.cached_property
    def tags_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('tags'),
            label='Tags',
            precondition=self.make_precondition('tags_job'),
            prejobs=(
                self.imdb_job,
            ),
            text=self.autodetect_tags,
            warn_exceptions=(
                errors.RequestError,
            ),
            finish_on_success=True,
            normalizer=self.normalize_tags,
            validator=self.validate_tags,
            **self.common_job_args(),
        )

    async def autodetect_tags(self):
        try:
            tags = await self._autodetect_tags_from_uhd()
        except errors.RequestError:
            tags = []
        _log.debug('Tags from UHD: %r', tags)

        # Get more tags from IMDb. UHD only returns genres and we can get people from IMDb.
        imdb_tags = await self._autodetect_tags_from_imdb()
        _log.debug('Tags from IMDb: %r', imdb_tags)
        tags.extend(str(tag) for tag in imdb_tags)

        _log.debug('Tags: %r', tags)
        return ', '.join(tags)

    async def _autodetect_tags_from_uhd(self):
        assert self.imdb_job.is_finished

        # Return sequence of tags from UHD. UHD returns comma-separated tags in a single string
        # which may contain entities like "&eacute;". Note that tags will be sanitized later by
        # normalize_tags().
        json = await self._tracker.get_uhd_info(self.imdb_id)
        tags = utils.html.as_text(json.get('tag', '')).split(',')
        return tags

    async def _autodetect_tags_from_imdb(self):
        # Return sequence of tags from IMDb. This may be necessary if UHD returns less than 3 tags,
        # which is the minimum. Ideally, we would only request IMDb tags if UHD tags are lacking,
        # but it's simpler and faster this way.
        async def get_tags(method):
            try:
                more_tags = await getattr(self.imdb, method)(self.imdb_id)
            except errors.RequestError:
                return ()
            else:
                return more_tags

        tags = []
        tags.extend(await get_tags('genres'))
        tags.extend(await get_tags('directors'))
        tags.extend(await get_tags('creators'))
        tags.extend(await get_tags('cast'))
        return tags

    max_tags_length = 200

    def normalize_tags(self, text):
        # Remove leading/trailing whitespace, remove empty tags, replace spaces with ".", etc.
        seq = [
            tag.strip().casefold().replace(' ', '.')
            for line in text.splitlines()
            for tag in line.split(',')
            if tag.strip()
        ]

        # Deduplicate while maintaining order.
        seq = list(dict.fromkeys(seq))

        # Ensure maximum combined length of `max_tag_length`.
        while seq and len(','.join(seq)) > self.max_tags_length:
            del seq[-1]
        return ', '.join(seq)

    min_tags_count = 3

    def validate_tags(self, text):
        tags = [tag for tag in text.split(',') if tag.strip()]
        if len(tags) < self.min_tags_count:
            raise ValueError(f'At least {self.min_tags_count} tags are required.')

    async def get_poster_from_tracker(self):
        await self.imdb_job.wait_finished()
        json = await self._tracker.get_uhd_info(self.imdb_id)
        poster = json.get('photo', None)
        _log.debug('Poster from UHD: %r', poster)
        if poster:
            return {
                'poster': poster,
                'width': None,
                'height': None,
                'imagehosts': (),
                'write_to': None,
            }

    @functools.cached_property
    def trailer_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('trailer'),
            label='Trailer',
            precondition=self.make_precondition('trailer_job'),
            prejobs=(
                self.imdb_job,
            ),
            text=self.autodetect_trailer,
            warn_exceptions=(
                errors.RequestError,
            ),
            normalizer=self.normalize_trailer,
            validator=self.validate_trailer,
            finish_on_success=True,
            **self.common_job_args(ignore_cache=bool('trailer' in self.options)),
        )

    async def autodetect_trailer(self):
        # Get trailer from user.
        if self.options.get('trailer', ''):
            return self.options['trailer']

        # Get trailer from UHD.
        assert self.imdb_job.is_finished
        json = await self._tracker.get_uhd_info(self.imdb_id)
        trailer_id = json.get('trailer', None)
        if trailer_id:
            return trailer_id

        # Default to no trailer.
        return ''

    def normalize_trailer(self, text):
        try:
            return 'https://youtu.be/' + self.get_youtube_id(text)
        except ValueError:
            # Keep invalid URL so the user can fix it.
            return text

    def validate_trailer(self, text):
        if text:
            # Raise ValueError if no YouTube ID is found.
            self.get_youtube_id(text)

    _YOUTUBE_ID_NO_DEFAULT = object()

    def get_youtube_id(self, url, default=_YOUTUBE_ID_NO_DEFAULT):
        """
        Find YouTube video ID in `url`

        :param url: Any YouTube URL
        :param default: Return value if no YouTube ID can be found in `url`

            If not provided, raise :class:`ValueError` if no YouTube ID can be
            found in `url`.
        """
        url_ = urllib.parse.urlparse(url)
        if not url_.hostname:
            if re.search(r'^([a-zA-Z0-9_-]+)$', url):
                # `url` is YouTube ID.
                return url

        elif (
                re.search(r'youtu(?:be|)\.[a-z]{2,3}', url_.hostname)
                and (
                    (match := re.search(r'\bv=([a-zA-Z0-9_-]+)\b', url_.query))
                    or (match := re.search(r'^/(?:embed/|v/|watch/|)([a-zA-Z0-9_-]+)$', url_.path))
                )
        ):
            # Found YouTube ID in `url`.
            return match.group(1)

        if default is self._YOUTUBE_ID_NO_DEFAULT:
            # No default value provided - raise exception.
            raise ValueError('Not a YouTube ID or URL.')
        else:
            return default

    @functools.cached_property
    def description_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('description'),
            label='Description',
            precondition=self.make_precondition('description_job'),
            prejobs=(
                self.screenshots_job,
                self.upload_screenshots_job,
                self.mediainfo_job,
            ),
            text=self.generate_description,
            error_exceptions=(
                errors.ContentError,  # Raised by read_nfo()
            ),
            hidden=True,
            finish_on_success=True,
            read_only=True,
            **self.common_job_args(ignore_cache=True),
        )

    image_host_config = {
        'common': {'thumb_width': 350},
    }

    def generate_description(self):
        screenshots = self.generate_description_screenshots()
        parts = (
            self.generate_description_nfo(),
            (
                f'[center]{screenshots}[/center]'
                if screenshots else
                ''
            ),
            self.generate_promotion_bbcode(),
        )
        return '\n\n'.join(part for part in parts if part)

    def generate_description_screenshots(self):
        assert self.upload_screenshots_job.is_finished
        return utils.bbcode.screenshots_grid(
            screenshots=self.upload_screenshots_job.uploaded_images,
            columns=2,
            horizontal_spacer='   ',
            vertical_spacer='\n\n',
        )

    def generate_description_nfo(self):
        nfo = self.read_nfo(strip=True)
        if nfo:
            return (
                '[spoiler=NFO]'
                + '[code]'
                + nfo
                + '[/code]'
                + '[/spoiler]'
            )

    @functools.cached_property
    def automerge_group_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('automerge-group'),
            label='Automerge Group',
            precondition=self.make_precondition('automerge_group_job'),
            prejobs=(
                self.imdb_job,
                self.type_job,
                self.season_job,
                self.login_job,
            ),
            autodetect=self.autodetect_automerge_group,
            autofinish=True,
            options=(
                ('Yes', True),
                ('No', False),
            ),
            **self.common_job_args(ignore_cache=True),
        )

    async def autodetect_automerge_group(self, _):
        assert self.season_job.is_finished
        if self.season_number is not None:
            # All TV seasons share the same IMDB ID, but they are grouped by season
            # number. From the Uploading Guide v2 in the wiki:
            # > Auto-Merge should always be selected unless you are uploading a
            # > TV season that doesn't have a torrent group yet.
            # https://uhdbits.org/wiki.php?action=article&id=33
            #
            # This implementation searches for the IMDb ID and tries to find a
            # group named ".* Season \d+" in the returned HTML.
            season_group_names = await self._get_season_group_names()
            target_group_name_suffix = f'Season {self.season_number:02d}'.lower()
            for group_name in season_group_names:
                # Example season group names:
                #  - The Title
                #  - The Title Season 03
                #  - The Title Season 03 / The AKA Title
                if re.search(rf'\s+{target_group_name_suffix}\b', group_name):
                    _log.debug('Found existing season group: %r', group_name)
                    return 'Yes'
                else:
                    _log.debug('Existing season group does not match %r: %r',
                               target_group_name_suffix, group_name)

            # Looks like season group doesn't exist yet.
            return 'No'
        else:
            # Movies are always autogrouped by IMDb ID
            return 'Yes'

    async def _get_season_group_names(self):
        response = await self._tracker._request(
            method='GET',
            url=self._tracker._torrents_url,
            params={
                'searchstr': self.imdb_id,
            },
            error_prefix='Automerge group check failed',
        )

        group_names = []
        doc = utils.html.parse(response)
        for tag in doc.find_all('a', {'class': 'torrent_name'}):
            group_name = utils.html.as_text(tag).strip()
            group_names.append(unidecode.unidecode(group_name.lower()))
        _log.debug('Existing season groups: %r', group_names)
        return group_names

    release_name_translation = {
        'group': {
            re.compile(r'^NOGROUP$'): 'Unknown',
        },
    }

    @property
    def post_data(self):
        return {
            'submit': 'true',

            # Type ("0" for Movie, "2" for TV)
            'type': self.get_job_attribute(self.type_job, 'choice'),

            # IMDb ID ("tt...")
            'imdbid': self.get_job_output(self.imdb_job, slice=0),

            # Original title
            'title': self.release_name.title,

            # English title
            'OtherTitle': self.release_name.title_aka,

            # Uploading Guide v2 says: "Disregard this field"
            'smalldesc': '',

            # Year
            'year': self.get_job_output(self.year_job, slice=0),

            # Season number or `None` (i.e. no submission of "season") for movie
            'season': self.season_number,

            # Quality (e.g. "1080p")
            'format': self.get_job_attribute(self.quality_job, 'choice'),

            # Group
            'team': self.release_name.group,

            # Version (e.g. "Director's Cut")
            'Version': ' / '.join(self.get_job_output(self.version_job)),

            # Source ("Media" on the website) (e.g. "BluRay")
            'media': self.get_job_attribute(self.source_job, 'choice'),

            # Codec (e.g. "x264")
            'codec': self.get_job_attribute(self.codec_job, 'choice'),

            # HDR format (e.g. "HDR10" or "DoVi")
            'hdr': self.get_job_attribute(self.hdr_format_job, 'choice'),

            # "genre_tags" is a side-effect of the dropdown list that lets the
            # user pick tags. This is probably ignored by the server, but we
            # keep it to reduce the bug surface.
            'genre_tags': '---',

            # Tags (We show them separated by ", " but submit them with ",".)
            'tags': ','.join(
                tag_stripped
                for tag in self.get_job_output(self.tags_job, slice=0).split(',')
                if (tag_stripped := tag.strip())
            ),

            # Poster URL
            'image': self.get_job_output(self.poster_job, slice=0),

            # Trailer (YouTube ID)
            'trailer': self.get_youtube_id(
                self.get_job_output(self.trailer_job, slice=0),
                default='',
            ),

            # Mediainfo
            'mediainfo': self.get_job_output(self.mediainfo_job, slice=0),

            # Screenshots and release info
            'release_desc': self.get_job_output(self.description_job, slice=0),

            # Group with anything that has the same IMDB ID
            'auto_merge_group': (
                'on'
                if self.get_job_attribute(self.automerge_group_job, 'choice') else
                None
            ),

            # Internal release
            'internal': 'on' if self.options['internal'] else None,

            # No support for exclusive releases (this is intentional)
            # 'exclude': '0',

            # 3D version
            'd3d': '1' if self.options['3d'] else None,

            # Release contains Vietnamese Audio dub
            'vie': '1' if self.options['vie'] else None,

            # Scene release
            'scene': '1' if self.get_job_attribute(self.scene_check_job, 'is_scene_release') else None,

            # Upload anonymously
            'anonymous': '1' if self.options['anonymous'] else None,
        }

    @property
    def post_files(self):
        return {
            'file_input': {
                'file': self.torrent_filepath,
                'mimetype': 'application/x-bittorrent',
            },
        }
