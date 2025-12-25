"""
Dump frames from video file
"""

import os

from .. import errors, utils

import logging  # isort:skip
_log = logging.getLogger(__name__)


def _ffmpeg_executable():
    if utils.os_family() == 'windows':
        return 'ffmpeg.exe'
    else:
        return 'ffmpeg'


def _is_tonemappable(video_file):
    return any(
        hdr_format.startswith('HDR')
        for hdr_format in utils.mediainfo.video.get_hdr_formats(video_file)
    )


def _make_screenshot_cmd(video_file, timestamp, screenshot_file, tonemap):
    # ffmpeg's "image2" image file muxer uses "%" for string formatting, so we
    # must escape "%" in `video_file`
    screenshot_file = screenshot_file.replace('%', '%%')

    # -vf argument from:
    # https://rendezvois.github.io/video/screenshots/programs-choices/#ffmpeg

    vf = {}

    # Some magic to prevent grey screenshots for some BDMV releases. (Maybe related to VC-1?)
    if (
            utils.disc.is_bluray(video_file)
            or utils.fs.file_extension(video_file).lower() == 'm2ts'
    ):
        vf['fps'] = ('1/60',)

    # Always fix aspect ratio in case video is anamorphic. Doesn't matter if it isn't.
    vf['scale'] = ["'max(sar,1)*iw'", "'max(1/sar,1)*ih'"]

    if utils.mediainfo.video.is_bt2020(video_file):
        vf['scale'].extend((
            'in_h_chr_pos=0',
            'in_v_chr_pos=0',
            'in_color_matrix=bt2020',
        ))

    elif utils.mediainfo.video.is_bt709(video_file):
        vf['scale'].extend((
            'in_h_chr_pos=0',
            'in_v_chr_pos=128',
            'in_color_matrix=bt709',
        ))

    elif utils.mediainfo.video.is_bt601(video_file):
        vf['scale'].extend((
            'in_h_chr_pos=0',
            'in_v_chr_pos=128',
            'in_color_matrix=bt601',
        ))

    vf['scale'].append('flags=' + '+'.join((
        'full_chroma_int',
        'full_chroma_inp',
        'accurate_rnd',
        'spline',
    )))

    vf = ','.join(
        f'{filtername}=' + ':'.join(filtervalue)
        for filtername, filtervalue in vf.items()
    )

    if tonemap and _is_tonemappable(video_file):
        # https://ffmpeg.org/ffmpeg-filters.html#tonemap-1
        vf += ',zscale=t=linear,tonemap=hable,zscale=t=bt709,format=rgb24'

    return (
        _ffmpeg_executable(),
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        '-ss', str(timestamp),
        '-i', f'file:{video_file}',
        '-vf', vf,
        '-pix_fmt', 'rgb24',
        '-vframes', '1',
        f'file:{screenshot_file}',
    )


def screenshot(*, video_file, timestamp, screenshot_file, tonemap):
    """
    Create single screenshot from video file

    :param str video_file: Path to video file
    :param timestamp: Time location in the video
    :type timestamp: :class:`~.Timestamp` (or any :class:`int` or :class:`float`)
    :param str screenshot_file: Path to screenshot file

    .. note:: It is important to use the returned file path because it is passed
              through :func:`~.fs.sanitize_path` to make sure it can exist.

    :raise ScreenshotError: if something goes wrong

    :return: Path to screenshot file
    """
    # See if `video_file` is readable before we do further checks and launch ffmpeg, which will
    # produce a long and unexpected error message.
    try:
        utils.fs.assert_file_readable(video_file)
    except errors.ContentError as e:
        raise errors.ScreenshotError(e) from e

    # Validate timestamp.
    if not isinstance(timestamp, utils.types.Timestamp):
        try:
            timestamp = utils.types.Timestamp(timestamp)
        except (TypeError, ValueError) as e:
            raise errors.ScreenshotError(f'Invalid timestamp: {timestamp!r}') from e

    # Make `screenshot_file` compatible to the file system.
    screenshot_file = utils.fs.sanitize_path(screenshot_file)

    # Add "tonemapped" flag in file name.
    if tonemap and _is_tonemappable(video_file):
        screenshot_file = (
            utils.fs.strip_extension(screenshot_file)
            + '.tonemapped.'
            + utils.fs.file_extension(screenshot_file)
        )

    # Ensure timestamp is within range.
    duration = utils.types.Timestamp(utils.mediainfo.get_duration(video_file))
    if timestamp > duration:
        raise errors.ScreenshotError(f'Timestamp is too close to or after end of video ({duration}): {timestamp}')

    # Make screenshot.
    cmd = _make_screenshot_cmd(video_file, timestamp, screenshot_file, tonemap)
    output = utils.subproc.run(cmd, ignore_errors=True, join_stderr=True)
    if not os.path.exists(screenshot_file):
        import shlex
        raise errors.ScreenshotError(
            f'{video_file}: Failed to create screenshot at {timestamp}: {output}\n'
            + ' '.join(shlex.quote(arg) for arg in cmd)
        )
    else:
        return screenshot_file


