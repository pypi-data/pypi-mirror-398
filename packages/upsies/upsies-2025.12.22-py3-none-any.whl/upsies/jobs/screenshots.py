"""
Create screenshots from video file(s)
"""

import collections
import inspect
import os

from .. import errors, utils
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)

shutil = utils.LazyModule(module='shutil', namespace=globals())


DEFAULT_NUMBER_OF_SCREENSHOTS = 2


class ScreenshotsJob(base.JobBase):
    r"""
    Create screenshots from video file(s) or :class:`~.Playlist` instances

    To get :class:`~.Playlist`\ s, this job relies on a :class:`~.PlaylistsJob` instance to be
    available via a job :attr:`~.JobBase.siblings` named "playlists".

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``screenshots_total``
            Emitted before screenshots are created. Registered callbacks get the
            total number of screenshots as a positional argument.
    """

    name = 'screenshots'
    label = 'Screenshots'

    # Caching of original/optimized screenshots is handled in the _screenshots/optimize_process()
    # functions based on file names, which we generate and should be unique.
    cache_id = None

    def initialize(self, *, content_path, precreated=(),
                   exclude_files=(), timestamps=(), count=0,
                   from_all_videos=False, optimize='default', tonemap=False):
        r"""
        Set internal state

        :param str content_path: Path to file or directory or sequence of paths

        :param precreated: Sequence of paths of already existing screenshots

            These do not count towards the wanted number of screenshots.
            `count` screenshots are created in addition to any precreated
            screenshots.

        :param exclude_files: Sequence of glob patterns (:class:`str`) and
            :class:`re.Pattern` objects (return value from :func:`re.compile`)
            that are matched against the relative path beneath each `source`

            Glob patterns are matched case-insensitively.

            .. note:: Non-video files and stuff like `Sample.mkv` are always
                      excluded by :func:`.fs.find_main_videos`.

        :param timestamps: Screenshot positions in the video
        :type timestamps: sequence of "[[H+:]M+:]S+" strings or seconds

        :param count: Number of screenshots to make or :func:`callable` that returns how many
            screenshots to make

            If this is a callable (synchronous or asynchronous), it is called when this job is
            :meth:`~.JobBase.start`\ ed, and :attr:`count` is ``0`` until then.

        :param bool from_all_videos: Whether to take `count` screenshots from
            each video file or only from the first video

            See :func:`.fs.find_main_videos` for more information.

        :param optimize: `level` argument for :func:`~image.optimize`

            If this is ``"default"``, missing optimization dependencies are
            silently ignored.

        :param bool tonemap: Whether to apply tonemap algorithm for HDR screenshots

        If `timestamps` and `count` are not given, screenshot positions are
        picked at even intervals. If `count` is larger than the number of
        `timestamps`, more timestamps are added.
        """
        self._content_path = content_path
        self._precreated = precreated
        self._exclude_files = exclude_files
        self._timestamps = timestamps
        if callable(count):
            self._count = 0
            self._count_callable = count
        else:
            self._count = count
            self._count_callable = None
        self._from_all_videos = from_all_videos
        self._optimize = optimize
        self._tonemap = tonemap
        self._screenshots_created = 0
        self._screenshots_total = -1
        self._screenshots_process = None
        self._optimize_process = None
        self._screenshots_by_file = collections.defaultdict(list)
        self.signal.add('screenshots_total', record=True)

    async def run(self):
        """Execute subprocesses for screenshot creation and optimization"""
        # Execute subprocesses
        await self._execute_screenshots_process()
        if self._optimize not in ('none', None):
            self._execute_optimize_process()

        if utils.disc.is_disc(self._content_path, multidisc=True):
            await self._process_playlists()
        else:
            await self._process_file_or_directory()

        # Wait for subprocesses
        await self._screenshots_process.join()
        if self._optimize_process:
            await self._optimize_process.join()

    async def _execute_screenshots_process(self):
        if inspect.iscoroutinefunction(self._count_callable):
            self._count = await self._count_callable()
        elif callable(self._count_callable):
            self._count = self._count_callable()
        _log.debug('Screenshots per video file: %s', self._count)

        self._screenshots_process = utils.daemon.DaemonProcess(
            name='_screenshots_process',
            target=_screenshots_process,
            kwargs={
                'precreated': self._precreated,
                'exclude_files': self._exclude_files,
                'timestamps': self._timestamps,
                'count': self._count,
                'from_all_videos': self._from_all_videos,
                'output_dir': self.cache_directory,
                'overwrite': self.ignore_cache,
                'tonemap': self._tonemap,
            },
            info_callback=self._handle_info,
            error_callback=self._handle_error,
        )
        self._screenshots_process.start()

    def _execute_optimize_process(self):
        self._optimize_process = utils.daemon.DaemonProcess(
            name='_optimize_process',
            target=_optimize_process,
            kwargs={
                'level': self._optimize,
                'overwrite': self.ignore_cache,
                # Ignore missing dependecy if we do "default" optimization
                'ignore_dependency_error': self._optimize == 'default',
                'cache_directory': self.cache_directory,
            },
            info_callback=self._handle_info,
            error_callback=self._handle_error,
        )
        self._optimize_process.start()

    async def _process_playlists(self):
        async for _discpath, playlists in self.receive_all('playlists', 'playlists_selected', only_posargs=True):
            _log.debug('Sending playlists to _screenshots_process(): %r', playlists)
            for playlist in playlists:
                self._screenshots_process.send(utils.daemon.MsgType.info, {'source': playlist})
        self._screenshots_process.send(utils.daemon.MsgType.info, {'source': _ALL_SOURCES_SELECTED})

    async def _process_file_or_directory(self):
        self._screenshots_process.send(utils.daemon.MsgType.info, {'source': self._content_path})
        self._screenshots_process.send(utils.daemon.MsgType.info, {'source': _ALL_SOURCES_SELECTED})

    @base.unless_job_is_finished
    def _handle_info(self, info):
        if 'screenshots_total' in info:
            self._screenshots_total = info['screenshots_total']
            self.signal.emit('screenshots_total', self._screenshots_total)

        elif 'screenshot_filepath' in info:
            if self._optimize_process:
                _log.debug('Screenshot: %s: %.2f KiB',
                           info['screenshot_filepath'],
                           (utils.fs.file_size(info['screenshot_filepath']) or 0) / 1024)
                self._optimize_process.send(utils.daemon.MsgType.info, info)

            else:
                _log.debug('Screenshot: %s: %.2f KiB',
                           info['screenshot_filepath'],
                           (utils.fs.file_size(info['screenshot_filepath']) or 0) / 1024)
                self.add_output(info['screenshot_filepath'], info['video_filepath'], info['source'])

        elif 'optimized_screenshot_filepath' in info:
            _log.debug('Optimized %s: %.2f KiB',
                       info['optimized_screenshot_filepath'],
                       (utils.fs.file_size(info['optimized_screenshot_filepath']) or 0) / 1024)
            self.add_output(info['optimized_screenshot_filepath'], info['video_filepath'], info['source'])

        else:
            raise RuntimeError(f'Unexpected info: {info!r}')

        if self._optimize_process and self.screenshots_created == self.screenshots_total:
            self._optimize_process.stop()

    @base.unless_job_is_finished
    def _handle_error(self, error):
        if (
                isinstance(error, (
                    errors.ScreenshotError,
                    errors.ImageOptimizeError,
                    errors.DependencyError,
                ))
                or not isinstance(error, BaseException)
        ):
            self.error(error)
        else:
            raise error

    def terminate(self, reason=None):
        """
        Stop screenshot creation and optimization subprocesses before
        terminating the job
        """
        if self._screenshots_process:
            self._screenshots_process.stop()
        if self._optimize_process:
            self._optimize_process.stop()
        super().terminate(reason=reason)

    @property
    def exit_code(self):
        """`0` if all screenshots were made, `1` otherwise, `None` if unfinished"""
        if self.is_finished:
            if self.screenshots_total < 0:
                # Job is finished but _screenshots_process() never told us how many screenshots
                # should be created. That means we're either using previously cached output or the
                # job was cancelled while _screenshots_process() was still initializing.
                if self.output:
                    # If we have cached output, assume the cached number of screenshots is what the
                    # user wanted because the output of failed jobs is not cached (see
                    # JobBase._write_cache()).
                    return 0
                else:
                    return 1
            elif len(self.output) == self.screenshots_total:
                return 0
            else:
                return 1

    @property
    def exclude_files(self):
        """
        Sequence of glob and :class:`regex <re.Pattern>` patterns to exclude

        See :meth:`initialize` for more information.

        Setting this property when this job :attr:`~.JobBase.is_started` raises
        :class:`RuntimeError`.
        """
        return self._exclude_files

    @exclude_files.setter
    @base.raise_if_started
    def exclude_files(self, exclude_files):
        self._exclude_files = exclude_files

    @property
    def from_all_videos(self):
        """
        Whether to make screenshots from all video files or only the first

        Setting this property when this job :attr:`~.JobBase.is_started` raises
        :class:`RuntimeError`.
        """
        return self._from_all_videos

    @from_all_videos.setter
    @base.raise_if_started
    def from_all_videos(self, from_all_videos):
        self._from_all_videos = from_all_videos

    @property
    def count(self):
        """
        How many screenshots to make per video file

        Setting this property when this job :attr:`~.JobBase.is_started` raises
        :class:`RuntimeError`.
        """
        return self._count

    @count.setter
    @base.raise_if_started
    def count(self, count):
        self._count = count

    @property
    def timestamps(self):
        """
        Specific list of timestamps to make

        Setting this property when this job :attr:`~.JobBase.is_started` raises
        :class:`RuntimeError`.
        """
        return self._timestamps

    @timestamps.setter
    @base.raise_if_started
    def timestamps(self, timestamps):
        self._timestamps = timestamps

    @property
    def screenshots_total(self):
        """
        Total number of screenshots to make

        .. note:: This is ``-1`` until the subprocess that creates the
                  screenshots is executed and determined the number of
                  screenshots.
        """
        return self._screenshots_total

    @property
    def screenshots_created(self):
        """Total number of screenshots made so far"""
        return self._screenshots_created

    @property
    def screenshots_by_file(self):
        """Map video file paths to sequences of generated screenshot file paths so far"""
        return {
            video_filepath: tuple(screenshot_paths)
            for video_filepath, screenshot_paths in self._screenshots_by_file.items()
        }

    def add_output(self, screenshot_filepath, video_filepath, source):
        """
        Populate :attr:`~.JobBase.output` and :attr:`screenshots_by_file` and bump
        :attr:`screenshots_created`

        :param screenshots_filepath: Path to screenshot file
        :param video_filepath: Path to video file `screenshot_filepath` is from
        :param source: Path to release directory, :class:`~.Playlist` instance or the same as
            `video_filepath`
        """

        def normalize_path(path):
            # Resolve symbolic links and make path absolute.
            return os.path.abspath(os.path.realpath(path))

        # Copy screenshot to home_directory if it is different from cache_directory.
        home_directory = normalize_path(self.home_directory)
        cache_directory = normalize_path(self.cache_directory)
        if home_directory != cache_directory:
            destination_path = self.home_directory or '.'
            try:
                screenshot_filepath = shutil.copy2(screenshot_filepath, destination_path)
            except OSError as e:
                msg = e.strerror if e.strerror else str(e)
                self.error(f'{msg}: {destination_path}')
                return

        # Register successfully created screenshot internally.
        self._screenshots_created += 1
        if isinstance(source, utils.disc.Playlist):
            self._screenshots_by_file[source.filepath].append(screenshot_filepath)
        else:
            self._screenshots_by_file[video_filepath].append(screenshot_filepath)

        return super().add_output(screenshot_filepath)

