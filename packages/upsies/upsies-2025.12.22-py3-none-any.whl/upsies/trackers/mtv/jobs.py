"""
Concrete :class:`~.TrackerJobsBase` subclass for MTV
"""

import functools
import re

from ... import errors, jobs, utils
from ...utils.release import ReleaseType
from ..base import TrackerJobsBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class MtvTrackerJobs(TrackerJobsBase):

    @functools.cached_property
    def jobs_before_upload(self):
        # NOTE: Keep in mind that the order of jobs is important for
        #       isolated_jobs: The final job is the overall result, so if
        #       upload_screenshots_job is listed after description_job,
        #       --only-description is going to print the list of uploaded
        #       screenshot URLs.
        return (
            self.login_job,

            # Interactive jobs
            self.playlists_job,
            self.category_job,
            self.imdb_job,
            self.tmdb_job,
            self.scene_check_job,
            self.title_job,

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
        if self.options.get('only_description', False):
            return self.get_job_and_dependencies(self.description_job)
        elif self.options.get('only_title', False):
            return self.get_job_and_dependencies(self.title_job)
        else:
            # Activate all jobs
            return ()

    @functools.cached_property
    def category_job(self):
        return jobs.dialog.ChoiceJob(
            name=self.get_job_name('category'),
            label='Category',
            precondition=self.make_precondition('category_job'),
            autodetect=self.autodetect_category,
            options=[
                (c['label'], c['value'])
                for c in self._categories
            ],
            callbacks={
                'finished': self.handle_category_chosen,
            },
            **self.common_job_args(),
        )

    _categories = (
        {'label': 'HD Season', 'value': '5', 'type': ReleaseType.season},
        {'label': 'HD Episode', 'value': '3', 'type': ReleaseType.episode},
        {'label': 'HD Movie', 'value': '1', 'type': ReleaseType.movie},
        {'label': 'SD Season', 'value': '6', 'type': ReleaseType.season},
        {'label': 'SD Episode', 'value': '4', 'type': ReleaseType.episode},
        {'label': 'SD Movie', 'value': '2', 'type': ReleaseType.movie},
    )

    _category_value_type_map = {
        c['value']: c['type']
        for c in _categories
    }

    def autodetect_category(self, _):
        # "HD" or "SD"
        if utils.mediainfo.video.get_resolution_int(self.content_path) >= 720:
            resolution = 'HD'
        else:
            resolution = 'SD'

        # "Movie", "Episode" or "Season"
        if self.release_name.type is ReleaseType.movie:
            typ = 'Movie'
        elif self.release_name.type is ReleaseType.season:
            typ = 'Season'
        elif self.release_name.type is ReleaseType.episode:
            typ = 'Episode'
        else:
            raise RuntimeError(f'Unsupported type: {self.release_name.type}')

        category = f'{resolution} {typ}'
        _log.debug('Autodetected category: %r', category)
        return category

    @property
    def chosen_release_type(self):
        """
        :class:`~.types.ReleaseType` enum derived from :attr:`category_job` or
        `None` if :attr:`category_job` is not finished yet
        """
        if self.category_job.is_finished:
            choice = self.get_job_attribute(self.category_job, 'choice')
            return self._category_value_type_map.get(choice)

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

    def handle_category_chosen(self, category_job_):
        """
        Update the category wherever it matters so the user only has to correct the category
        once
        """
        new_type = self.chosen_release_type
        if new_type is not None:
            old_type = self.imdb_job.query.type
            _log.debug('Updating release type from %s to %s', old_type, new_type)

            # Update title
            if not self.title_job.is_finished:
                self.release_name.type = new_type
            else:
                _log.debug('Not updating title because title job is already finished')

            # Update IMDb query
            if not self.imdb_job.is_finished:
                self.imdb_job.query.type = new_type
            else:
                _log.debug('Not updating IMDb query because IMDb job is already finished')

            # Update TMDb query
            if not self.tmdb_job.is_finished:
                self.tmdb_job.query.type = new_type
            else:
                _log.debug('Not updating TMDb query because TMDb job is already finished')

    release_name_separator = '.'

    release_name_translation = {
        'edition': {
            re.compile(r"^Director's Cut$"): 'DC',
        },
        'group': {
            re.compile(r'^NOGROUP$'): 'NOGRP',
        },
    }

    @functools.cached_property
    def title_job(self):
        """
        :class:`~.jobs.dialog.TextFieldJob` instance with text set to the
        release title

        Unlike :attr:`~.TrackerJobsBase.release_name_job`, this uses the
        original scene release name for movie and episode scene releases.
        """
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('title'),
            label='Title',
            precondition=self.make_precondition('title_job'),
            prejobs=(
                self.category_job,
                self.scene_check_job,
                self.imdb_job,
                self.tmdb_job,
            ),
            text=self.generate_title,
            validator=self.validate_title,
            **self.common_job_args(),
        )

    async def generate_title(self):
        try:
            if (
                    self.chosen_release_type in (ReleaseType.movie, ReleaseType.episode)
                    and self.scene_check_job.is_scene_release
            ):
                # Use the original scene release name instead of a standardized release name. We
                # rely on scene_check_job making sure that the file/directory name is the correct
                # release name.
                search_results = await utils.predbs.MultiPredbApi().search(self.content_path)
                # We can't rely on finding a search result because the user might have marked this
                # as a scene release manually, (e.g. because no predb has indexed that release
                # (yet)).
                if len(search_results) >= 1:
                    return search_results[0]

            # We're dealing with a non-scene release or season pack and may generate a title.
            # First, we try to get more accurate information from a webdb.
            if self.imdb_id:
                _log.debug('Fetching info from IMDb: %r', self.imdb_id)
                await self.release_name.fetch_info(webdb=self.imdb, webdb_id=self.imdb_id)
            elif self.tmdb_id:
                _log.debug('Fetching info from TMDb: %r', self.tmdb_id)
                await self.release_name.fetch_info(webdb=self.tmdb, webdb_id=self.tmdb_id)
            else:
                _log.debug('Not updating autogenerated title')

        except errors.RequestError as e:
            _log.debug('Fetching title failed: %r', e)

        _log.debug('Updated title: %r', str(self.release_name))
        return str(self.release_name)

    def validate_title(self, text):
        if not text.strip():
            raise ValueError('Title must not be empty.')
        super().validate_release_name(text)

    image_host_config = {
        'common': {'thumb_width': 350},
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
            finish_on_success=True,
            read_only=True,
            hidden=True,
            # Don't cache job output because the number of screenshots can be
            # changed by the user between runs.
            **self.common_job_args(ignore_cache=True),
        )

    document_all_videos = False

    async def generate_description(self):
        sections = []
        section = []
        for info in self.video_info.values():
            section.extend(
                f'[mediainfo]{mediainfo}[/mediainfo]\n'
                for mediainfo in info['mediainfos']
            )

            section.extend(
                f'[quote][code]{bdinfo.quick_summary}[/code][/quote]\n'
                for bdinfo in info['bdinfos']
            )

            if info['screenshot_urls']:
                section.append(
                    '[center]'
                    + utils.bbcode.screenshots_grid(
                        screenshots=info['screenshot_urls'],
                        columns=2,
                        horizontal_spacer='    ',
                        vertical_spacer='\n\n',
                    )
                    + '[/center]'
                )

            sections.append(''.join(section))
            section.clear()

        description = '\n[hr]\n'.join(sections)
        return (
            description
            + (f'\n\n{promo}' if (promo := self.generate_promotion_bbcode()) else '')
        )

    @property
    def post_data_autofill(self):
        return {
            'submit': 'true',
            'MAX_FILE_SIZE': '2097152',
            'fillonly': 'auto fill',
            'category': '0',
            'Resolution': '0',
            'source': '12',
            'origin': '6',
            'title': '',
            'genre_tags': '---',
            'taglist': '',
            'autocomplete_toggle': 'on',
            'image': '',
            'desc': '',
            'fontfont': '-1',
            'fontsize': '-1',
            'groupDesc': '',
            'anonymous': '0',
        }

    @property
    def post_data_upload(self):
        return {
            'submit': 'true',
            'category': self.get_job_attribute(self.category_job, 'choice'),
            'Resolution': '0',
            'source': '12',
            'origin': '6',
            'title': self.get_job_output(self.title_job, slice=0),
            'genre_tags': '---',
            'autocomplete_toggle': 'on',
            'image': '',
            'desc': self.get_job_output(self.description_job, slice=0),
            'fontfont': '-1',
            'fontsize': '-1',
            'groupDesc': self.post_data_group_desc,
            'anonymous': '1' if self.options['anonymous'] else '0',
            'ignoredupes': '1' if self.options['ignore_dupes'] else None,
            # These are probably ignored by the server, but it doesn't cost anything to provide them
            # and maybe eventually someone will pick them up.
            'imdbID': self.imdb_job.selected.get('id', None),
            'tmdbID': self.tmdb_job.selected.get('id', None),
            # 'thetvdbID': ...,
            # 'tvmazeID': ...,
        }

    @property
    def post_data_group_desc(self):
        group_desc = []
        if self.imdb_job.selected:
            group_desc.append(self.imdb_job.selected['url'])
        if self.tmdb_job.selected:
            group_desc.append(self.tmdb_job.selected['url'])

        # Return newline-separated webdb URLs or None.
        if group_desc:
            return '\n'.join(group_desc)
