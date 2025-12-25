"""
Wrapper for ``mediainfo`` command
"""

import os

from .. import errors, utils
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)


class MediainfoJob(base.JobBase):
    """
    Get output from ``mediainfo`` command

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``generating_report``
            Emitted before mediainfo report generation begins. Registered callbacks get the video
            file path ``mediainfo`` was called with.

        ``generated_report``
            Emitted after mediainfo report generation has finished. Registered callbacks get the
            video file path ``mediainfo`` was called with and the report text.
    """

    name = 'mediainfo'
    label = 'Mediainfo'

    _DEFAULT_FORMAT = '{MEDIAINFO}'

    # Caching is done on a per-file basis in the daemon process.
    cache_id = None

    @property
    def content_path(self):
        """Instantiation argument of the same name"""
        return self._content_path

    def initialize(
            self,
            *,
            content_path,
            from_all_videos=False,
            exclude_files=(),
            format='{MEDIAINFO}',
    ):
        """
        Set internal state

        :param content_path: Path to video file or directory that contains a video file

        :param bool from_all_videos: Whether to get ``mediainfo`` output from each video file or
            only from the first video

        :param exclude_files: Sequence of glob patterns (:class:`str`) and :class:`re.Pattern`
            objects (return value from :func:`re.compile`) that are matched against each relative
            path beneath `content_path`

            Glob patterns are matched case-insensitively.

            .. note:: Non-video files and stuff like `Sample.mkv` are always
                      excluded (see :func:`.fs.find_main_videos`).

        :param format: String that contains the placeholder ``"{MEDIAINFO}"``,
            which is replaced by the actual mediainfo

            Any other placeholders are ignored.
        """
        self._content_path = content_path
        self._from_all_videos = from_all_videos
        self._exclude_files = exclude_files
        self._format = format
        self._reports_by_file = {}
        self._mediainfo_process = None
        self.signal.add('generating_report')
        self.signal.add('generated_report')
        self.signal.register('generated_report', self._store_report_by_file)
        self.signal.register('finished', self._hide_job)

    def _hide_job(self, job):
        # Do not display the mediainfo report as output. It can be very long.
        self.hidden = True

    async def run(self):
        self._mediainfo_process = utils.daemon.DaemonProcess(
            target=_mediainfo_process,
            kwargs={
                'from_all_videos': self._from_all_videos,
                'exclude_files': self._exclude_files,
                'cache_directory': self.cache_directory,
                'ignore_cache': self.ignore_cache,
            },
            info_callback=self._handle_info,
            error_callback=self._handle_error,
        )
        self._mediainfo_process.start()

        if utils.disc.is_disc(self._content_path, multidisc=True):
            await self._process_playlists()
        else:
            await self._process_file_or_directory()

        await self._mediainfo_process.join()
        self._add_mediainfo_reports()

    def terminate(self, reason=None):
        if self._mediainfo_process:
            self._mediainfo_process.stop()
        super().terminate(reason=reason)

    async def _process_playlists(self):
        # Receive selected playlists from PlaylistsJob and pass them on to _mediainfo_process().
        async for _discpath, playlists in self.receive_all('playlists', 'playlists_selected', only_posargs=True):
            _log.debug('Sending playlists to _mediainfo_process(): %r', playlists)
            for playlist in playlists:
                self._mediainfo_process.send(utils.daemon.MsgType.info, {'source': playlist})
        _log.debug('All playlists received')

        # Tell _mediainfo_process() that there won't be any more playlists.
        self._mediainfo_process.send(utils.daemon.MsgType.info, {'source': _ALL_SOURCES_SELECTED})

    async def _process_file_or_directory(self):
        self._mediainfo_process.send(utils.daemon.MsgType.info, {'source': self._content_path})
        self._mediainfo_process.send(utils.daemon.MsgType.info, {'source': _ALL_SOURCES_SELECTED})

    @base.unless_job_is_finished
    def _handle_info(self, info):
        if 'generating_report' in info:
            self.signal.emit('generating_report', info['generating_report'])
        elif 'generated_report' in info:
            self.signal.emit('generated_report', info['video_filepath'], info['generated_report'])
        else:
            raise RuntimeError(f'Unexpected info: {info!r}')

    @base.unless_job_is_finished
    def _handle_error(self, error):
        if isinstance(error, errors.ContentError):
            self.error(error)
        else:
            self.exception(error)

    def _add_mediainfo_reports(self):
        for report in self.reports_by_file.values():
            # We are not using self._format.format(MEDIAINFO=report) because that turns "{" and "}"
            # into special characters that must be escaped, which the user should not expect.
            self.add_output(self._format.replace('{MEDIAINFO}', report))

    def _store_report_by_file(self, video_filepath, mediainfo):
        _log.debug(f'Storing mediainfo report for {video_filepath}')
        self._reports_by_file[video_filepath] = mediainfo

    @property
    def reports_by_file(self):
        """
        Map video file paths to ``mediainfo`` outputs gathered so far

        .. note:: For VIDEO_TS releases, one mediainfo is made for an ``.IFO`` file and a second
                  mediainfo is made for a ``.VOB`` file.
        """
        return self._reports_by_file.copy()