def _screenshots_process(
        output_queue, input_queue,
        *,
        precreated, exclude_files, timestamps, count,
        from_all_videos, output_dir, overwrite, tonemap,
):
    # First we have to collect all video files we want to create screenshots from. This allows us to
    # report the total number of screenshots.
    screenshot_infos = _get_screenshot_infos(
        input_queue=input_queue,
        custom_timestamps=timestamps,
        count=count,
        exclude_files=exclude_files,
        from_all_videos=from_all_videos,
    )

    # How many screenshots we are going to make. This is used for displaying progress.
    screenshots_total = len(precreated) + len(screenshot_infos)
    output_queue.put((utils.daemon.MsgType.info, {'screenshots_total': screenshots_total}))

    # Feed user-provided, precreated screenshots back into the normal processing pipeline.
    for screenshot_filepath in precreated:
        output_queue.put((utils.daemon.MsgType.info, {
            'screenshot_filepath': screenshot_filepath,
            'video_filepath': '',
            'source': '',
        }))

    try:
        for source, video_filepath, screenshot_filename_base, timestamp in screenshot_infos:
            screenshot_filepath = _make_screenshot(
                video_filepath=video_filepath,
                screenshot_filename_base=screenshot_filename_base,
                timestamp=timestamp,
                output_dir=output_dir,
                overwrite=overwrite,
                tonemap=tonemap,
            )
            output_queue.put((utils.daemon.MsgType.info, {
                'screenshot_filepath': screenshot_filepath,
                'video_filepath': video_filepath,
                'source': source,
            }))
    except errors.ScreenshotError as e:
        output_queue.put((utils.daemon.MsgType.error, e))


