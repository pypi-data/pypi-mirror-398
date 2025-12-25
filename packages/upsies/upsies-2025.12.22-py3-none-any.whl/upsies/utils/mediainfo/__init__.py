import collections
import functools
import json
import os
import re

from ... import errors, utils
from . import audio, text, video

import logging  # isort:skip
_log = logging.getLogger(__name__)

NO_DEFAULT_VALUE = object()

if utils.os_family() == 'windows':
    _mediainfo_executable = 'mediainfo.exe'
    _ffprobe_executable = 'ffprobe.exe'
else:
    _mediainfo_executable = 'mediainfo'
    _ffprobe_executable = 'ffprobe'


@functools.cache
def _run_mediainfo(path, *args):
    if os.path.isdir(path):
        video_path = utils.fs.find_main_video(path)
    else:
        video_path = path

    # It's easier to check for readability than to interpret error output from mediainfo.
    utils.fs.assert_file_readable(video_path)
    cmd = (_mediainfo_executable, video_path, *args)

    # Translate DependencyError to ContentError so callers have to expect less exceptions. Do not
    # catch ProcessError because things like wrong mediainfo arguments are bugs.
    try:
        return utils.subproc.run(cmd)
    except errors.DependencyError as e:
        raise errors.ContentError(e) from e


def get_mediainfo_report(path):
    """
    ``mediainfo`` output as a string

    The parent directory of `path` is redacted.

    :param str path: Path to video file or directory

        For directories, the return value of :func:`find_main_video` is used.

    :raise ContentError: if anything goes wrong
    """
    def remove_parent_directory(mi, parent_directory=utils.fs.dirname(path)):
        # Remove parent directory, but only if it's not empty.
        if parent_directory:
            return mi.replace(parent_directory + os.sep, '')
        else:
            return mi

    def ensure_unique_id_exists(mi):
        # Some old files don't contain a unique ID and some mediainfo parsers cannot deal with that,
        # so we default to a fake "Unique ID" field.
        unique_id_regex = re.compile(r'^Unique ID\s*:\s*\d+', flags=re.MULTILINE)
        unique_id_default = 'Unique ID                                : 0 (0x0)'
        if unique_id_regex.search(mi):
            return mi
        else:
            assert mi.startswith('General\n')
            return (
                mi[:len('General\n')]
                + unique_id_default + '\n'
                + mi[len('General\n'):]
            )

    report = _run_mediainfo(path)
    return remove_parent_directory(ensure_unique_id_exists(report))


def get_tracks(path, default=NO_DEFAULT_VALUE):
    """
    ``mediainfo --Output=JSON`` as dictionary that maps each track's ``@type`` to a list of
    track dictionaries

    :param str path: Path to video file or directory

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    if default is not NO_DEFAULT_VALUE and not os.path.exists(path):
        return default

    # --full adds "internal tags" (e.g. "InternetMediaType", which seems to be the MIME type).
    stdout = _run_mediainfo(path, '--Output=JSON', '--full')
    tracks = {}
    try:
        for track in json.loads(stdout)['media']['track']:
            if track['@type'] not in tracks:
                tracks[track['@type']] = []
            tracks[track['@type']].append(track)
    except (ValueError, TypeError) as e:
        raise RuntimeError(f'{path}: Unexpected mediainfo output: {stdout}: {e}') from e
    except KeyError as e:
        raise RuntimeError(f'{path}: Unexpected mediainfo output: {stdout}: Missing field: {e}') from e
    else:
        return tracks


def _get_default_track(tracks):
    # Find first track that is marked as default.
    for track in tracks:
        if track.get('Default') == 'Yes':
            return track

    # Default to first track.
    return tracks[0]


def lookup(path, keys, type=None, default=NO_DEFAULT_VALUE):
    """
    Return nested value from :func:`get_tracks`

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param keys: Iterable of nested keys/indexes in the return value of :func:`get_tracks`

    :param type: Callable that takes a :class:`str` value from the tracks returned by
        :func:`get_tracks` and returns a desired type (e.g. :class:`int`)

    :param default: Return value if `path` doesn't exist, raise :exc:`ValueError` if not provided

    For example, `("Audio", 0, "Language")` returns the language of the first audio track. If no
    language is defined return `default` or raise :exc:`~.ContentError` if `default` is not
    provided.

    In lists, instead of an index, you can use ``"DEFAULT"`` to find the default track in that list,
    e.g. `("Audio", "DEFAULT", "Language")` returns the language of the default audio track. The
    default track is either marked specifically as such in the container or, if no track is marked,
    the first track is used.

    Any exception from `type` will bubble up and must be caught by the caller.

    :raise ContentError: if `path` does not exist or if `keys` does not resolve to a value and
        `default` is not provided.
    """
    try:
        initial_value = value = get_tracks(path)
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        try:
            for key in keys:
                if isinstance(value, collections.abc.Mapping):
                    value = value[key]

                elif isinstance(value, collections.abc.Sequence) and not isinstance(value, str):
                    if key == 'DEFAULT':
                        value = _get_default_track(value)
                    else:
                        value = value[key]

                else:
                    value = default

        except (KeyError, IndexError, TypeError):
            value = default

        if value is NO_DEFAULT_VALUE:
            raise errors.ContentError(f'Unable to lookup {keys!r} in {initial_value!r}')
        elif type is not None:
            return type(value)
        else:
            return value


def get_duration(path, default=NO_DEFAULT_VALUE):
    """
    Return video duration in seconds (float)

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    try:
        return get_duration_from_ffprobe(path, default=default)
    except (errors.DependencyError, errors.ProcessError):
        return get_duration_from_mediainfo(path, default=default)


def get_duration_from_ffprobe(path, default=NO_DEFAULT_VALUE):
    """
    Return video duration in seconds (float) from ``ffprobe``

    :param str path: Path to video file or directory

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    if default is not NO_DEFAULT_VALUE and not os.path.exists(path):
        return default

    main_video = utils.fs.find_main_video(path)
    cmd = (
        _ffprobe_executable,
        '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        f'file:{main_video}',
    )
    length = utils.subproc.run(cmd, ignore_errors=True)
    try:
        return float(length.strip())
    except ValueError as e:
        raise RuntimeError(f'Unexpected output from {cmd}: {length!r}') from e


def get_duration_from_mediainfo(path, default=NO_DEFAULT_VALUE):
    """
    Return video duration in seconds (float) from ``mediainfo``

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    try:
        all_tracks = get_tracks(path)
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        try:
            return float(all_tracks['General'][0]['Duration'])
        except (KeyError, IndexError, ValueError, TypeError) as e:
            raise RuntimeError(f'Unexpected tracks from {path}: {all_tracks!r}') from e
