"""
Get information from "BDMV" directory trees
"""

import collections
import os
import re

from ... import utils

natsort = utils.LazyModule(module='natsort', namespace=globals())


def is_dvd(content_path, *, multidisc=False):
    """
    Whether `content_path` contains a "VIDEO_TS" subdirectory

    Also look for "VIDEO_TS.IFO" exists directly in `content_path`.

    If `multidisc` is truthy, also look for a "VIDEO_TS" directory in any subdirectory, but not
    recursively.
    """
    if os.path.isdir(content_path):
        if os.path.isdir(os.path.join(content_path, 'VIDEO_TS')):
            return True

        if os.path.exists(os.path.join(content_path, 'VIDEO_TS.IFO')):
            return True

        if multidisc:
            for subdir in utils.fs.listdir(content_path):
                if os.path.isdir(os.path.join(content_path, subdir, 'VIDEO_TS')):
                    return True

    return False


def get_disc_paths(content_path):
    """
    Return sequence of subdirectories that contain a "VIDEO_TS" directory

    If `content_path` contains a "VIDEO_TS.IFO" file, return `content_path`.

    Return empty sequence by default.
    """
    if os.path.isdir(content_path):
        discpaths = []

        # Most likely single-disc release.
        if os.path.isdir(os.path.join(content_path, 'VIDEO_TS')):
            discpaths.append(content_path)

        # The .VOB files may also be in `content_path` with no "VIDEO_TS" directory.
        if os.path.exists(os.path.join(content_path, 'VIDEO_TS.IFO')):
            discpaths.append(content_path)

        # Find more discs in subdirectories.
        for name in utils.fs.listdir(content_path):
            subpath = os.path.join(content_path, name)
            if name != 'VIDEO_TS' and is_dvd(subpath):
                discpaths.append(subpath)

        return tuple(natsort.natsorted(discpaths))

    return ()


def get_playlists(discpath):
    """
    Return sequence of :class:`~.Playlist` instances from VIDEO_TS subdirectory

    Return empty sequence if no playlists are found.

    Playlists with a runtime of less than 3 minutes are ignored.

    Each playlist represents one Video Title Set, e.g. ``VTS_01_*``, ``VTS_02_*``, ``VTS_03_*``,
    etc. Each playlist's :attr:`.Playlist.filepath` is the .IFO file and the :attr:`.Playlist.items`
    are .VOB files.

    :param discpath: Path to directory that contains a "VIDEO_TS" subdirectory
    """
    video_ts_path = _get_video_ts_directory(discpath)
    if not video_ts_path:
        return ()

    playlists = collections.defaultdict(dict)
    vob_sets = collections.defaultdict(list)
    for filename in utils.fs.listdir(video_ts_path):
        match = re.search(r'^(VTS_\d+)_\d+\.[A-Z]+$', filename)
        if match:
            set_name = match.group(1)
            filepath = os.path.join(video_ts_path, filename)
            file_extension = utils.fs.file_extension(filename).lower()

            if file_extension == 'ifo':
                playlists[set_name]['filepath'] = filepath
                playlists[set_name]['discpath'] = discpath
                playlists[set_name]['duration'] = utils.mediainfo.get_duration_from_mediainfo(filepath)

            elif file_extension == 'vob':
                vob_sets[set_name].append(filepath)

    # Move Video Title Sets to each playlist's `items`.
    for set_name, items in vob_sets.items():
        playlists[set_name]['items'] = tuple(sorted(items))

    # Remove playlist with less than 3 minutes runtime.
    for set_name, playlist in tuple(playlists.items()):
        if playlist['duration'] < 180:
            del playlists[set_name]

    playlists = tuple(
        natsort.natsorted(
            (
                utils.disc.Playlist(**playlist)
                for playlist in playlists.values()
            ),
            key=lambda playlist: playlist.filepath,
        )
    )
    utils.disc.playlist.mark_main_playlists(playlists)
    return playlists


def _get_video_ts_directory(discpath):
    """
    Return the path of the directory that contains the DVD files

    This may be ``<discpath>/VIDEO_TS`` or ``<discpath>``.

    :raise errors.ContentError: if `discpath` does not contain DVD files
    """
    if os.path.isdir(os.path.join(discpath, 'VIDEO_TS')):
        return os.path.join(discpath, 'VIDEO_TS')
    elif os.path.exists(os.path.join(discpath, 'VIDEO_TS.IFO')):
        return discpath