_ALL_SOURCES_SELECTED = '_ALL_SOURCES_SELECTED'

def _get_screenshot_infos(input_queue, *, custom_timestamps, count, exclude_files, from_all_videos):
    screenshot_infos = []
    while True:
        source = utils.daemon.read_input_queue_key(input_queue, 'source')
        if source == '_ALL_SOURCES_SELECTED':
            break
        else:
            # Return sequence of tuples where each contains all the information to create one screenshot.
            video_infos = _get_video_infos(source, exclude_files, from_all_videos)

            # We want to create `len(validated_timestamps)` screenshots for each item in `video_infos`.
            for source, video_filepath, screenshot_filename_base in video_infos:
                validated_timestamps = _validate_timestamps(
                    video_filepath=video_filepath,
                    timestamps=custom_timestamps,
                    count=count,
                )
                screenshot_infos.extend(
                    (source, video_filepath, screenshot_filename_base, ts)
                    for ts in validated_timestamps
                )

    return tuple(screenshot_infos)


def _get_video_infos(source, exclude_files, from_all_videos):
    if isinstance(source, utils.disc.Playlist):
        return _get_video_infos_from_playlist(source)
    else:
        return _get_video_infos_from_file_or_directory(source, exclude_files, from_all_videos)


def _get_video_infos_from_playlist(playlist):
    # Include parent directory name.
    screenshot_filename_base = [playlist.discname]

    # Only include the playlist filename for BDMVs. For DVDs, it is implied by the file name of the
    # playlist item.
    if not playlist.filename.startswith('VTS_'):
        screenshot_filename_base.append(utils.fs.strip_extension(playlist.filename))

    # Include file name of playlist item (e.g. 00003.m2ts or VTS_12_1.VOB) without file extension.
    screenshot_filename_base.append(utils.fs.strip_extension(utils.fs.basename(playlist.largest_item)))

    return (
        # (<source>, <video_filepath>, <screenshot_filename_base>)
        (playlist, playlist.largest_item, '.'.join(screenshot_filename_base)),
    )


