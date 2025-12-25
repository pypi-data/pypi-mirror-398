import functools
import re

from ... import errors, utils

import logging  # isort:skip
_log = logging.getLogger(__name__)

NO_DEFAULT_VALUE = object()


@functools.cache
def get_width(path, *, dar=True, default=NO_DEFAULT_VALUE):
    """
    Return displayed width of video file `path`

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param bool dar: Return display aspect ratio instead of storage aspect ratio

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if width can't be determined
    """
    try:
        width = utils.mediainfo.lookup(path, ('Video', 'DEFAULT', 'Width'), type=int)
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        par = utils.mediainfo.lookup(path, ('Video', 'DEFAULT', 'PixelAspectRatio'), type=float, default=1.0)
        if dar and par > 1.0:
            _log.debug('Display width: %r * %r = %r', width, par, width * par)
            width = int(width * par)
        return width


@functools.cache
def get_height(path, *, dar=True, default=NO_DEFAULT_VALUE):
    """
    Return displayed height of video file `path`

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param bool dar: Return display aspect ratio instead of storage aspect ratio

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if height can't be determined
    """
    try:
        height = utils.mediainfo.lookup(path, ('Video', 'DEFAULT', 'Height'), type=int)
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        par = utils.mediainfo.lookup(path, ('Video', 'DEFAULT', 'PixelAspectRatio'), type=float, default=1.0)
        if dar and par < 1.0:
            _log.debug('Display height: (1 / %r) * %r = %r', par, height, (1 / par) * height)
            height = int((1 / par) * height)
        return height


def get_resolution(path, default=NO_DEFAULT_VALUE):
    """
    Return resolution and scan type of video file `path` as :class:`str` (e.g. "1080p")

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if resolution can't be determined
    """
    try:
        resolution = get_resolution_int(path)
        scan_type = get_scan_type(path)
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        return f'{resolution}{scan_type}'


# Normal widths and heights for normal aspect ratios.
std_resolutions = {
    4 / 3: {
        480: (640, 480),
        576: (768, 576),
        720: (960, 720),
        1080: (1440, 1080),
        2160: (2880, 2160),
        4320: (7680, 4320),
    },
    16 / 9: {
        480: (854, 480),
        576: (1024, 576),
        720: (1280, 720),
        1080: (1920, 1080),
        2160: (3840, 2160),
        4320: (7680, 4320),
    },
    21 / 9: {
        # Height must shrink because width cannot grow.
        480: (854, 366),
        576: (1024, 439),
        720: (1280, 549),
        1080: (1920, 823),
        2160: (3840, 1646),
        4320: (7680, 3292),
    },
}

# Maximum widths and heights for any aspect ratio.
max_resolutions = {
    480: (854, 480),
    576: (1024, 576),
    720: (1280, 720),
    1080: (1920, 1080),
    2160: (3840, 2160),
    4320: (7680, 4320),
}