def _make_resize_cmd(image_file, dimensions, resized_file):
    # ffmpeg's "image2" image file muxer uses "%" for string formatting
    resized_file = resized_file.replace('%', '%%')
    return (
        _ffmpeg_executable(),
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        '-i', f'file:{image_file}',
        '-vf', f'scale={dimensions}:force_original_aspect_ratio=decrease',
        f'file:{resized_file}',
    )


def resize(image_file, *, width=0, height=0, target_directory=None, target_filename=None, overwrite=False):
    """
    Resize image, preserve aspect ratio

    :param image_file: Path to source image
    :param width: Desired image width in pixels or `0`
    :param height: Desired image height in pixels or `0`
    :param target_directory: Where to put the resized image or `None` to use the
        parent directory of `image_file`
    :param target_filename: File name of resized image or `None` to generate a
        name from `image_file`, `width` and `height`
    :param bool overwrite: Whether to overwrite the resized image file if it
        already exists

    If `width` and `height` are falsy (the default) return `image_file` if
    `target_directory` and `target_filename` are falsy or copy `image_file` to
    the target path.

    .. note:: It is important to use the returned file path because it is passed
              through :func:`~.fs.sanitize_path` to make sure it can exist.

    :raise ImageResizeError: if resizing fails

    :return: Path to resized or copied image
    """
    try:
        utils.fs.assert_file_readable(image_file)
    except errors.ContentError as e:
        raise errors.ImageResizeError(e) from e

    if width and width < 1:
        raise errors.ImageResizeError(f'Width must be greater than zero: {width}')
    elif height and height < 1:
        raise errors.ImageResizeError(f'Height must be greater than zero: {height}')

    dimensions_map = {'width': int(width), 'height': int(height)}
    ext_args = {'minlen': 3, 'maxlen': 4}

    def get_target_filename():
        if target_filename:
            filename = utils.fs.strip_extension(target_filename, **ext_args)
            extension = utils.fs.file_extension(target_filename, **ext_args)
            if not extension:
                extension = utils.fs.file_extension(image_file, **ext_args)
        else:
            filename = utils.fs.basename(utils.fs.strip_extension(image_file, **ext_args))
            dimensions = ','.join(f'{k}={v}' for k, v in dimensions_map.items() if v)
            if dimensions:
                filename += f'.{dimensions}'
            extension = utils.fs.file_extension(image_file, **ext_args)

        if extension:
            filename += f'.{extension}'
        else:
            filename += '.jpg'

        return filename

    def get_target_directory():
        if target_directory:
            return str(target_directory)
        else:
            return utils.fs.dirname(image_file)

    # Assemble full target filepath and make sure it can exist
    target_filepath = utils.fs.sanitize_path(
        os.path.join(get_target_directory(), get_target_filename()),
    )

    if not overwrite and os.path.exists(target_filepath):
        _log.debug('Already resized: %r', target_filepath)
        return target_filepath

    if not width and not height:
        # Nothing to resize
        if target_filepath != str(image_file):
            # Copy image_file to target_filepath
            try:
                utils.fs.mkdir(utils.fs.dirname(target_filepath))
            except errors.ContentError as e:
                raise errors.ImageResizeError(e) from e

            import shutil
            try:
                return str(shutil.copy2(image_file, target_filepath))
            except OSError as e:
                msg = e.strerror if e.strerror else str(e)
                raise errors.ImageResizeError(
                    f'Failed to copy {image_file} to {target_filepath}: {msg}'
                ) from e
        else:
            # Nothing to copy
            return str(image_file)

    ffmpeg_params = ':'.join(
        f'{k[0]}={v if v else -1}'
        for k, v in dimensions_map.items()
    )
    cmd = _make_resize_cmd(image_file, ffmpeg_params, target_filepath)
    output = utils.subproc.run(cmd, ignore_errors=True, join_stderr=True)
    if not os.path.exists(target_filepath):
        error = output or 'Unknown reason'
        raise errors.ImageResizeError(f'Failed to resize: {error}')
    else:
        return str(target_filepath)