def _get_video_infos_from_file_or_directory(content_path, exclude_files, from_all_videos):
    video_filepaths = utils.fs.find_main_videos(content_path, exclude_files)
    video_infos = []
    for video_filepath in video_filepaths:
        screenshot_filename_base = utils.fs.strip_extension(utils.fs.basename(video_filepath))
        video_infos.append((content_path, video_filepath, screenshot_filename_base))
        if not from_all_videos:
            break
    return tuple(video_infos)


def _make_screenshot(*, video_filepath, screenshot_filename_base, timestamp, output_dir, overwrite, tonemap):
    screenshot_filepath = os.path.join(
        output_dir,
        screenshot_filename_base + f'.{timestamp}.png',
    )
    if not overwrite and os.path.exists(screenshot_filepath):
        return screenshot_filepath
    else:
        return utils.image.screenshot(
            video_file=video_filepath,
            screenshot_file=screenshot_filepath,
            timestamp=timestamp,
            tonemap=tonemap,
        )


def _validate_timestamps(*, video_filepath, timestamps, count):
    # Validate, normalize, deduplicate and sort timestamps

    duration = utils.mediainfo.get_duration(video_filepath)
    if duration < 1:
        raise errors.ContentError(f'Video duration is too short: {duration}s')

    # Convert timestamp int/float/str to Timestamp and limit its value.
    validated_timestamps = []
    min_ts = utils.types.Timestamp(0)
    max_ts = utils.types.Timestamp(duration)
    for ts in timestamps:
        try:
            ts = max(min_ts, min(max_ts, utils.types.Timestamp(ts)))
        except ValueError as e:
            raise errors.ContentError(e) from e
        else:
            validated_timestamps.append(ts)
    # Deduplicated validated_timestamps.
    validated_timestamps = sorted(set(validated_timestamps))

    if not timestamps and not count:
        count = DEFAULT_NUMBER_OF_SCREENSHOTS

    # Add more timestamps if the user didn't specify less than `count`.
    if count > 0 and len(validated_timestamps) < count:
        # Get position as fraction of video duration for each timestamp:
        # 0.0 = Timestamp(0)
        # 1.0 = Timestamp(duration)
        positions = [ts / duration for ts in sorted(validated_timestamps)]

        # Include start and end of video. They are required for the algorithm below.
        if 0.0 not in positions:
            positions.insert(0, 0.0)
        if 1.0 not in positions:
            positions.append(1.0)

        # Sort positions so they can be paired to find the largest gap.
        positions.sort()

        # Add new positions between the two positions with the largest gap until we have the desired
        # number of screenshots.
        while len(validated_timestamps) < count:
            pairs = zip(positions, positions[1:])
            _max_distance, pos1, pos2 = max((b - a, a, b) for a, b in pairs)
            new_position = ((pos2 - pos1) / 2) + pos1
            validated_timestamps.append(utils.types.Timestamp(int(duration * new_position)))
            positions.append(new_position)
            positions.sort()

    # Return deduplicated, sorted, immutable validated_timestamps.
    return tuple(sorted(set(validated_timestamps)))