@functools.cache
def get_resolution_int(path, default=NO_DEFAULT_VALUE):
    """
    Return resolution of video file `path` as :class:`int` (e.g. ``1080``)

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if resolution can't be determined
    """
    try:
        sar_width = get_width(path, dar=False)
        sar_height = get_height(path, dar=False)
        dar_width = get_width(path, dar=True)
        dar_height = get_height(path, dar=True)
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        aspect_ratio = dar_width / dar_height
        closest_aspect_ratio = utils.closest_number(aspect_ratio, std_resolutions)
        is_anamorphic = sar_width != dar_width or sar_height != dar_height
        _log.debug('sar_width=%r, sar_height=%r, dar_width=%r, dar_height=%r, aspect_ratio=%.3f->%.3f, is_anamorphic=%r',
                   sar_width, sar_height, dar_width, dar_height, aspect_ratio, closest_aspect_ratio, is_anamorphic)

        # Some resolutions are in the middle between two resolutions. For example, 1480x620 is
        # conventionally labeled as 720p even though it is too big.
        height_distances = {}

        for resolution, (max_width, max_height) in sorted(max_resolutions.items()):
            std_width, std_height = std_resolutions[closest_aspect_ratio][resolution]
            _log.debug('%4d: %dx%d (max: %dx%d)', resolution, std_width, std_height, max_width, max_height)

            # Find width/height distance to normal width/height for the closest standard aspect ratio.
            width_distance_from_std_aspect_ratio = sar_width - std_width
            _log.debug(f'  {width_distance_from_std_aspect_ratio=}: {sar_width} - {std_width}')
            height_distance_from_std_aspect_ratio = sar_height - std_height
            _log.debug(f'  {height_distance_from_std_aspect_ratio=}: {sar_height} - {std_height}')
            height_distances[abs(height_distance_from_std_aspect_ratio)] = resolution

            # Check if width/height is smaller than the maximum for this resolution.
            is_within_bounds = sar_width <= max_width and sar_height <= max_height
            _log.debug(f'  {is_within_bounds=}: {sar_width} <= {max_width} and {sar_height} <= {max_height}')

            # Check if width is too far away from the standard width.
            if is_anamorphic:
                is_reasonably_close = True
            else:
                is_reasonably_close = abs(width_distance_from_std_aspect_ratio) < std_width * 0.06
                _log.debug(
                    f'  {is_reasonably_close=}: '
                    f'abs({width_distance_from_std_aspect_ratio}) < ({std_width} * 0.06 = {std_width * 0.06:.0f})'
                )

            if is_within_bounds and is_reasonably_close:
                _log.debug('      Resolution is close enough')
                return resolution

        height_distances_sorted = sorted(height_distances.items())
        _log.debug('Picking closest resolution by normal height for %.3f: %r', closest_aspect_ratio, height_distances_sorted)
        return height_distances_sorted[0][1]


def get_scan_type(path):
    """
    Return scan type of video file `path` ("i" for interlaced, "p" for progressive)

    This always defaults to "p" if it cannot be determined.

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :raise ContentError: if scan type can't be determined
    """
    scan_type = utils.mediainfo.lookup(path, ('Video', 'DEFAULT', 'ScanType'), default='p').lower()
    if scan_type in ('interlaced', 'mbaff', 'paff'):
        return 'i'
    else:
        return 'p'


def get_frame_rate(path, default=NO_DEFAULT_VALUE):
    """
    Return frames per second of default video track as :class:`float`

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    return utils.mediainfo.lookup(
        path=path,
        keys=('Video', 'DEFAULT', 'FrameRate'),
        default=default,
        type=float,
    )


def get_bit_depth(path, default=NO_DEFAULT_VALUE):
    """
    Return bit depth of default video track (e.g. ``8`` or ``10``)

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    return utils.mediainfo.lookup(
        path=path,
        keys=('Video', 'DEFAULT', 'BitDepth'),
        default=default,
        type=int,
    )


known_hdr_formats = {
    'DV',
    'HDR10+',
    'HDR10',
    'HDR',
}
"""Set of valid HDR format names"""

