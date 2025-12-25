"""
Classes and functions that are not specific to
:class:`~.base.PredbApiBase` subclasses
"""

import os
import re

from ... import errors, utils
from ..types import ReleaseType

_abbreviated_scene_filename_regexs = (
    # Match names with group in front
    re.compile(r'^[a-z0-9]+-[a-z0-9_\.-]+?(?!-[a-z]{2,})\.(?:mkv|avi)$'),
    # Match "ttl.720p-group.mkv"
    re.compile(r'^[a-z0-9]+[\.-]\d{3,4}p-[a-z]{2,}\.(?:mkv|avi)$'),
    # Match "GR0UP1080pTTL.mkv"
    re.compile(r'^[a-zA-Z0-9]+\d{3,4}p[a-zA-Z]+\.(?:mkv|avi)$'),
)

def is_abbreviated_filename(filepath):
    """
    Return whether `filepath` points to an abbreviated scene file name
    like ``abd-mother.mkv``
    """
    filename = utils.fs.basename(filepath)
    for regex in _abbreviated_scene_filename_regexs:
        if regex.search(filename):
            return True
    return False

def assert_not_abbreviated_filename(filepath):
    """
    Raise :class:`~.errors.SceneError` if `filepath` points to an
    abbreviated scene file name like ``abd-mother.mkv``
    """
    if is_abbreviated_filename(filepath):
        raise errors.SceneAbbreviatedFilenameError(filepath)


_needed_movie_keys = ('title', 'year', 'resolution', 'edition', 'source', 'video_codec', 'group')
_needed_series_keys = ('title', 'episodes', 'resolution', 'edition', 'source', 'video_codec', 'group')

def get_needed_keys(release_info, exclude=()):
    """
    Return needed :class:`~.release.ReleaseInfo` keys to identify release

    :param release_info: :class:`~.release.ReleaseInfo` instance or any
        :class:`dict`-like object with the keys ``type`` and ``source``
    :param exclude: Sequence of keys to exclude from the returned sequence

    :return: Sequence of required keys or empty sequence if `release_info`
        doesn't contain a ``type``
    """
    if release_info['type'] is ReleaseType.movie:
        needed_keys = _needed_movie_keys
    elif release_info['type'] in (ReleaseType.season, ReleaseType.episode):
        needed_keys = _needed_series_keys
    else:
        # If we don't even know the type, we certainly don't have enough
        # information to pin down a release.
        return ()

    # DVDRips typically don't include resolution in release name
    if release_info['source'] == 'DVDRip':
        needed_keys = list(needed_keys)
        needed_keys.remove('resolution')

    return tuple(k for k in needed_keys if k not in exclude)


def get_season_pack_name(release_name):
    """Remove episode information (e.g. "E03") from `release_name`"""
    # Remove episode(s) from release name to create season pack name
    season_pack = re.sub(
        (
            r'\b'
            rf'(S\d{{2,}})'
            rf'(?:{utils.release.DELIM}*E\d{{2,}})+'
            r'\b'
        ),
        r'\1',
        release_name,
    )

    # Remove episode title
    release_info = utils.release.ReleaseInfo(release_name)
    if release_info['episode_title']:
        # Escape special characters in each word and
        # join words with "space or period" regex
        episode_title_regex = rf'{utils.release.DELIM}+'.join(
            re.escape(word)
            for word in release_info['episode_title'].split()
        )
        season_pack = re.sub(rf'\b{episode_title_regex}\W', '', season_pack)

    return season_pack


def is_mixed_season_pack(directory):
    """
    Return whether `directory` is a season pack with episodes from different
    groups
    """
    if not os.path.isdir(directory):
        return False

    release_info = utils.release.ReleaseInfo(directory)
    if release_info['type'] is not utils.release.ReleaseType.season:
        return False

    groups_found = set()
    for filepath in utils.fs.file_list(directory):
        filepath_info = utils.release.ReleaseInfo(filepath)
        # Ignore files without release group
        if filepath_info['group']:
            groups_found.add(filepath_info['group'])

        # If there are 2 or more different groups, we know enough
        if len(groups_found) >= 2:
            return True

    return False