# NOTE: This cannot be the typical `object()` constant because its identity differs between the main
# process and _mediainfo_process() and `... is _ALL_SOURCES_SELECTED` doesn't work as
# expected.
_ALL_SOURCES_SELECTED = '_ALL_SOURCES_SELECTED'

def _mediainfo_process(output_queue, input_queue, *, from_all_videos, exclude_files, cache_directory, ignore_cache):
    # This process reads user-selected video sources from the main process and runs `mediainfo` on
    # them.
    while True:
        source = utils.daemon.read_input_queue_key(input_queue, 'source')
        utils.daemon.maybe_terminate(input_queue)
        if source == _ALL_SOURCES_SELECTED:
            # No more values will be sent on `input_queue`.
            break
        else:
            _send_mediainfo_reports_for_source(
                output_queue=output_queue,
                input_queue=input_queue,
                source=source,
                from_all_videos=from_all_videos,
                exclude_files=exclude_files,
                cache_directory=cache_directory,
                ignore_cache=ignore_cache,
            )


def _send_mediainfo_reports_for_source(
        output_queue, input_queue,
        *, source, from_all_videos, exclude_files, cache_directory, ignore_cache,
):
    for video_filepath in _get_filepaths_for_source(source, from_all_videos, exclude_files):
        utils.daemon.maybe_terminate(input_queue)

        output_queue.put((utils.daemon.MsgType.info, {'generating_report': video_filepath}))
        try:
            mediainfo_report = _get_mediainfo_report(video_filepath, cache_directory, ignore_cache)
        except errors.ContentError as e:
            output_queue.put((utils.daemon.MsgType.error, e))
        else:
            output_queue.put((utils.daemon.MsgType.info, {
                'generated_report': mediainfo_report,
                'video_filepath': video_filepath,
            }))


def _get_mediainfo_report(video_filepath, cache_directory, ignore_cache):
    cache_filepath = _get_cache_filepath(video_filepath, cache_directory)

    if not ignore_cache:
        # Try to read mediainfo from cache file or fail silently.
        try:
            with open(cache_filepath, 'r') as f:
                return f.read()
        except OSError as e:
            msg = e.strerror if e.strerror else str(e)
            _log.debug(f'Failed to read cache file {cache_filepath}: {msg}')

    # Create mediainfo report.
    mediainfo_report = utils.mediainfo.get_mediainfo_report(video_filepath)

    # Write mediainfo report to cache or fail silently.
    try:
        with open(cache_filepath, 'w') as f:
            f.write(mediainfo_report)
    except OSError as e:
        msg = e.strerror if e.strerror else str(e)
        _log.debug(f'Failed to write cache file {cache_filepath}: {msg}')
    finally:
        return mediainfo_report


def _get_cache_filepath(video_filepath, cache_directory):
    return os.path.join(
        cache_directory,
        f'{utils.fs.basename(video_filepath)}.{utils.fs.file_size(video_filepath) or 0}.mediainfo',
    )


def _get_filepaths_for_source(source, from_all_videos, exclude_files):
    if isinstance(source, utils.disc.Playlist):
        if source.type == 'dvd':
            return (
                source.filepath,      # IFO
                source.largest_item,  # VOB
            )
        else:
            return (source.largest_item,)

    elif os.path.isdir(source):
        video_files = utils.fs.find_main_videos(source, exclude=exclude_files)
        if from_all_videos:
            return video_files
        elif video_files:
            return (video_files[0],)
        else:
            return ()

    else:
        # Source is file.
        return (source,)
