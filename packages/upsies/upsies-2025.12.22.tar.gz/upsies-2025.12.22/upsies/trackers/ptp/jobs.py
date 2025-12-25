"""
Concrete :class:`~.TrackerJobsBase` subclass for PTP
"""

import functools
import itertools
import re
from datetime import datetime

import async_lru

from ... import errors, jobs, uis, utils
from ...utils.release import ReleaseType
from ..base import TrackerJobsBase
from . import metadata

import logging  # isort:skip
_log = logging.getLogger(__name__)


class PtpTrackerJobs(TrackerJobsBase):

    @functools.cached_property
    def jobs_before_upload(self):
        # NOTE: Keep in mind that the order of jobs is important for
        #       isolated_jobs: The final job is the overall result, so if
        #       upload_screenshots_job is listed after description_job,
        #       --only-description is going to print the list of uploaded
        #       screenshot URLs.
        return (
            self.login_job,

            # Common interactive jobs
            self.playlists_job,
            self.imdb_job,
            self.tmdb_job,
            self.type_job,
            self.ptp_group_id_job,
            self.source_job,
            self.scene_check_job,

            # Interactive jobs that only run if movie does not exists on PTP yet
            self.title_job,
            self.year_job,
            self.edition_job,
            self.plot_job,
            self.tags_job,
            self.poster_job,
            self.artists_job,

            # Background jobs
            self.create_torrent_job,
            self.mediainfo_job,
            self.bdinfo_job,
            self.screenshots_job,
            self.upload_screenshots_job,
            self.audio_languages_job,
            self.subtitle_languages_job,
            self.trumpable_job,
            self.description_job,
            self.rules_job,
            self.nfo_job,
        )

    @property
    def isolated_jobs(self):
        """
        Sequence of job attribute names (e.g. "title_job") that were singled
        out by the user, e.g. with --only-title
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
            prejobs=self.get_job_and_dependencies(
                self.imdb_job,
                self.tmdb_job,
            ),
            autodetect=self.autodetect_type,
            options=metadata.types,
            # If user specified a type, e.g. via CLI, do not make them select it
            # again in the TUI.
            autofinish=bool(self.options.get('type')),
            # Ignore cached type if CLI option --type is provided.
            **self.common_job_args(ignore_cache=bool(self.options.get('type'))),
        )

    def autodetect_type(self, _):
        # User explicitly specified type, e.g. via CLI.
        if self.options.get('type'):
            for type, regex in metadata.types.items():
                if regex.search(self.options['type']):
                    return type

        # Miniseries if user selected a TV ID.
        # NOTE: Do not check for ReleaseType.episode because sometimes movies are tracked as
        #       episodes from a collection on IMDb or episodes are allowed to be uploaded as movies.
        _log.debug('Selected IMDb: %r', self.imdb_job.selected)
        if self.imdb_job.selected.get('type') is ReleaseType.season:
            return 'Miniseries'

        _log.debug('Selected TMDb: %r', self.tmdb_job.selected)
        if self.tmdb_job.selected.get('type') is ReleaseType.season:
            return 'Miniseries'

        # Short film if runtime 45 min or less.
        main_video = utils.fs.find_main_video(self.content_path)
        if utils.mediainfo.get_duration(main_video) <= 45 * 60:
            return 'Short Film'

    @functools.cached_property
    def imdb_job(self):
        imdb_job = super().imdb_job
        imdb_job.no_id_ok = True
        return imdb_job

    @functools.cached_property
    def tmdb_job(self):
        tmdb_job = super().tmdb_job
        tmdb_job.no_id_ok = True
        tmdb_job.prejobs += (self.imdb_job,)
        tmdb_job.precondition = self.make_precondition('tmdb_job', precondition=self.no_imdb_id_available)
        return tmdb_job

    def no_imdb_id_available(self):
        return not bool(self.imdb_id)

    @functools.cached_property
    def audio_languages_job(self):
        return jobs.custom.CustomJob(
            name=self.get_job_name('audio-languages'),
            label='Audio Languages',
            precondition=self.make_precondition('audio_languages_job'),
            worker=self.autodetect_audio_languages,
            no_output_is_ok=True,
            catch=(
                errors.ContentError,
            ),
            **self.common_job_args(ignore_cache=True),
        )

    async def autodetect_audio_languages(self, job):
        audio_languages = utils.mediainfo.audio.get_audio_languages(
            self.content_path,
            default='?',
            exclude_commentary=True,
        )
        _log.debug('Audio languages: %r', audio_languages)
        for language in audio_languages:
            self.audio_languages_job.add_output(language)

    @functools.cached_property
    def subtitle_languages_job(self):
        return jobs.custom.CustomJob(
            name=self.get_job_name('subtitle-languages'),
            label='Subtitle Languages',
            precondition=self.make_precondition('subtitle_languages_job'),
            worker=self.autodetect_subtitle_languages,
            catch=(
                ValueError,
            ),
            no_output_is_ok=True,
            **self.common_job_args(ignore_cache=True),
        )

    async def autodetect_subtitle_languages(self, job):
        # Combine user-provided subtitles, e.g. via --subtitles and autodetected subtitles.
        user_subtitles = tuple(self.options.get('subtitles') or ())
        _log.debug('User-specified subtitles: %r', user_subtitles)

        # Check if user-provided subtitles are supported by the PTP API because it would be
        # unexpected to manually specify a subtitle with no effect.
        unsupported_subtitles = [
            subtitle
            for subtitle in user_subtitles
            if str(subtitle) not in metadata.subtitles
        ]
        if unsupported_subtitles:
            raise ValueError('Unsupported subtitles: ' + ', '.join(str(s) for s in unsupported_subtitles))

        # Autodetected subtitles from .srt, .idx/.sub, VIDEO_TS, BDMV, etc. Ignore if those are not
        # supported by the PTP API.
        autodetected_subtitles = self.subtitles
        _log.debug('Autodetected subtitles: %r', autodetected_subtitles)

        subtitles = user_subtitles + autodetected_subtitles
        _log.debug('Subtitle languages: %r', subtitles)
        for subtitle in subtitles:
            self.subtitle_languages_job.add_output(subtitle)

        # If there are any subtitle tracks without a language tag, tell the user
        # to manually check the subtitle boxes on the website.
        if any(s.language == '?' for s in subtitles):
            self.subtitle_languages_job.warn(
                "Some subtitle tracks don't have a language tag.\n"
                'Please add any missing subtitle languages manually\n'
                'on the website after uploading.'
            )

    @functools.cached_property
    def trumpable_job(self):
        return jobs.custom.CustomJob(
            name=self.get_job_name('trumpable'),
            label='Trumpable',
            precondition=self.make_precondition('trumpable_job'),
            prejobs=self.get_job_and_dependencies(
                self.audio_languages_job,
                self.subtitle_languages_job,
            ),
            worker=self.autodetect_trumpable,
            no_output_is_ok=True,
            **self.common_job_args(ignore_cache=True),
        )

    async def autodetect_trumpable(self, job):
        # Set of TrumpableReasons.
        reasons = set()

        # If there is no linguistic content, we don't ask stupid questions about subtitles.
        if not utils.mediainfo.audio.has_language(self.content_path, default=False):
            _log.debug('No audio track or no linguistic content in main audio track')

        else:
            # Reason: Hardcoded subtitles.
            # The option "hardcoded_subtitles" is `None` if user has not made a choice.
            if self.options.get('hardcoded_subtitles', None) is True:
                reasons.add(metadata.TrumpableReason.HARDCODED_SUBTITLES)

            # Reason: No English audio and no English subtitles.
            if self.options.get('no_english_subtitles', None) in (True, False):
                # User specified "No English subtitles" or "English subtitles".
                if self.options['no_english_subtitles']:
                    reasons.add(metadata.TrumpableReason.NO_ENGLISH_SUBTITLES)

            elif await self.trumpable_no_english_subtitles():
                # Release has no English audio and no English subtitle track, but it could still have
                # hardcoded subtitles. We can't just check `reasons` for `HARDCODED_SUBTITLES` because
                # they could be non-English, so we have to ask the user. User may have already specified
                # --hardcoded-subtitles, so we ask the question accordingly.
                if metadata.TrumpableReason.HARDCODED_SUBTITLES in reasons:
                    question = 'Are the hardcoded subtitles English?'
                else:
                    question = 'Does this release have hardcoded English subtitles?'
                if await self.trumpable_prompt(question):
                    reasons.add(metadata.TrumpableReason.HARDCODED_SUBTITLES)
                else:
                    reasons.add(metadata.TrumpableReason.NO_ENGLISH_SUBTITLES)

        _log.debug('Trumpable reasons: %r', reasons)
        return reasons

    async def trumpable_no_english_subtitles(self):
        assert self.audio_languages_job.is_finished
        assert self.subtitle_languages_job.is_finished

        # `audio_languages` and `subtitle_languages` should be BCP47 (e.g. "en" or "en-US").
        audio_languages = self.audio_languages_job.output
        subtitle_languages = self.subtitle_languages_job.output
        if (
                # Not a silent film?
                audio_languages
                # No properly tagged English audio track?
                and not any(language.startswith('en') for language in audio_languages)
                # No properly tagged English subtitles?
                and not any(language.startswith('en') for language in subtitle_languages)
        ):
            # Ask the user about any unknown audio languages.
            has_english_audio_track = False
            if any(lang.startswith('?') for lang in audio_languages):
                has_english_audio_track = await self.trumpable_prompt(
                    'Does this release have an English audio track?\n'
                    '(Commentary and the like do not count.)'
                )

            has_english_subtitle_track = False
            if (
                    not has_english_audio_track
                    # Ask the user about any unknown subtitle languages.
                    and any(lang.startswith('?') for lang in subtitle_languages)
            ):
                has_english_subtitle_track = await self.trumpable_prompt(
                    'Does this release have English subtitles for the main audio track?'
                )

            return bool(
                not has_english_audio_track
                and not has_english_subtitle_track
            )

        return False

    async def trumpable_prompt(self, question):
        _, value = await self.trumpable_job.add_prompt(
            uis.prompts.RadioListPrompt(
                question=question,
                options=(
                    ('Yes', True),
                    ('No', False),
                ),
                focused=1,
            )
        )
        return value

    @functools.cached_property
    def description_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('description'),
            label='Description',
            precondition=self.make_precondition('description_job'),
            prejobs=self.get_job_and_dependencies(
                self.playlists_job,
                self.mediainfo_job,
                self.bdinfo_job,
                self.screenshots_job,
                self.upload_screenshots_job,
            ),
            text=self.generate_description,
            read_only=True,
            hidden=True,
            finish_on_success=True,
            **self.common_job_args(ignore_cache=True),
        )

    async def generate_description(self):
        original_release_name = (
            '[size=4][b]'
            + utils.fs.basename(
                utils.fs.strip_extension(self.content_path)
            )
            + '[/b][/size]'
        )

        # For each video, list mediainfo(s) and bdinfo(s), followed by screenshots.
        bbcode_per_video = []
        for info in self.video_info.values():
            # Mediainfo and BDInfo reports zipped together.
            reports = '\n'.join(
                f'[mediainfo]{report}[/mediainfo]'
                for reports in itertools.zip_longest(
                        info.get('mediainfos', ()),
                        (
                            bdinfo.quick_summary
                            for bdinfo in info.get('bdinfos', ())
                        ),
                        fillvalue=None,
                )
                for report in reports
                if report is not None
            )

            # Screenshots.
            screenshots = '\n'.join(
                f'[img={url}]'
                for url in info.get('screenshot_urls', ())
            )

            # `reports` and/or `screenshots` may be empty.
            merged = ''.join((reports, screenshots)).strip()
            if merged:
                bbcode_per_video.append(merged)

        return (
            original_release_name
            + '\n\n'
            + '\n\n[hr]\n'.join(bbcode_per_video)
        ).strip()

    # Create screenshots/mediainfo/bdinfo from each video file or playlist.
    document_all_videos = True

    @functools.cached_property
    def screenshots_job(self):
        # screenshots_job uses screenshots_count, which uses type_job to determine if we're dealing
        # with a miniseries (`screenshots_from_episode`) or something else
        # (`screenshots_from_movie`), so type_job must finish first before we can start.
        screenshots_job = super().screenshots_job
        screenshots_job.prejobs += (self.type_job,)
        return screenshots_job

    @functools.cached_property
    def screenshots_count(self):
        """
        How many screenshots to make

        Return :attr:`options`\\ ``["screenshots_count"]`` it it exists and is truthy. This value
        should be explicitly set by the user, e.g. via a CLI argument or GUI element.

        Otherwise, return a coroutine function that waits for :attr:`type_job`. If the user selected
        "Miniseries", return :attr:`options`\\ ``["screenshots_from_episode"]``. If not, return
        :attr:`options`\\ ``["screenshots_from_movie"]``.
        """
        # CLI option, GUI widget, etc
        if self.options.get('screenshots_count'):
            return self.options['screenshots_count']

        async def get_screenshots_count():
            await self.type_job.wait_finished()
            if self.type_job.output == ('Miniseries',):
                return self.options['screenshots_from_episode']
            else:
                return self.options['screenshots_from_movie']

        return get_screenshots_count

    @functools.cached_property
    def ptp_group_id_job(self):
        return jobs.custom.CustomJob(
            name=self.get_job_name('ptp-group-id'),
            label='PTP Group ID',
            precondition=self.make_precondition('ptp_group_id_job'),
            prejobs=self.get_job_and_dependencies(
                self.imdb_job,
            ),
            worker=self.get_ptp_group_id,
            catch=(
                errors.RequestError,
            ),
            **self.common_job_args(),
        )

    async def get_ptp_group_id(self, _):
        # Get group ID from PTP by IMDb ID.
        assert self.imdb_job.is_finished
        group_id = await self.tracker.get_ptp_group_id_by_imdb_id(self.imdb_id)
        if group_id:
            _log.debug('PTP group ID via IMDb ID: %r -> %r', self.imdb_id, group_id)
            return group_id
        else:
            # If there is no existing PTP group, ask the user. Usually this happens if PTP doesn't
            # know this movie yet. The user can just press enter to create a new PTP group.
            #
            # But it's also possible that PTP has a group for this movie while it has no IMDb ID
            # (i.e. it does not exist on IMDb). In that case, the user must find the existing PTP
            # group ID and enter it manually.
            self.ptp_group_id_job.info = 'Enter PTP group ID or nothing if this movie does not exist on PTP.'
            ptp_group_id = await self.ptp_group_id_job.add_prompt(
                uis.prompts.TextPrompt()
            )
            _log.debug('PTP group ID from user: %r', ptp_group_id)
            return ptp_group_id.strip()

    @property
    def ptp_group_id(self):
        """
        PTP group ID if :attr:`ptp_group_id_job` is finished and group ID
        was found, `None` otherwise
        """
        if self.ptp_group_id_job.is_finished and self.ptp_group_id_job.output:
            return self.ptp_group_id_job.output[0]

    def ptp_group_does_not_exist(self):
        """
        Whether no releases of the user-selected IMDb ID already exist on PTP

        :attr:`ptp_group_id_job` must be finished when this is called.

        This is used as a :attr:`~.JobBase.precondition` for jobs that are only
        needed if the server doesn't have any releases for this IMDb ID yet.
        """
        assert self.ptp_group_id_job.is_finished
        return not self.ptp_group_id

    @async_lru.alru_cache
    async def get_movie_metadata(self):
        """
        Wrapper around :meth:`~.PtpTrackerJobs.get_movie_metadata` that defaults to from
        :attr:`~.TrackerJobsBase.tmdb`

        If no IMDb ID was selected by the user or if the metadata from PTP is incomplete, try to add
        values from TMDb.
        """
        # Get PTP-normalized metadata by IMDb ID. If the IMDb ID is falsy, we get a metadata dict
        # with empty values.
        metadata = await self.tracker.get_movie_metadata(self.imdb_id)
        _log.debug('PTP metadata:')
        for k, v in metadata.items():
            _log.debug(f'  * {k} = {v!r}')

        if self.tmdb_id:
            # If there is no IMDb ID or the PTP metadata is incomplete or whatever, update missing
            # information with information from TMDb. Some movies are on TMDb but not on IMDb.

            async def update(key, method_name):
                if not metadata[key]:
                    method = getattr(self.tmdb, method_name)
                    try:
                        metadata[key] = await method(self.tmdb_id)
                    except errors.RequestError as e:
                        _log.debug(f'Ignoring {e!r} from {method_name}({self.tmdb_id!r})')

            await update('title', 'title_original')
            await update('plot', 'summary')
            await update('year', 'year')
            await update('poster', 'poster_url')
            await update('countries', 'countries')
            await update('tags', 'genres')

            _log.debug(f'Updated metadata with TMDb ID {self.tmdb_id}:')
            for k, v in metadata.items():
                _log.debug(f'  * {k} = {v!r}')

        return metadata

    @functools.cached_property
    def title_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('title'),
            label='Title',
            precondition=self.make_precondition(
                'title_job',
                # Don't run this job if PTP already knows this movie.
                precondition=self.ptp_group_does_not_exist,
            ),
            prejobs=self.get_job_and_dependencies(
                # We need to wait for the PTP group ID to become available
                # before we can check if it exists.
                self.ptp_group_id_job,
                # fetch_title() needs the IMDb ID for get_movie_metadata().
                self.imdb_job,
            ),
            text=self.fetch_title,
            warn_exceptions=(
                # Raised when get_movie_metadata() cannot find IMDb ID.
                errors.RequestError,
            ),
            normalizer=self.normalize_title,
            validator=self.validate_title,
            **self.common_job_args(),
        )

    async def fetch_title(self):
        assert self.imdb_job.is_finished
        # Fill in title from release name first.
        self.title_job.text = self.release_name.title
        # Fetch canonical title from PTP.
        metadata = await self.get_movie_metadata()
        # Default to `None` to use title from release name.
        return metadata['title'] or None

    def normalize_title(self, text):
        return text.strip()

    def validate_title(self, text):
        if not text:
            raise ValueError('Title must not be empty.')

    @functools.cached_property
    def year_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('year'),
            label='Year',
            precondition=self.make_precondition(
                'year_job',
                # Don't run this job if PTP already knows this movie.
                precondition=self.ptp_group_does_not_exist,
            ),
            prejobs=self.get_job_and_dependencies(
                # We need to wait for the PTP group ID to become available
                # before we can check if it exists.
                self.ptp_group_id_job,
                # fetch_year() needs the IMDb ID for get_movie_metadata().
                self.imdb_job,
            ),
            text=self.fetch_year,
            warn_exceptions=(
                # Raised when get_movie_metadata() cannot find IMDb ID.
                errors.RequestError,
            ),
            normalizer=self.normalize_year,
            validator=self.validate_year,
            **self.common_job_args(),
        )

    async def fetch_year(self):
        assert self.imdb_job.is_finished
        # Load year from release name into text field.
        self.year_job.text = self.release_name.year
        # Try to get canonical year from PTP.
        metadata = await self.get_movie_metadata()
        # Default to `None` to use year from release name.
        return metadata['year'] or None

    def normalize_year(self, text):
        return text.strip()

    def validate_year(self, text):
        if not text:
            raise ValueError('Year must not be empty.')
        try:
            year = int(text)
        except ValueError as e:
            raise ValueError('Year is not a number.') from e
        else:
            if not 1800 < year < datetime.now().year + 10:
                raise ValueError('Year is not reasonable.')

    @functools.cached_property
    def edition_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('edition'),
            label='Edition',
            precondition=self.make_precondition('edition_job'),
            text=self.autodetect_edition,
            finish_on_success=True,
            **self.common_job_args(ignore_cache=True),
        )

    async def autodetect_edition(self):
        # List of keys in metadata.editions. The corresponding values are
        # returned in the same order as they are specified in metadata.editions.
        edition_keys = []

        for key, is_edition in self.autodetect_edition_map.items():
            if is_edition(self):
                edition_keys.append(key)

        return ' / '.join(
            metadata.editions[key]
            for key in edition_keys
        )

    autodetect_edition_map = {
        'collection.criterion': lambda self: 'Criterion' in self.release_name.edition,
        # 'collection.masters': lambda self: False,
        # 'collection.warner': lambda self: False,

        'edition.dc': lambda self: "Director's Cut" in self.release_name.edition,
        'edition.extended': lambda self: 'Extended Cut' in self.release_name.edition,
        # 'edition.rifftrax': lambda self: False,
        'edition.theatrical': lambda self: 'Theatrical Cut' in self.release_name.edition,
        'edition.uncut': lambda self: 'Uncut' in self.release_name.edition,
        'edition.unrated': lambda self: 'Unrated' in self.release_name.edition,

        'feature.remux': lambda self: 'Remux' in self.release_name.source,
        'feature.2in1': lambda self: '2in1' in self.release_name.edition,
        # 'feature.2disc': lambda self: False,
        # 'feature.3d_anaglyph': lambda self: False,
        # 'feature.3d_full_sbs': lambda self: False,
        # 'feature.3d_half_ou': lambda self: False,
        # 'feature.3D_half_sbs': lambda self: False,
        'feature.4krestoration': lambda self: '4k Restored' in self.release_name.edition,
        'feature.4kremaster': lambda self: '4k Remastered' in self.release_name.edition,
        'feature.10bit': lambda self: (
            utils.mediainfo.video.get_bit_depth(self.content_path, default=None) == 10
            and 'HDR' not in self.release_name.hdr_format
            and 'DV' not in self.release_name.hdr_format
        ),
        # 'feature.extras': lambda self: False,
        # 'feature.2d3d_edition': lambda self: False,
        'feature.dtsx': lambda self: 'DTS:X' in self.release_name.audio_format,
        'feature.dolby_atmos': lambda self: 'Atmos' in self.release_name.audio_format,
        'feature.dolby_vision': lambda self: 'DV' in self.release_name.hdr_format,
        'feature.hdr10': lambda self: re.search(r'HDR10(?!\+)', self.release_name.hdr_format),
        'feature.hdr10+': lambda self: 'HDR10+' in self.release_name.hdr_format,
        'feature.dual_audio': lambda self: self.release_name.has_dual_audio,
        # 'feature.english_dub': lambda self: False,
        'feature.commentary': lambda self: self.release_name.has_commentary,
    }

    @functools.cached_property
    def tags_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('tags'),
            label='Tags',
            precondition=self.make_precondition(
                'tags_job',
                # Don't run this job if PTP already knows this movie.
                precondition=self.ptp_group_does_not_exist,
            ),
            prejobs=self.get_job_and_dependencies(
                # We need to wait for the PTP group ID to become available
                # before we can check if it exists.
                self.ptp_group_id_job,
                # fetch_tags() needs the IMDb ID for get_movie_metadata().
                self.imdb_job,
            ),
            text=self.fetch_tags,
            warn_exceptions=(
                # Raised when get_movie_metadata() cannot find IMDb ID.
                errors.RequestError,
            ),
            normalizer=self.normalize_tags,
            validator=self.validate_tags,
            **self.common_job_args(),
        )

    async def fetch_tags(self):
        assert self.imdb_job.is_finished
        metadata = await self.get_movie_metadata()
        return ', '.join(metadata['tags'])

    def normalize_tags(self, text):
        tags = [tag.strip().lower() for tag in text.split(',')]
        tags = sorted(dict.fromkeys(tags))
        # Replace space with ".".
        tags = ('.'.join(re.split(r'\s+', tag)) for tag in tags)
        # Fix "science fiction" tag. ("sci.fi" seems to be the most popular.)
        tags = (
            re.sub(r'^(?i:sci(?:ence|).?fi(?:ction|))$', 'sci.fi', tag)
            for tag in tags
        )
        return ', '.join(tag for tag in tags if tag)

    def validate_tags(self, text):
        if not text.strip():
            raise ValueError('You must provide at least one tag.')

        if len(self.normalize_tags(text)) > 200:
            raise ValueError('You provided too many tags.')

    @functools.cached_property
    def poster_job(self):
        job = super().poster_job
        # Hide poster_job until imdb_job and ptp_group_id_job are done.
        job.prejobs += (
            self.imdb_job,
            self.ptp_group_id_job,
        )
        return job

    def make_poster_job_precondition(self):
        # Do not run poster_job if there is already a PTP group, meaning the
        # server already has a poster.
        return self.make_precondition('poster_job', precondition=self.ptp_group_does_not_exist)

    @functools.cached_property
    def plot_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('plot'),
            label='Plot',
            precondition=self.make_precondition(
                'plot_job',
                # Don't run this job if PTP already knows this movie.
                precondition=self.ptp_group_does_not_exist,
            ),
            prejobs=self.get_job_and_dependencies(
                # We need to wait for the PTP group ID to become available
                # before we can check if it exists.
                self.ptp_group_id_job,
                # fetch_plot() needs the IMDb ID for get_movie_metadata().
                self.imdb_job,
            ),
            text=self.fetch_plot,
            warn_exceptions=(
                # Raised when get_movie_metadata() cannot find IMDb ID.
                errors.RequestError,
            ),
            normalizer=self.normalize_plot,
            finish_on_success=True,
            **self.common_job_args(),
        )

    async def fetch_plot(self):
        assert self.imdb_job.is_finished
        metadata = await self.get_movie_metadata()
        return metadata['plot']

    def normalize_plot(self, text):
        return text.strip()

    @functools.cached_property
    def artists_job(self):
        return jobs.custom.CustomJob(
            name=self.get_job_name('artists'),
            label='Artists',
            precondition=self.make_precondition(
                'artists_job',
                precondition=self.artists_job_precondition,
            ),
            prejobs=self.get_job_and_dependencies(
                # These jobs must finish before we can check the precondition.
                self.ptp_group_id_job,
                # We must have an IMDb ID to get artists from PTP.
                self.imdb_job,
            ),
            worker=self._get_artists,
            **self.common_job_args(),
        )

    def artists_job_precondition(self):
        # Don't ask user to provide artists if we can get them from PTP or IMDb.
        return (
            not self.ptp_group_id  # PTP does not know this movie.
            and not self.imdb_id   # IMDb does not know this movie.
        )

    async def _get_artists(self, job):
        # If movie is not on IMDb, try to get artists from TMDb.
        await self.imdb_job.wait_finished()
        if not self.imdb_id:
            await self._get_artists_from_tmdb(job)

        # Allow the user to add more artists manually.
        if job.output:
            # We found artists on TMDb. Focus "Stop adding artists" so user can just press enter.
            await self._get_artists_from_user(job, focused=-1)
        else:
            # We haven't found artists on TMDb. Focus "Add actor".
            await self._get_artists_from_user(job, focused=0)

    async def _get_artists_from_tmdb(self, job):
        # Pre-fill "Add artist" prompts with artists found on TMDb.
        await self.tmdb_job.wait_finished()
        if self.tmdb_id:
            artists = {
                metadata.ArtistImportance.DIRECTOR: await self.tmdb.directors(self.tmdb_id),
                metadata.ArtistImportance.ACTOR: await self.tmdb.cast(self.tmdb_id),
            }
            _log.debug('Artists found on TMDb:')
            for k, v in artists.items():
                _log.debug(' * %r: %r', k, v)

            # Get user confirmation for each artist.
            for importance, persons in artists.items():
                for person in persons:
                    _log.debug(f'Confirming TMDb artist: {importance!r}: {person}')
                    artist = await self._get_one_artist_from_user(job, importance, name=str(person), role=person.role)
                    # The user can prevent the artist from being added if they enter an empty name, in
                    # which case we get a falsy `artist` (None, empty `dict`, whatever).
                    if artist:
                        self._add_formatted_artist(job, artist)
                    else:
                        return

    async def _get_artists_from_user(self, job, focused):
        # Loop over artist prompts until the user stops the loop.
        while True:
            importance = await self._get_artist_importance(focused=focused)
            _log.debug('Adding artist: %r', importance)
            if importance:
                artist = await self._get_one_artist_from_user(job, importance)
                if artist:
                    self._add_formatted_artist(job, artist)
                else:
                    break
            else:
                # No `importance` means the user wants to stop entering artists.
                break

    async def _get_one_artist_from_user(self, job, importance, *, name='', role=''):
        # Keep asking for the name or other ID until we get a valid one.
        current_name = name
        while True:
            try:
                name, ptpurl = await self._get_artist_name_and_ptpurl(
                    question=f'{importance} name:',
                    name=current_name,
                )
            except errors.RequestedNotFoundError as e:
                _log.debug('Unknown artist: %r', e)
                job.warn(e)
                current_name = e.requested
            except errors.RequestError as e:
                _log.debug('Failed to get artist name: %r', e)
                job.warn(e)
            else:
                break
        _log.debug('Artist name and URL: (%r, %r)', name, ptpurl)
        job.clear_warnings()

        if name and ptpurl:
            # Only actors have a role, and it may be empty.
            if importance == metadata.ArtistImportance.ACTOR:
                role = await self._get_artist_role(question=f'{name} role (optional):', role=role)
                _log.debug('Artist role: %r', role)
            else:
                role = ''
            return {
                'importance': importance,
                'name': name,
                'ptpurl': ptpurl,
                'role': role,
            }

    async def _get_artist_name_and_ptpurl(self, question, name=''):
        self.artists_job.info = (
            'Enter artist name, IMDb link/ID, PTP link/ID '
            'or nothing to stop entering artists.'
        )
        id = await self.artists_job.add_prompt(uis.prompts.TextPrompt(
            question=question,
            text=name,
        ))
        id = id.strip()
        self.artists_job.info = ''

        if not id:
            # User wants to stop entering artists.
            return None, None

        # Get canonical name and PTP ID. This works for IMDb ID/URL and PTP URL.
        try:
            artist = await self.tracker.get_artist_metadata(id)
        except errors.RequestedNotFoundError as e:
            # Create new artist after confirmation or raise "Artist not found".
            artist_name = id
            if (
                    await self.artists_job.add_prompt(uis.prompts.RadioListPrompt(
                        question=f'Create new artist with the name "{artist_name}"?',
                        options=('Yes', 'No'),
                        focused='No',
                    )) == 'Yes'
                    and
                    await self.artists_job.add_prompt(uis.prompts.RadioListPrompt(
                        question=f'Are you sure "{artist_name}" does not exist on PTP or IMDb?',
                        options=('Yes', 'No'),
                        focused='No',
                    )) == 'Yes'
            ):
                artist = await self.tracker.create_artist(artist_name)
            else:
                raise e

        _log.debug('Got artist metadata: %r', artist)
        return artist['name'], artist['url']

    async def _get_artist_importance(self, focused=None):
        _label, enum = await self.artists_job.add_prompt(uis.prompts.RadioListPrompt(
            options=[
                (f'Add {str(importance).lower()}', importance)
                for importance in metadata.ArtistImportance
            ] + [
                ('Stop adding artists', None)
            ],
            focused=focused,
        ))
        return enum

    async def _get_artist_role(self, question, role=''):
        role = await self.artists_job.add_prompt(uis.prompts.TextPrompt(
            question=question,
            text=role,
        ))
        return role.strip()

    def _add_formatted_artist(self, job, artist):
        # IMPORTANT: If you change the output format, make sure to also change the regex in
        # _post_data_add_new_movie_artists.
        if artist.get('role'):
            job.add_output(f'{artist["importance"]}: {artist["name"]} | {artist["role"]} | {artist["ptpurl"]}')
        else:
            job.add_output(f'{artist["importance"]}: {artist["name"]} | {artist["ptpurl"]}')

    @functools.cached_property
    def source_job(self):
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('source'),
            label='Source',
            precondition=self.make_precondition('source_job'),
            text=self.autodetect_source,
            normalizer=self.normalize_source,
            validator=self.validate_source,
            finish_on_success=True,
            # Ignore cached source if CLI option --source is provided.
            **self.common_job_args(ignore_cache=bool(self.options.get('source'))),
        )

    def autodetect_source(self):
        if self.options.get('source'):
            # Get pre-specified source, e.g. from CLI argument.
            source = self.options['source']
        else:
            # Get source from release name.
            source = self.release_name.source

        # Find autodetected source in valid PTP sources
        for known_source, regex in metadata.sources.items():
            if regex.search(source):
                # Finish the job without prompting the user
                return known_source

        # Let the user fix the autodetected source
        self.source_job.text = source

    def normalize_source(self, text):
        text = text.strip()
        for source, regex in metadata.sources.items():
            if regex.search(text):
                return source
        return text

    def validate_source(self, text):
        if not text or text == 'UNKNOWN_SOURCE':
            raise ValueError('You must provide a source.')
        elif text not in metadata.sources:
            raise ValueError(f'Source is not valid: {text}')

    @property
    def post_data(self):
        post_data = self._post_data_common

        _log.debug('PTP group ID: %r', self.ptp_group_id)
        if self.ptp_group_id:
            _log.debug('Adding movie format to existing group')
            post_data.update(self._post_data_add_movie_format)
        else:
            _log.debug('Creating new movie group')
            post_data.update(self._post_data_add_new_movie)

        return post_data

    @property
    def _post_data_common(self):
        return {
            # Feature Film, Miniseries, Short Film, etc
            'type': self.get_job_attribute(self.type_job, 'choice'),

            # Mediainfo and Screenshots
            'release_desc': self.get_job_output(self.description_job, slice=0),

            # Is not main movie (bool)
            'special': '1' if self.options['not_main_movie'] else None,

            # Is personal rip (bool)
            'internalrip': '1' if self.options['personal_rip'] else None,

            # Is scene Release (bool)
            'scene': '1' if self.get_job_attribute(self.scene_check_job, 'is_scene_release') else None,

            # .nfo file content
            'nfo_text': self.nfo_text,

            # Upload token from staff
            'uploadtoken': self.options.get('upload_token', None),

            **self._post_data_common_source,
            **self._post_data_common_codec,
            **self._post_data_common_container,
            **self._post_data_common_resolution,
            **self._post_data_common_edition,
            **self._post_data_common_subtitles,
            **self._post_data_common_trumpable,
        }

    @property
    def _post_data_common_source(self):
        return {
            'source': 'Other',
            'other_source': self.get_job_output(self.source_job, slice=0),
        }

    @property
    def _post_data_common_codec(self):
        return {
            # Server-side autodetection
            'codec': '* Auto-detect',
            'other_codec': '',

            # # Custom codec
            # 'codec': 'Other',
            # 'other_codec': self.get_job_output(self.video_codec_job, slice=0),
        }

    @property
    def _post_data_common_container(self):
        return {
            # Server-side autodetection
            'container': '* Auto-detect',
            'other_container': ''

            # # Custom container
            # 'container': 'Other',
            # 'other_container': self.get_job_output(self.container_job, slice=0),
        }

    @property
    def _post_data_common_resolution(self):
        return {
            # Server-side autodetection
            'resolution': '* Auto-detect',
            'other_resolution': '',
        }

        # Custom resolution
        # resolution = self.get_job_output(self.resolution_job, slice=0)
        # # WIDTHxHEIGHT
        # if 'x' in resolution:
        #     width, height = resolution.split('x', maxsplit=1)
        #     return {
        #         'resolution': 'Other',  # Custom resolution
        #         'other_resolution_width': width,
        #         'other_resolution_height': height,
        #     }

        # # 1080p, 720p, etc
        # else:
        #     return {
        #         'resolution': resolution,
        #         'other_resolution': releaseInfo.Resolution,
        #     }

    @property
    def _post_data_common_subtitles(self):
        # Translate BCP47 codes into PTP numeric codes from upload.php
        ptp_codes = []
        for subtitle_text in self.subtitle_languages_job.output:
            # Remove subtitle format (e.g. "[SRT]").
            subtitle_text = re.sub(r'\[.+?\]', '', subtitle_text).strip()

            # Lookup "pt" and "pt-BR" format.
            ptp_code = metadata.subtitles.get(subtitle_text, None)
            if ptp_code:
                _log.debug('PTP subtitle code for %r: %r', subtitle_text, ptp_code)
                ptp_codes.append(ptp_code)

            # If subtitle is specified with a region (e.g. "en-AU"), try without the region.
            elif '-' in subtitle_text:
                subtitle_text = re.sub(r'-.*$', '', subtitle_text)
                ptp_code = metadata.subtitles.get(subtitle_text, None)
                if ptp_code:
                    _log.debug('PTP subtitle code for %r: %r', subtitle_text, ptp_code)
                    ptp_codes.append(ptp_code)

        # Add "No subtitles" flag if there are no subtitles. If we failed to detect some languages
        # or the PTP API doesn't support some of the detected languages, we also submit "No
        # subtitles". In that case, autodetect_subtitle_languages() should've already warned the
        # user to double-check after submission.
        if not ptp_codes:
            ptp_codes.append(metadata.subtitles['No Subtitles'])

        return {'subtitles[]': ptp_codes}

    @property
    def _post_data_common_edition(self):
        text = self.get_job_output(self.edition_job, slice=0)
        return {
            # Edition Information ("Director's Cut", "Dual Audio", etc.)
            'remaster': 'on' if text else None,
            'remaster_title': text if text else None,
            # 'remaster_year': ...,
            # 'remaster_other_input': ...,
        }

    @property
    def _post_data_common_trumpable(self):
        # NOTE: Only certain classes can submit trumpable tags. Trumpabale tags
        # from petty users are simply ignored and staff will have to add them.
        return {
            'trumpable[]': [
                # Convert pretty strings to API values
                metadata.TrumpableReason.from_string(string).value
                for string in self.trumpable_job.output
            ],
        }

    @property
    def _post_data_add_movie_format(self):
        # Upload another release to existing movie group
        return {
            'groupid': self.ptp_group_id,
        }

    @property
    def _post_data_add_new_movie(self):
        # Upload movie that is not on PTP yet in any format
        post_data = {
            # IMDb ID (must be 7 characters without the leading "tt")
            'imdb': self.tracker.normalize_imdb_id(self.imdb_id),
            # Release year
            'title': self.get_job_output(self.title_job, slice=0),
            # Release year
            'year': self.get_job_output(self.year_job, slice=0),
            # Movie plot or summary
            'album_desc': self.get_job_output(self.plot_job, slice=0),
            # Genre
            'tags': self.get_job_output(self.tags_job, slice=0),
            # Youtube ID
            # 'trailer': ...,
            # Poster URL
            'image': self.get_job_output(self.poster_job, slice=0),
        }
        post_data.update(self._post_data_add_new_movie_artists)
        return post_data

    @property
    def _post_data_add_new_movie_artists(self):
        # artists_job may not be running at all because artists are handled by
        # the server after the upload via the provided IMDb or PTP ID, so we
        # default to an empty output.
        lines = self.get_job_output(self.artists_job, default=())
        if lines:
            artistnames = []
            artistids = []
            importances = []
            roles = []

            # Possible formats:
            # > {importance}: {name} | {role} | {ptpurl}
            # > {importance}: {name} | {ptpurl}
            line_regex = re.compile(
                r'^(?P<importance>\w+?): '
                r'(?P<name>[^\|]+?) '
                r'(?:\| (?P<role>[^\|]+?) |)'
                r'\| (?P<ptpurl>https://.*)$'
            )

            # PTP URL format:
            # > https://hostname/artist.php?id=123456
            id_regex = re.compile(r'^.*?\bid=(\d+).*$')

            for line in lines:
                _log.debug('OUTPUT: %r', line)
                match = line_regex.search(line)
                _log.debug('match: %r', match)
                if match:
                    # Get ArtistImportance from human-readable string.
                    importance = metadata.ArtistImportance.from_string(match.group('importance'))

                    # Get PTP ID from URL.
                    id = id_regex.sub(r'\1', match.group('ptpurl'))
                    assert all(c in '0123456789' for c in id), id

                    artistnames.append(match.group('name'))
                    importances.append(importance.value)
                    artistids.append(id)
                    roles.append(match.group('role') or '')

                else:
                    raise RuntimeError(f'Unexpected line: {line}')

            # Sanity check: Make sure all lists have the same length.
            artists_count = len(lines)
            for lst in (
                    artistnames,
                    artistids,
                    importances,
                    roles,
            ):
                assert len(lst) == artists_count, (lst, artists_count)

            return {
                'artistnames[]': artistnames,
                'artistids[]': artistids,
                'importances[]': importances,
                'roles[]': roles,
            }

        else:
            return {}