# NOTE: Most of the optimization is achieved at level 1 with ~40 % smaller
#       files. Anything higher seems to only reduce by tens of kB or less.
_optimization_levels = {
    'low': '1',
    'medium': '2',
    'high': '4',
    'placebo': 'max',
}

optimization_levels = (*tuple(_optimization_levels), 'none', 'default')
"""Valid `level` arguments for :func:`optimize`"""


def optimize(image_file, output_file=None, level=None):
    """
    Optimize PNG image size

    :path image_file: Path to PNG File
    :path output_file: Path to optimized `image_file` or any falsy value to
        overwrite `image_file`
    :path str,int level: Optimiziation level (``"low"``, ``"medium"``,
        ``"high"``) or ``"default"`` to use recommended level or ``"none"`` /
        `None` to not do any optimization

    If the optimization fails and `image_file` does not end with ".png", it is assumed that it is
    not a PNG and the original file is returned unoptimized.

    :return: path to optimized PNG file
    :raise ImageOptimizeError: if the optimization fails
    """
    if level not in ('none', None):
        if level == 'default':
            level = 'medium'

        try:
            opt = _optimization_levels[str(level)]
        except KeyError as e:
            raise errors.ImageOptimizeError(f'Invalid optimization level: {level}') from e

        cmd = [
            'oxipng', '--preserve',
            '--opt', opt,
            '--interlace', '0',  # Remove any interlacing
            '--strip', 'safe',   # Remove irrelevant metadata
            str(image_file),
        ]

        if output_file:
            sanitized_output_file = utils.fs.sanitize_path(output_file)
            cmd.extend(('--out', sanitized_output_file))
            return_value = sanitized_output_file
        else:
            return_value = image_file

        # oxipng prints errors AND info messages to stderr, so we can't use output on stderr as an
        # indicator of failure. Instead, we check if the output file exists
        error_message, exitcode = utils.subproc.run(cmd, join_stderr=True, return_exitcode=True)
        error_message = error_message.strip()
        if exitcode == 0:
            return return_value
        elif utils.fs.file_extension(image_file).lower() == 'png':
            if error_message:
                raise errors.ImageOptimizeError(f'Failed to optimize: {error_message}')
            else:
                raise errors.ImageOptimizeError('Failed to optimize for unknown reason')
        else:
            # This is probably not a PNG and we can just fail silently and return the
            # unoptimized original.
            return image_file


def get_mime_type(image_file):
    """Return MIME type of `image_file` or `None` if it cannot be determined"""
    tracks = utils.mediainfo.get_tracks(image_file, default={})
    try:
        return tracks['General'][0]['InternetMediaType']
    except (KeyError, IndexError):
        return None


def convert(image_file, *, mime_type, output_file):
    """
    Convert image

    :param str image_file: Path to image
    :param str mime_type: Target MIME type to convert `image_file` to (e.g. "image/png")
    :param str output_file: Where to write the converted image to

    :raise ImageConvertError: if the conversion failed

    :return: Sanitized `output_file` (via :meth:`~.utils.fs.sanitize_path`)
    """
    sanitized_output_file = utils.fs.sanitize_path(output_file)
    cmd = ('ffmpeg', '-y', '-i', image_file, sanitized_output_file)
    error_message, exit_code = utils.subproc.run(cmd, join_stderr=True, return_exitcode=True)
    if exit_code != 0:
        raise errors.ImageConvertError(f'Failed to convert to {mime_type}: {image_file}: {error_message}')
    elif not os.path.exists(sanitized_output_file):
        raise errors.ImageConvertError(f'Failed to convert to {mime_type}: {image_file}')
    else:
        return sanitized_output_file