def get_hdr_formats(path, default=NO_DEFAULT_VALUE):
    """
    Return sequence of HDR formats e.g. ``("HDR10",)``, ``("DV", "HDR10")``

    The sequence may be empty.

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    def is_dv(video_track):
        return bool(
            # Dolby Vision[ / <more information>]
            re.search(r'^Dolby Vision', video_track.get('HDR_Format', ''))
        )

    def is_hdr10p(video_track):
        return bool(
            # "HDR10+ Profile A" or "HDR10+ Profile B"
            re.search(r'HDR10\+', video_track.get('HDR_Format_Compatibility', ''))
        )

    def is_hdr10(video_track):
        return bool(
            (
                re.search(r'HDR10(?!\+)', video_track.get('HDR_Format_Compatibility', ''))
                or
                re.search(r'BT\.2020', video_track.get('colour_primaries', ''))
            )
            and not re.search(r'dvhe\.05', video_track.get('HDR_Format_Profile', ''))
        )

    def is_hdr(video_track):
        return bool(
            re.search(r'HDR(?!10)', video_track.get('HDR_Format_Compatibility', ''))
            or
            re.search(r'HDR(?!10)', video_track.get('HDR_Format', ''))
        )

    try:
        video_track = utils.mediainfo.lookup(path, ('Video', 'DEFAULT'))
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        hdr_formats = []

        # NOTE: DV and HDR(10)(+) can co-exist.
        if is_dv(video_track):
            hdr_formats.append('DV')

        if is_hdr10p(video_track):
            hdr_formats.append('HDR10+')
        elif is_hdr10(video_track):
            hdr_formats.append('HDR10')
        elif is_hdr(video_track):
            hdr_formats.append('HDR')

        return tuple(hdr_formats)


def is_bt601(path, default=NO_DEFAULT_VALUE):
    """
    Whether `path` is BT.601 (~SD) video

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    try:
        if (
                _is_color_matrix(path, 'BT.601')
                or _is_color_matrix(path, 'BT.470 System B/G')
        ):
            return True
        else:
            # Assume BT.601 if default video is SD.
            # https://rendezvois.github.io/video/screenshots/programs-choices/#color-matrix
            resolution = get_resolution_int(path)
            return resolution < 720
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default

def is_bt709(path, default=NO_DEFAULT_VALUE):
    """
    Whether `path` is BT.709 (~UHD) video

    See :func:`is_bt601`.
    """
    return _is_color_matrix(path, 'BT.709', default=default)

def is_bt2020(path, default=NO_DEFAULT_VALUE):
    """
    Whether `path` is BT.2020 (~UHD) video

    See :func:`is_bt601`.
    """
    return _is_color_matrix(path, 'BT.2020', default=default)

def _is_color_matrix(path, matrix, default=NO_DEFAULT_VALUE):
    def normalize_matrix(matrix):
        # Remove whitespace and convert to lower case.
        return ''.join(matrix.casefold().split())

    matrix = normalize_matrix(matrix)

    try:
        video_tracks = utils.mediainfo.lookup(path, ('Video',))
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        # https://rendezvois.github.io/video/screenshots/programs-choices/#color-matrix
        for track in video_tracks:
            if normalize_matrix(track.get('matrix_coefficients', '')).startswith(matrix):
                return True
        return False


_video_translations = (
    ('x264', {'Encoded_Library_Name': re.compile(r'^x264$')}),
    ('x265', {'Encoded_Library_Name': re.compile(r'^x265$')}),
    ('XviD', {'Encoded_Library_Name': re.compile(r'^XviD$')}),
    ('DivX', {'Encoded_Library_Name': re.compile(r'^DivX$')}),
    ('H.264', {'Format': re.compile(r'^AVC$')}),
    ('H.265', {'Format': re.compile(r'^HEVC$')}),
    ('VP9', {'Format': re.compile(r'^VP9$')}),
    ('VC-1', {'Format': re.compile(r'^VC-1$')}),
    ('MPEG-4', {'Format': re.compile(r'^MPEG-4')}),
    ('MPEG-2', {'Format': re.compile(r'^MPEG Video$')}),
)

@functools.cache
def get_video_format(path, default=NO_DEFAULT_VALUE):
    """
    Return video format of default video track

    Return x264, x265 or XviD if either one is detected.

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist or video format cannot be determined, raise
        :exc:`~.ContentError` if not provided

    :raise ContentError: if anything goes wrong
    """
    try:
        video_track = utils.mediainfo.lookup(path, ('Video', 'DEFAULT'))
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        for vfmt, regexs in _video_translations:
            for key, regex in regexs.items():
                value = video_track.get(key)
                if value and regex.search(value):
                    _log.debug('Detected video format: %s', vfmt)
                    return vfmt

        if default is NO_DEFAULT_VALUE:
            raise errors.ContentError('Unable to detect video format')
        else:
            _log.debug('Failed to detect video format, falling back to default: %s', default)
            return default
