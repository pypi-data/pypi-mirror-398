"""
Abstract base class for tracker jobs
"""

import abc
import builtins
import collections
import functools
import pathlib
import re

from ... import __homepage__, __project_name__, errors, jobs, uis, utils

import logging  # isort:skip
_log = logging.getLogger(__name__)


class TrackerJobsBase(abc.ABC):
    """
    Base class for tracker-specific :class:`jobs <upsies.jobs.base.JobBase>`

    This base class defines general-purpose jobs that can be used by subclasses
    by returning them in their :attr:`jobs_before_upload` or
    :attr:`jobs_after_upload` attributes. It also provides all objects that are
    needed by any one of those jobs.

    Job instances are provided as :func:`functools.cached_property`, i.e. jobs
    are created only once per session.

    Subclasses that need to run background tasks should pass them to
    :meth:`.JobBase.add_task` or to :meth:`.TrackerBase.attach_task`.
    :meth:`.TrackerBase.attach_task` should only be used if there is no
    appropriate job for the task.

    For a description of the arguments see the corresponding properties.
    """

    def __init__(self, *, content_path, tracker,
                 reuse_torrent_path=None, exclude_files=(),
                 btclient_config=None, torrent_destination=None,
                 screenshots_optimization=None, screenshots_tonemapped=False,
                 image_hosts=None, show_poster=False,
                 options=None, common_job_args=None):
        self._content_path = content_path
        self._tracker = tracker
        self._reuse_torrent_path = reuse_torrent_path
        self._exclude_files = exclude_files
        self._btclient_config = btclient_config
        self._torrent_destination = torrent_destination
        self._screenshots_optimization = screenshots_optimization
        self._screenshots_tonemapped = screenshots_tonemapped
        self._image_hosts = image_hosts
        self._show_poster = show_poster
        self._options = options or {}
        self._common_job_args = common_job_args or {}

    @property
    def content_path(self):
        """
        Content path to generate metadata for

        This is the same object that was passed as initialization argument.
        """
        return self._content_path

    @property
    def tracker(self):
        """
        :class:`~.trackers.base.TrackerBase` subclass

        This is the same object that was passed as initialization argument.
        """
        return self._tracker

    @property
    def reuse_torrent_path(self):
        """
        Path to an existing torrent file that matches :attr:`content_path`

        See :func:`.torrent.create`.
        """
        return self._reuse_torrent_path

    @property
    def torrent_destination(self):
        """
        Where to copy the generated torrent file to or `None`

        This is the same object that was passed as initialization argument.
        """
        return self._torrent_destination

    @property
    def exclude_files(self):
        """
        Sequence of glob and regular expression patterns to exclude from the
        generated torrent

        See the ``exclude_files`` argument of
        :meth:`.CreateTorrentJob.initialize`.

        This should also be used by :attr:`screenshots_job` to avoid making
        screenshots from files that aren't in the torrent.
        """
        return self._exclude_files

    @property
    def options(self):
        """
        Configuration options provided by the user

        This is the same object that was passed as initialization argument.
        """
        return self._options

    @property
    def image_hosts(self):
        """
        Sequence of :class:`~.base.ImagehostBase` instances or `None`

        This is the same object that was passed as initialization argument.
        """
        return self._image_hosts

    @property
    def btclient_config(self):
        """
        :class:`~.btclient.BtclientConfig` instance or `None`

        This is the same object that was passed as initialization argument.
        """
        return self._btclient_config

    @functools.cached_property
    def is_bdmv_release(self):
        """Whether :attr:`content_path` is a Blu-ray release (see :func:`~.is_bluray`)"""
        return utils.disc.is_bluray(self.content_path, multidisc=True)

    @functools.cached_property
    def is_video_ts_release(self):
        """Whether :attr:`content_path` is a DVD release (see :func:`~.is_dvd`)"""
        return utils.disc.is_dvd(self.content_path, multidisc=True)

    @functools.cached_property
    def is_disc_release(self):
        """Whether :attr:`content_path` is a Blu-ray or DVD release (see :func:`~.is_disc`)"""
        return utils.disc.is_disc(self.content_path, multidisc=True)

    def common_job_args(self, **overload):
        """
        Keyword arguments that are passed to all jobs or empty `dict`

        :param overload: Keyword arguments add or replace values from the
            initialization argument
        """
        # Combine global defaults with custom values.
        args = {
            **self._common_job_args,
            **overload,
        }

        # Individual jobs may only set `ignore_cache=False` if
        # `ignore_cache=True` wasn't set globally, e.g. with --ignore-cache.
        if self._common_job_args.get('ignore_cache') or overload.get('ignore_cache'):
            args['ignore_cache'] = True

        return args

    @property
    @abc.abstractmethod
    def jobs_before_upload(self):
        """
        Sequence of jobs that need to finish before :meth:`~.TrackerBase.upload` can
        be called
        """

    @functools.cached_property
    def jobs_after_upload(self):
        """
        Sequence of jobs that are started after :meth:`~.TrackerBase.upload`
        finished

        .. note:: Jobs returned by this class should have
                  :attr:`~.JobBase.autostart` set to `False` or they will be
                  started before submission is attempted.

        By default, this returns :attr:`add_torrent_job` and
        :attr:`copy_torrent_job`.
        """
        return (
            self.logout_job,
            self.add_torrent_job,
            self.copy_torrent_job,
        )

    @property
    def isolated_jobs(self):
        """
        Sequence of job names (e.g. ``"imdb_job"``) that were singled out by the
        user (e.g. with a CLI argument) to create only a subset of the usual
        metadata

        If this sequence is empty, all jobs in :attr:`jobs_before_upload` and
        :attr:`jobs_after_upload` are enabled.
        """
        return ()

    def get_job_and_dependencies(self, *jobs):
        """
        Combine all `jobs` and their dependencies recursively into flat sequence

        :param jobs: :class:`~.JobBase` instances

        Dependencies are gathered from each job's :attr:`~.JobBase.prejobs`.

        .. warning:: This is not a foolproof way to find all dependencies.

                     Jobs may :meth:`~.JobBase.receive_all` signals from :attr:`~.JobBase.siblings`,
                     but only optionally (e.g. :class:`~.AddTorrentJob`), so they don't specify the
                     required siblings as dependencies.

        :return: Sequence of :class:`~.JobBase` instances
        """
        all_jobs = set()

        def add_job(job):
            if job not in all_jobs:
                all_jobs.add(job)

        def add_prejobs(job):
            for prejob in job.prejobs:
                add_job(prejob)
                add_prejobs(prejob)

        for j in jobs:
            add_job(j)
            add_prejobs(j)

        return tuple(all_jobs)

    @property
    def submission_ok(self):
        """
        Whether the created metadata should be submitted

        The base class implementation returns `False` if there are any
        :attr:`isolated_jobs`. Otherwise, it returns `True` only if all
        :attr:`jobs_before_upload` have an :attr:`~.base.JobBase.exit_code` of
        ``0`` or a falsy :attr:`~.base.JobBase.is_enabled` value.

        Subclasses should always call the parent class implementation to ensure
        all metadata was created successfully.
        """
        if self.isolated_jobs:
            # If some jobs are disabled, required metadata is missing and we
            # can't submit
            return False
        else:
            enabled_jobs_before_upload = tuple(
                job for job in self.jobs_before_upload
                if job and job.is_enabled
            )
            enabled_jobs_succeeded = all(
                job.exit_code == 0
                for job in enabled_jobs_before_upload
            )
            return bool(
                enabled_jobs_before_upload
                and enabled_jobs_succeeded
            )

    @functools.cached_property
    def imdb(self):
        """:class:`~.webdbs.imdb.ImdbApi` instance"""
        return utils.webdbs.webdb('imdb')

    @functools.cached_property
    def tmdb(self):
        """:class:`~.webdbs.tmdb.TmdbApi` instance"""
        return utils.webdbs.webdb('tmdb')

    @functools.cached_property
    def tvmaze(self):
        """:class:`~.webdbs.tvmaze.TvmazeApi` instance"""
        return utils.webdbs.webdb('tvmaze')

    def get_job_name(self, name):
        """
        Return job name that is unique for this tracker

        It's important for tracker jobs to have unique names to avoid re-using
        cached output from another tracker's job with the same name.

        Standard jobs have names so that cached output will be re-used by other
        trackers if possible. This function is mainly for unique and custom jobs
        that are only used for one tracker but might share the same name with
        other trackers.
        """
        suffix = f'.{self.tracker.name}'
        if name.endswith(suffix):
            return name
        else:
            return f'{name}{suffix}'

    @functools.cached_property
    def create_torrent_job(self):
        """:class:`~.jobs.torrent.CreateTorrentJob` instance"""
        return jobs.torrent.CreateTorrentJob(
            content_path=self.content_path,
            reuse_torrent_path=self.reuse_torrent_path,
            tracker=self.tracker,
            exclude_files=self.exclude_files,
            precondition=self.make_precondition('create_torrent_job'),
            # If the user didn't specify trackers.<name>.announce_url,
            # TrackerBase.get_announce_url() can try to get it from the tracker website, but we must
            # be logged in first.
            prejobs=(
                ()
                if self.options.get('announce_url') else
                (self.login_job,)
            ),
            **self.common_job_args(),
        )

    @functools.cached_property
    def add_torrent_job(self):
        """:class:`~.jobs.torrent.AddTorrentJob` instance"""
        if self.btclient_config and self.create_torrent_job:
            return jobs.torrent.AddTorrentJob(
                # This job will be started by SubmitJob after successful submission.
                autostart=False,
                precondition=self.make_precondition('add_torrent_job', precondition=self.add_torrent_precondition),
                btclient_config=self.btclient_config,
                download_path=utils.fs.dirname(self.content_path),
                **self.common_job_args(),
            )

    @functools.cached_property
    def copy_torrent_job(self):
        """:class:`~.jobs.torrent.CopyTorrentJob` instance"""
        if self.torrent_destination and self.create_torrent_job:
            return jobs.torrent.CopyTorrentJob(
                # This job will be started by SubmitJob after successful submission.
                autostart=False,
                destination=self.torrent_destination,
                precondition=self.make_precondition('copy_torrent_job', precondition=self.add_torrent_precondition),
                **self.common_job_args(),
            )

    def add_torrent_precondition(self):
        """
        Return whether torrent should be postprocessed locally after submission

        Postprocessing usually includes adding the torrent to a BitTorrent client or copying it to a
        directory.

        For example, a subclass can overload this method if a submission is only a draft.
        """
        return True

    @property
    def torrent_filepath(self):
        """Local path to the torrent file created by :attr:`create_torrent_job`"""
        return self.get_job_output(self.create_torrent_job, slice=0)

    @functools.cached_property
    def subtitles(self):
        """Sequence of :mod:`~.mediainfo.text.Subtitle` objects for :attr:`content_path`"""
        return utils.mediainfo.text.get_subtitles(self.content_path)

    @functools.cached_property
    def release_name(self):
        """
        :class:`~.release.ReleaseName` instance with
        :attr:`release_name_translation` applied
        """
        return utils.release.ReleaseName(
            path=self.content_path,
            translate=self.release_name_translation,
            separator=self.release_name_separator,
            english_title_before_original=self.release_name_english_title_before_original,
        )

    release_name_separator = None
    """See :attr:`.ReleaseName.separator`"""

    release_name_english_title_before_original = False
    """See :attr:`~.utils.release.ReleaseName.english_title_before_original`"""

    release_name_translation = {}
    """See ``translate`` argument of :class:`~.utils.release.ReleaseName`"""

    @functools.cached_property
    def release_name_job(self):
        """
        :class:`~.jobs.dialog.TextFieldJob` instance with text set to
        :attr:`release_name`

        The text is automatically updated when :attr:`imdb_job` sends an ID.
        """
        # NOTE: This job should not use the same cache as the `release-name`
        #       subcommand because a tracker's release_name_job can make
        #       arbitrary customizations.
        return jobs.dialog.TextFieldJob(
            name=self.get_job_name('release-name'),
            label='Release Name',
            callbacks={
                'output': self.release_name.set_release_info,
            },
            precondition=self.make_precondition('release_name_job'),
            validator=self.validate_release_name,
            **self.common_job_args(),
        )

    def validate_release_name(self, text):
        if not text.strip():
            raise ValueError('Release name must not be empty.')

        match = re.search(rf'(?:{utils.release.DELIM}|$)(UNKNOWN_([A-Z_]+))(?:{utils.release.DELIM}|$)', text)
        if match:
            placeholder = match.group(1)
            attribute = match.group(2).replace('_', ' ')
            raise ValueError(f'Replace "{placeholder}" with the proper {attribute.lower()}.')

    async def update_release_name_from(self, webdb, webdb_id):
        """
        Update :attr:`release_name_job` with web DB information

        :param webdb: :class:`~.webdbs.base.WebDbApiBase` instance
        :param webdb_id: ID for `webdb`

        This is a convenience wrapper around :meth:`.ReleaseName.fetch_info` and
        :meth:`.TextFieldJob.fetch_text`.
        """
        if not self.release_name_job.is_finished:
            await self.release_name_job.fetch_text(
                coro=self.release_name.fetch_info(webdb=webdb, webdb_id=webdb_id),
                warn_exceptions=(errors.RequestError,),
                default=str(self.release_name),
            )
            _log.debug('Updated release name: %s', self.release_name)
        else:
            _log.debug('Not updating release name because %r is finished', self.release_name_job)

    @functools.cached_property
    def imdb_job(self):
        """:class:`~.jobs.webdb.WebDbSearchJob` instance"""
        return jobs.webdb.WebDbSearchJob(
            query=self.content_path,
            db=self.imdb,
            autodetect=self.autodetect_imdb_id,
            show_poster=self._show_poster,
            callbacks={
                'output': self._handle_imdb_id,
            },
            precondition=self.make_precondition('imdb_job'),
            **self.common_job_args(),
        )

    async def autodetect_imdb_id(self):
        # Get ID from CLI option or other user-provided source.
        if self.options.get('imdb'):
            _log.debug('Found IMDb ID in CLI: %r', self.options)
            return self.options['imdb']

        # Get ID from video container tag.
        imdb_id = utils.mediainfo.lookup(
            path=self.content_path,
            keys=('General', 0, 'extra', 'IMDB'),
            default=None,
        )
        if imdb_id:
            _log.debug('Found IMDb ID in mediainfo: %r', imdb_id)
            return imdb_id

    def _handle_imdb_id(self, imdb_id):
        # Update other webdb queries with IMDb info
        self.tracker.attach_task(self._propagate_webdb_info(self.imdb, imdb_id))

    @property
    def imdb_id(self):
        """IMDb ID if :attr:`imdb_job` is finished or `None`"""
        return self.imdb_job.selected.get('id', None)

    @functools.cached_property
    def tmdb_job(self):
        """:class:`~.jobs.webdb.WebDbSearchJob` instance"""
        return jobs.webdb.WebDbSearchJob(
            query=self.content_path,
            db=self.tmdb,
            autodetect=self.autodetect_tmdb_id,
            show_poster=self._show_poster,
            callbacks={
                'output': self._handle_tmdb_id,
            },
            precondition=self.make_precondition('tmdb_job'),
            **self.common_job_args(),
        )

    async def autodetect_tmdb_id(self):
        # Get ID from CLI option or other user-provided source.
        if self.options.get('tmdb'):
            _log.debug('Found TMDb ID in CLI: %r', self.options)
            return self.options['tmdb']

        # Get ID from video container tag.
        tmdb_id = utils.mediainfo.lookup(
            path=self.content_path,
            keys=('General', 0, 'extra', 'TMDB'),
            default=None,
        )
        if tmdb_id:
            _log.debug('Found TMDb ID in mediainfo: %r', tmdb_id)
            return tmdb_id

    def _handle_tmdb_id(self, tmdb_id):
        # Do NOT update other webdb queries with TMDb info. TMDb year seems to
        # change based on geolocation and is therefore garbage.
        # self.tracker.attach_task(self._propagate_webdb_info(self.tmdb, tmdb_id))
        pass

    @property
    def tmdb_id(self):
        """TMDb ID if :attr:`tmdb_job` is finished or `None`"""
        return self.tmdb_job.selected.get('id', None)

    @functools.cached_property
    def tvmaze_job(self):
        """:class:`~.jobs.webdb.WebDbSearchJob` instance"""
        return jobs.webdb.WebDbSearchJob(
            query=self.content_path,
            db=self.tvmaze,
            autodetect=self.autodetect_tvmaze_id,
            show_poster=self._show_poster,
            callbacks={
                'output': self._handle_tvmaze_id,
            },
            precondition=self.make_precondition('tvmaze_job'),
            **self.common_job_args(),
        )

    async def autodetect_tvmaze_id(self):
        # Get ID from CLI option or other user-provided source.
        if self.options.get('tvmaze'):
            _log.debug('Found TVmaze ID in CLI: %r', self.options)
            return self.options['tvmaze']

        # Get ID from video container tag.
        tvmaze_id = utils.mediainfo.lookup(
            path=self.content_path,
            keys=('General', 0, 'extra', 'TVMAZE'),
            default=None,
        )
        if tvmaze_id:
            _log.debug('Found TVmaze ID in mediainfo: %r', tvmaze_id)
            return tvmaze_id

    def _handle_tvmaze_id(self, tvmaze_id):
        # Update other webdb queries with TVmaze info
        self.tracker.attach_task(self._propagate_webdb_info(self.tvmaze, tvmaze_id))

    @property
    def tvmaze_id(self):
        """TVmaze ID if :attr:`tvmaze_job` is finished or `None`"""
        return self.tvmaze_job.selected.get('id', None)

    async def _propagate_webdb_info(self, webdb, webdb_id):
        target_webdb_jobs = [
            j for j in (getattr(self, f'{name}_job') for name in utils.webdbs.webdb_names())
            if (
                webdb.name not in j.name
                and j.is_enabled
                and not j.is_finished
            )
        ]

        if target_webdb_jobs:
            title_english = await webdb.title_english(webdb_id)
            title_original = await webdb.title_original(webdb_id)
            query = utils.webdbs.Query(
                type=await webdb.type(webdb_id),
                title=title_english or title_original,
                year=await webdb.year(webdb_id),
            )

            _log.debug('Propagating %s info to other webdbs: %r: %s', webdb.name, [j.name for j in target_webdb_jobs], query)
            for job in target_webdb_jobs:
                job.query.update(query)

        await self.update_release_name_from(webdb, webdb_id)

    @functools.cached_property
    def screenshots_job(self):
        """
        :class:`~.jobs.screenshots.ScreenshotsJob` instance

        The number of screenshots to make is taken the :attr:`screenshots_count`
        attribute.
        """
        return jobs.screenshots.ScreenshotsJob(
            content_path=self.content_path,
            precreated=self.screenshots_precreated,
            exclude_files=self.exclude_files,
            count=self.screenshots_count,
            from_all_videos=self.document_all_videos,
            optimize=self._screenshots_optimization,
            tonemap=self._screenshots_tonemapped,
            precondition=self.make_precondition('screenshots_job'),
            **self.common_job_args(),
        )

    @property
    def screenshots_precreated(self):
        """
        Sequence of user-provided screenshot file paths

        The default implementation uses :attr:`options`\\ ``["screenshots"]``.
        It may be an arbitrarily nested list, which is flattened.
        """
        return utils.flatten_nested_lists(
            self.options.get('screenshots', ())
        )

    @property
    def screenshots_count(self):
        """
        How many screenshots to make

        The default implementation uses :attr:`options`\\ ``["screenshots_count"]``
        with `None` as the default value, which creates a default number of
        screenshots.
        """
        return self.options.get('screenshots_count')

    @property
    def document_all_videos(self):
        """
        Whether to document all videos in the release or just the first/main video

        Documenting means creating screenshots and a Mediainfo or BDInfo report.

        Extras, and samples should never be documented even if this is enabled. (This is tricky and
        may fail sometimes.)

        For movies and episodes, this has no effect. For seasons, this documents each episode. For
        Blu-rays and DVDs, document each playlist that is selected by the user.

        The default is `False`.
        """
        return False

    image_host_config = {}
    """
    Dictionary that maps an image hosting service :attr:`~.ImagehostBase.name` to
    :attr:`~.ImagehostBase.config` values

    ``common`` is a special image host whose values are always applied.

    Values from a specific image hosting service overload ``common`` values.

    Example:

    >>> image_host_config = {
    ...     # Generate 300 pixels wide thumbnails for all image hosts.
    ...     "common": {"thumb_width": 300},
    ...     # Use specific API key for specific image hosting service just for this tracker.
    ...     "myhost": {"apikey": "d34db33f"},
    ... }
    """

    @functools.cached_property
    def upload_screenshots_job(self):
        """:class:`~.jobs.imagehost.ImagehostJob` instance"""
        if self.image_hosts and self.screenshots_job:
            return jobs.imagehost.ImagehostJob(
                imagehosts=self.image_hosts,
                precondition=self.make_precondition('upload_screenshots_job'),
                **self.common_job_args(),
            )

    poster_max_width = 300
    """Maximum poster image width"""

    poster_max_height = 600
    """Maximum poster image height"""

    @functools.cached_property
    def poster_job(self):
        """
        :class:`~.jobs.poster.PosterJob` instance

        See also :meth:`get_poster`, :meth:`get_poster_from_user`,
        and :meth:`get_poster_from_webdb`.
        """
        return jobs.poster.PosterJob(
            precondition=self.make_poster_job_precondition(),
            getter=self.get_poster,
            width=self.poster_max_width,
            height=self.poster_max_height,
            write_to=None,
            imagehosts=self.image_hosts,
            **self.common_job_args(),
        )

    def make_poster_job_precondition(self):
        """
        :attr:`~.JobBase.precondition` for :attr:`poster_job`

        Subclasses may override this method to selectively provide a poster only
        if the server doesn't have one yet.
        """
        return self.make_precondition('poster_job')

    async def get_poster(self):
        """
        Return poster file or URL or `None`

        The default implementation tries to get the poster from the following
        methods and returns the first truthy return value:

            - :meth:`get_poster_from_user`
            - :meth:`get_poster_from_tracker`
            - :meth:`get_poster_from_webdb`

        Besides a file or URL, the return value may also be a dictionary with
        the key ``poster`` and the following optional keys:

            - ``width`` - Resize width in pixels (keep aspeect ratio)
            - ``height`` - Resize height in pixels (keep aspeect ratio)
            - ``write_to`` - Write resized poster to this file
            - ``imagehosts`` - Sequence of :class:`~.ImagehostBase` instances to
              try to upload the poster to

        See :class:`~.PosterJob` for more information.
        """
        poster = await self.get_poster_from_user()
        if poster:
            return poster

        poster = await self.get_poster_from_tracker()
        if poster:
            return poster

        poster = await self.get_poster_from_webdb()
        if poster:
            return poster

    async def get_poster_from_user(self):
        """
        Get poster from user (e.g. CLI argument)

        The default implementation uses :attr:`options`\\ ``["poster"]``.
        """
        return self.options.get('poster', None)

    async def get_poster_from_tracker(self):
        """
        Get poster from tracker or any other custom source

        The default implementation always returns `None`.
        """
        return None

    async def get_poster_from_webdb(self):
        """Return poster URL from :attr:`poster_webdb` or `None`"""
        if self.poster_webdb_job:
            # We can't pass self.poster_webdb_job via `prejobs` to PosterJob because
            # self.poster_webdb_job is determined by checking which webdb job (self.imdb_job,
            # self.tvmaze_job, etc) is contained in self.jobs_before_upload. But
            # self.jobs_before_upload contains self.poster_job, resulting in infinite recursion.
            await self.poster_webdb_job.wait_finished()
            # Because imdb_job.no_id_ok may be True, we have to handle poster_webdb_job.output being
            # empty.
            webdb_id = self.get_job_output(self.poster_webdb_job, slice=0, default=None)
            if webdb_id:
                try:
                    poster_url = await self.poster_webdb.poster_url(
                        webdb_id,
                        season=self.release_name.only_season,
                    )
                except errors.RequestError as e:
                    _log.debug('Failed to get poster from %s: %r', self.poster_webdb, e)
                else:
                    if poster_url:
                        # Resize and reupload poster to configured image host.
                        return {
                            'poster': poster_url,
                            'width': 300,
                            'height': 0,
                            'imagehosts': self.image_hosts,
                            'write_to': None,
                        }

    @functools.cached_property
    def poster_webdb_job(self):
        """
        :class:`~.jobs.base.WebDbSearchJob` instance that is used by
        :meth:`get_poster_from_webdb` to get a poster image or `None` if no
        such instance is enabled and contained in :attr:`jobs_before_upload`
        """
        _webdb, job = self._poster_webdb_and_job
        return job

    @functools.cached_property
    def poster_webdb(self):
        """
        :class:`~.webdbs.base.WebDbApiBase` instance that is used by
        :meth:`get_poster_from_webdb` to get a poster image or `None` if no
        such instance is enabled and contained in :attr:`jobs_before_upload`
        """
        webdb, _job = self._poster_webdb_and_job
        return webdb

    @property
    def _poster_webdb_and_job(self):
        if (
                self.poster_job.is_enabled
                and self.poster_job in self.jobs_before_upload
        ):
            if (
                    self.tvmaze_job.is_enabled
                    and self.tvmaze_job in self.jobs_before_upload
                    and self.release_name.type in (utils.release.ReleaseType.season,
                                                   utils.release.ReleaseType.episode)
            ):
                return self.tvmaze, self.tvmaze_job

            elif (
                    self.imdb_job.is_enabled
                    and self.imdb_job in self.jobs_before_upload
            ):
                return self.imdb, self.imdb_job

            elif (
                    self.tmdb_job.is_enabled
                    and self.tmdb_job in self.jobs_before_upload
            ):
                return self.tmdb, self.tmdb_job

        return None, None

    @functools.cached_property
    def playlists_job(self):
        """:class:`~.jobs.playlists.PlaylistsJob` instance"""
        return jobs.playlists.PlaylistsJob(
            content_path=self.content_path,
            select_multiple=self.document_all_videos,
            precondition=self.make_precondition('playlists_job', precondition=self.playlists_job_precondition),
            **self.common_job_args(),
        )

    def playlists_job_precondition(self):
        return utils.disc.is_disc(self.content_path, multidisc=True)

    @functools.cached_property
    def mediainfo_job(self):
        """:class:`~.jobs.mediainfo.MediainfoJob` instance"""
        return jobs.mediainfo.MediainfoJob(
            content_path=self.content_path,
            from_all_videos=self.document_all_videos,
            exclude_files=self.exclude_files,
            precondition=self.make_precondition('mediainfo_job', precondition=self.mediainfo_job_precondition),
            **self.common_job_args(),
        )

    def mediainfo_job_precondition(self):
        return (
            # Non-BDMV releases always require mediainfo.
            not self.is_bdmv_release
            # BDMV releases require mediainfo based on the specific tracker.
            or self.mediainfo_required_for_bdmv
        )

    mediainfo_required_for_bdmv = False
    """Whether the tracker requires ``mediainfo`` output for BDMV Blu-ray releases"""

    @functools.cached_property
    def bdinfo_job(self):
        """:class:`~.jobs.bdinfo.BdinfoJob` instance"""
        return jobs.bdinfo.BdinfoJob(
            precondition=self.make_precondition('bdinfo_job', precondition=self.bdinfo_job_precondition),
            **self.common_job_args(),
        )

    def bdinfo_job_precondition(self):
        return self.is_bdmv_release

    @functools.cached_property
    def video_info(self):
        """
        Map video file paths to mediainfo/bdinfo reports and screenshot URLs

        Every key in the returned :class:`dict` is a file ID, which is derived from the file path
        from which mediainfo reports, bdinfo reports and/or screenshot URLs were generated.

        Every value in the returned :class:`dict` is a :class:`dict` with the keys ``mediainfos``,
        ``bdinfos`` and ``screenshot_urls``. Each value is a sequence, which may be empty.

        ``mediainfos`` is a sequence of mediainfo reports (:class:`str`), ``bdinfos`` is a sequence
        of :class:`~.BdinfoReport` instances, and ``screenshot_urls`` is a sequence of
        :class:`~.UploadedImage` instances.

        .. note:: We allow multiple reports per video file because VIDEO_TS releases may require one
                  report for the .IFO file and another report for the .VOB file.

        Season example:

        .. code::

            {
              "Foo.S01/Foo.S01E01.mkv": {
                "mediainfos": (
                  "<mediainfo report for Foo.S01E01.mkv>",
                ),
                "bdinfos": (),
                "screenshot_urls": (
                  <UploadeImage for Foo.S01E01.mkv.0:12:09.png>,
                  <UploadeImage for Foo.S01E01.mkv.0:24:12.png>,
                ),
              },
              "Foo.S01/Foo.S01E02.mkv": {
                "mediainfos": (
                  "<mediainfo report for Foo.S01E02.mkv>",
                ),
                "bdinfos": (),
                "screenshot_urls": (
                  <UploadedImage for Foo.S01E02.mkv.0:13:12.png>,
                  <UploadedImage for Foo.S01E02.mkv.0:26:03.png>,
                ),
              },
              ...
            }

        VIDEO_TS example:

        .. code::

            {
              "VIDEO_TS/VTS_03": {
                "mediainfos": (
                  "<mediainfo report for VTS_03_0.IFO>",
                  "<mediainfo report for VTS_03_2.VOB>",
                ),
                "bdinfos": (),
                "screenshot_urls": (
                  <UploadedImage for VTS_03_2.VOB.0:14:58.png>,
                  <UploadedImage for VTS_03_2.VOB.0:26:12.png>,
                ),
              },
              "VIDEO_TS/VTS_06": {
                "mediainfos": (
                  "<mediainfo report for VTS_06_0.IFO>",
                  "<mediainfo report for VTS_06_4.VOB>",
                ),
                "bdinfos": (),
                "screenshot_urls": (
                  <UploadedImage for VTS_06_4.VOB.0:12:53.png>,
                  <UploadedImage for VTS_06_4.VOB.0:29:32.png>,
                ),
              },
              ...
            }

        BDMV example:

        .. code::

            {
              "BDMV/STREAM/00003.mpls": {
                "mediainfos": (),
                "bdinfos": (
                  <BdinfoReport for 00003.mpls>,
                ),
                "screenshot_urls": (
                  <UplaodedImage for 00003.mpls.0:11:27.png>,
                  <UploadedImage for 00003.mpls.0:21:42.png>,
                ),
              },
              ...
            }
        """
        docs = collections.defaultdict(lambda: {
            'mediainfos': [],
            'bdinfos': [],
            'screenshot_urls': [],
        })

        @functools.lru_cache
        def get_video_id(video_path):
            # `video_path` is empty if screenshot was precreated by the user.
            if video_path:
                relative_video_path = self.get_relative_file_path(video_path)
                if self.is_video_ts_release:
                    # Remove enough characters from file name so that the return value is the same
                    # for .IFO and .VOB files for the same playlist. This means mediainfo reports
                    # are grouped by playlist, i.e. VTS_xx_0.IFO is ends up together with
                    # VTS_xx_y.VOB.
                    return re.sub(r'\b(VTS_\d+)_\d+\.(?:IFO|VOB)$', r'\1', relative_video_path)
                return relative_video_path
            return video_path

        # Map each created screenshot to its video file and look up the URL(s) for that screenshot.
        # We want any `precreated_screenshots` at the top, so we have to process screenshots first.
        assert self.upload_screenshots_job.is_finished
        urls_by_file = self.upload_screenshots_job.urls_by_file
        screenshots_by_file = self.screenshots_job.screenshots_by_file
        for video_filepath, screenshot_filepaths in screenshots_by_file.items():
            for screenshot_filepath in screenshot_filepaths:
                uploaded_image = urls_by_file.get(screenshot_filepath, None)
                if uploaded_image:
                    docs[get_video_id(video_filepath)]['screenshot_urls'].append(uploaded_image)

        # Map each created mediainfo report to its video file.
        assert self.mediainfo_job.is_finished or not self.mediainfo_job.is_enabled
        for video_filepath, report in self.mediainfo_job.reports_by_file.items():
            docs[get_video_id(video_filepath)]['mediainfos'].append(report)

        # Map each created mediainfo report to its video file.
        assert self.bdinfo_job.is_finished or not self.bdinfo_job.is_enabled
        for video_filepath, report in self.bdinfo_job.reports_by_file.items():
            docs[get_video_id(video_filepath)]['bdinfos'].append(report)

        # Make sequences immutable.
        for doc in docs.values():
            doc['mediainfos'] = tuple(doc['mediainfos'])
            doc['bdinfos'] = tuple(doc['bdinfos'])
            doc['screenshot_urls'] = tuple(doc['screenshot_urls'])

        return dict(docs)

    @functools.cached_property
    def scene_check_job(self):
        """:class:`~.jobs.scene.SceneCheckJob` instance"""
        common_job_args = self.common_job_args(ignore_cache=True)
        common_job_args['force'] = self.options.get('is_scene')
        return jobs.scene.SceneCheckJob(
            content_path=self.content_path,
            precondition=self.make_precondition('scene_check_job'),
            **common_job_args,
        )

    @functools.cached_property
    def rules_job(self):
        """:class:`~.jobs.rules.RulesJob` instance"""
        return jobs.rules.RulesJob(
            precondition=self.make_precondition('rules_job', precondition=self.rules_job_precondition),
            tracker_jobs=self,
            only_warn=self.options.get('ignore_rules', False),
            **self.common_job_args(),
        )

    def rules_job_precondition(self):
        # No need to start `rules_job` if there are no rules defined.
        return bool(self.tracker.rules)

    @functools.cached_property
    def nfo_job(self):
        """
        :attr:`~.JobBase.hidden` job that reads an ``*.nfo`` file

        The content of the ``*.nfo`` file is available via :attr:`nfo_text` when this job is
        finished.

        This job is mainly required for convenient error handling. You can also call
        :meth:`read_nfo` directly and catch :class:`~.ContentError`.
        """
        return jobs.custom.CustomJob(
            name=self.get_job_name('nfo'),
            label='NFO File',
            precondition=self.make_precondition('nfo_job'),
            worker=self.read_nfo_worker,
            no_output_is_ok=True,
            catch=(
                errors.ContentError,
            ),
            hidden=True,
            **self.common_job_args(ignore_cache=True),
        )

    async def read_nfo_worker(self, job):
        return self.read_nfo()

    @property
    def nfo_text(self):
        """``*.nfo`` file content that was read by :attr:`nfo_job` or `None`"""
        if self.nfo_job.output:
            return self.nfo_job.output[0]

    @functools.cached_property
    def login_job(self):
        """Prompt the user for login credentials if needed and start a user session"""
        return jobs.custom.CustomJob(
            name=self.get_job_name('login'),
            label='Login',
            precondition=self.make_precondition('login_job'),
            worker=self.perform_login,
            no_output_is_ok=True,
            catch=(
                errors.RequestError,
            ),
            **self.common_job_args(ignore_cache=True),
        )

    async def perform_login(self, job):
        async def indicate_activity(func, **kwargs):
            job.indicate_activity(True)
            try:
                return await func(**kwargs)
            finally:
                job.indicate_activity(False)

        # Only display this job while it is running.
        job.hidden = False
        try:
            # Check if we are still logged in via session cookie.
            if not await indicate_activity(self.tracker.still_logged_in):
                login_kwargs = {}
                while True:
                    try:
                        await indicate_activity(self.tracker.login, **login_kwargs)
                    except errors.TfaRequired:
                        login_kwargs['tfa_otp'] = await job.add_prompt(
                            uis.prompts.TextPrompt(question='Enter 2FA one-time password:')
                        )
                    else:
                        break

        finally:
            # Hide job. If an exception was raised, the error message overrides the "hidden" state
            # and it is displayed anyway.
            job.hidden = True

    @functools.cached_property
    def logout_job(self):
        """Terminate a user session started by :attr:`login_job`"""
        return jobs.custom.CustomJob(
            name=self.get_job_name('logout'),
            label='Logout',
            precondition=self.make_precondition('logout_job'),
            worker=self.perform_logout,
            guaranteed=True,
            no_output_is_ok=True,
            catch=(
                errors.RequestError,
            ),
            **self.common_job_args(ignore_cache=True),
        )

    async def perform_logout(self, job):
        # Hide job and wait until submission finished (even on failure).
        job.hidden = True
        await job.wait_for('submit', 'finished')
        job.hidden = False
        try:
            job.indicate_activity(True)
            await self.tracker.logout()
            job.indicate_activity(False)
        finally:
            # Hide job. If an exception was raised, the error message overrides the "hidden" state
            # and it is displayed anyway.
            job.hidden = True

    def make_precondition(self, job_attr, precondition=None):
        """
        Return :attr:`~.base.JobBase.precondition` function for job

        The returned function takes into account :attr:`jobs_before_upload`,
        :attr:`jobs_after_upload` and :attr:`isolated_jobs`.

        :param str job_attr: Name of the job attribute this precondition is for

            By convention, this should be ``"<name>_job"``.

        :param callable precondition: Custom :attr:`~.base.JobBase.precondition`

            `precondition` must be either `None` or return anything truthy for
            the job to get enabled.
        """
        def custom_precondition(precondition=precondition):
            return precondition is None or precondition()

        def precondition():
            job = getattr(self, job_attr)
            if not (
                    job in self.jobs_before_upload
                    or job in self.jobs_after_upload
            ):
                # Subclass doesn't use this job
                return False

            isolated_jobs = self.isolated_jobs
            if isolated_jobs and job in isolated_jobs:
                # Jobs was isolated by user (i.e. other jobs are disabled)
                return custom_precondition()

            if not isolated_jobs:
                # No isolated jobs means all jobs in jobs_before/after_upload are enabled
                return custom_precondition()

            return False

        # Rename precondition function to make debugging more readable
        precondition.__qualname__ = f'{job_attr}_precondition'
        return precondition

    _NO_DEFAULT = object()

    def get_job_output(self, job, slice=None, default=_NO_DEFAULT):
        """
        Helper method for getting output from job

        `job` must be finished.

        :param job: :class:`~.jobs.base.JobBase` instance
        :param slice: :class:`int` to get a specific item from `job`'s output,
            `None` to return all output as a list, or a :class:`slice` object to
            return only one or more items of the output
        :param default: Default value if `job` is not finished or getting
            `slice` from `job`'s output fails.

        :raise RuntimeError: if `job` is not finished or getting `slice` from
            :attr:`~.base.JobBase.output` raises an :class:`IndexError`
        :return: :class:`list` or :class:`str`
        """
        if not job.is_finished:
            if default is not self._NO_DEFAULT:
                return default
            else:
                raise RuntimeError(f'Cannot get output from unfinished job: {job.name}')
        else:
            if slice is None:
                slice = builtins.slice(None, None)
            try:
                return job.output[slice]
            except IndexError as e:
                if default is not self._NO_DEFAULT:
                    return default
                else:
                    raise RuntimeError(f'Job finished with insufficient output: {job.name}: {job.output}') from e

    def get_job_attribute(self, job, attribute, default=_NO_DEFAULT):
        """
        Helper method for getting an attribute from job

        :param job: :class:`~.jobs.base.JobBase` instance
        :param str attribute: Name of attribute to get from `job`
        :param default: Default value if `job` is not finished

        :raise RuntimeError: if `job` is not finished
        :raise AttributeError: if `attribute` is not an attribute of `job`
        """
        if not job.is_finished:
            if default is not self._NO_DEFAULT:
                return default
            else:
                raise RuntimeError(f'Cannot get attribute from unfinished job: {job.name}')
        else:
            return getattr(job, attribute)

    def get_relative_file_path(self, file_path):
        """
        Return `file_path` relative to :attr:`content_path`

        The first path component of the returned path is the last component of :attr:`content_path`.

        :raise ValueError: if `file_path` is not a subpath of :attr:`content_path`
        """
        # Make paths absolute and resolve any symbolic links.
        file_path_abs = pathlib.Path(file_path).resolve()
        content_path_abs = pathlib.Path(self.content_path).resolve()

        try:
            subpath = file_path_abs.relative_to(content_path_abs)
        except ValueError as e:
            raise ValueError(f'{str(file_path_abs)!r} is not a subpath of {str(content_path_abs)!r}') from e
        else:
            # Prepend last component of `content_path` (i.e. the release name) to the relative path.
            return str(content_path_abs.name / subpath)

    def read_nfo(self, *, strip=False):
        """
        Read ``*.nfo`` file

        If no file path is supplied by the user, find ``*.nfo`` file beneath :attr:`content_path`.

        If no ``*.nfo`` file is found, return `None`.

        :param path: Path to NFO file or directory that contains an NFO file or `None` to use
            :attr:`content_path`

        See :func:`.string.read_nfo` for more information.

        :return: if ``*.nfo`` file content or `None` if no ``*.nfo`` file is found
        :raise errors.ContentError: if an ``*.nfo`` file is found but cannot be read
        """
        nfo_filepath = self.options.get('nfo', self.content_path)
        return utils.string.read_nfo(nfo_filepath, strip=strip)

    def generate_promotion_bbcode(self, format='[align=right][size=1]{message}[/size][/align]'):
        """
        Return self promotional BBcode

        If ``only_description`` in :attr:`options` is set, return an empty string.

        :param str format: Template for the returned string

            The placeholder ``{message}`` is replaced with the promotional message.
        """
        if not self.options.get('only_description', False):
            return format.format(message=f'Shared with [url={__homepage__}]{__project_name__}[/url]')
        else:
            return ''