def _optimize_process(
        output_queue, input_queue,
        *,
        level, overwrite, ignore_dependency_error, cache_directory,
):
    # Keep reading queued screenshots forever. read_input_queue_until_empty() raises
    # DaemonProcessTerminated if there's a `MsgType.terminate` queued up.
    msgs = []
    while True:
        new_msgs = utils.daemon.read_input_queue_until_empty(input_queue)
        msgs.extend(new_msgs)
        if msgs:
            _typ, info = msgs.pop(0)
            _optimize_screenshot(
                output_queue=output_queue,
                screenshot_filepath=info['screenshot_filepath'],
                video_filepath=info['video_filepath'],
                source=info['source'],
                level=level,
                overwrite=overwrite,
                ignore_dependency_error=ignore_dependency_error,
                cache_directory=cache_directory,
            )


def _optimize_screenshot(
        output_queue,
        *,
        screenshot_filepath, video_filepath, source,
        level, overwrite, ignore_dependency_error, cache_directory,
):
    output_file = utils.fs.ensure_path_in_cache(
        os.path.join(
            utils.fs.dirname(screenshot_filepath),
            (
                utils.fs.basename(utils.fs.strip_extension(screenshot_filepath))
                + '.'
                + f'optimized={level}'
                + '.'
                + utils.fs.file_extension(screenshot_filepath)
            )
        ),
        cache_directory,
    )

    if not overwrite and os.path.exists(output_file):
        output_queue.put((utils.daemon.MsgType.info, {
            'optimized_screenshot_filepath': output_file,
            'video_filepath': video_filepath,
            'source': source,
        }))

    else:
        try:
            optimized_screenshot_filepath = utils.image.optimize(
                screenshot_filepath,
                level=level,
                output_file=output_file,
            )

        except errors.ImageOptimizeError as e:
            output_queue.put((utils.daemon.MsgType.error, e))

        except errors.DependencyError as e:
            if ignore_dependency_error:
                # Act like we optimized `screenshot_filepath`
                output_queue.put((utils.daemon.MsgType.info, {
                    'optimized_screenshot_filepath': screenshot_filepath,
                    'video_filepath': video_filepath,
                    'source': source,
                }))
            else:
                raise e

        else:
            output_queue.put((utils.daemon.MsgType.info, {
                'optimized_screenshot_filepath': optimized_screenshot_filepath,
                'video_filepath': video_filepath,
                'source': source,
            }))
