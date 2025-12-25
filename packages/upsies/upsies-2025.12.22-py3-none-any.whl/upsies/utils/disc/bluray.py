"""
Get information from "BDMV" directory trees
"""

import os

import pyparsebluray

from ... import utils

import logging  # isort:skip
_log = logging.getLogger(__name__)

natsort = utils.LazyModule(module='natsort', namespace=globals())


def is_bluray(content_path, *, multidisc=False):
    """
    Whether `content_path` contains a "BDMV" subdirectory

    If `multidisc` is truthy, also look for a "BDMV" directory in any subdirectory, but not
    recursively.
    """
    if os.path.isdir(content_path):
        if os.path.isdir(os.path.join(content_path, 'BDMV')):
            return True

        if multidisc:
            for subdir in utils.fs.listdir(content_path):
                if os.path.isdir(os.path.join(content_path, subdir, 'BDMV')):
                    return True

    return False


def get_disc_paths(content_path):
    """
    Return sequence of directory paths beneath `content_path` that contain a "BDMV" directory
    """

    discpaths = []

    # Most likely single-disc release.
    if os.path.isdir(os.path.join(content_path, 'BDMV')):
        discpaths.append(content_path)

    # Find more discs in subdirectories.
    if os.path.isdir(content_path):
        for name in utils.fs.listdir(content_path):
            subpath = os.path.join(content_path, name)
            if is_bluray(subpath):
                discpaths.append(subpath)

    return tuple(natsort.natsorted(discpaths))


def get_playlists(discpath):
    """
    Return sequence of :class:`~.Playlist` instances from BDMV subdirectory

    Return empty sequence if no playlists are found.

    Playlists with a runtime of less than 3 minutes are ignored.

    Each playlist's :attr:`~.Playlist.filepath` is the .MPLS file and the :attr:`~.Playlist.items`
    are .M2TS files.

    :param discpath: Path to directory that contains a "BDMV" subdirectory
    """
    playlist_directory = os.path.join(discpath, 'BDMV', 'PLAYLIST')
    stream_directory = os.path.join(discpath, 'BDMV', 'STREAM')
    if os.path.isdir(playlist_directory) and os.path.isdir(stream_directory):
        # Create Mpls instances and filter out any garbage.
        mplss = _filter_mplss(
            Mpls(mpls_filepath)
            for mpls_filepath in utils.fs.file_list(playlist_directory, extensions=('mpls',))
        )
    else:
        mplss = ()

    def get_duration(mpls):
        # Combined runtime for all playlist items.
        # "Times are expressed in 45 KHz, so you'll need to divide by 45000 to get them in seconds."
        # https://github.com/lw/BluRay/wiki/PlayItem#intime-and-outtime
        duration = 0
        for item in mpls['playlist']['play_items']:
            duration += (item['outtime'] - item['intime']) / 45000
        return duration

    # Create Playlist instances from Mpls instances and filter out any garbage.
    playlists = _filter_playlists(
        utils.disc.Playlist(
            discpath=discpath,
            # Playlist file (.mpls).
            filepath=mpls.filepath,
            # Video file(s) (.m2ts).
            items=tuple(
                os.path.join(
                    stream_directory,
                    item['clip_information_filename'] + '.m2ts',
                )
                for item in mpls['playlist']['play_items']
            ),
            # Combined runtime of all items.
            duration=get_duration(mpls),
        )
        for mpls in mplss
    )

    utils.disc.playlist.mark_main_playlists(playlists)
    return playlists


# This function filters Mpls instances.
def _filter_mplss(mplss):
    def is_empty(mpls):
        # Ignore empty playlists.
        if mpls['playlist']['play_items']:
            return False
        else:
            _log.debug(f'{mpls.filepath}: Mpls is empty: {mpls}')
            return True

    def repeats_clips(mpls):
        # Ignore playlists that repeat the same m2ts.

        def play_item_id(playitem):
            return (playitem['clip_information_filename'], playitem['intime'], playitem['outtime'])

        play_item_ids = tuple(
            play_item_id(play_item)
            for play_item in mpls['playlist']['play_items']
        )
        for play_item_id in play_item_ids:
            if play_item_ids.count(play_item_id) > 2:
                _log.debug(f'{mpls.filepath}: Found repeated play item: {play_item_id}')
                return True
        return False

    return tuple(
        mpls for mpls in mplss
        if (
                not is_empty(mpls)
                and not repeats_clips(mpls)
        )
    )


# This function filters Playlist instances.
def _filter_playlists(playlists):
    def is_too_short(playlist):
        # Ignore playlists with a total runtime of less than 3 minutes.
        if playlist.duration >= 180:
            return False
        else:
            _log.debug(f'{playlist}: Playlist is too short: {playlist.duration}')
            return True

    return tuple(
        playlist for playlist in playlists
        if (
                not is_too_short(playlist)
        )
    )


class Mpls(dict):
    """
    :class:`dict` that reads a Blu-ray ``.mpls`` file

    The provided `filepath` is available as an instance attribute.
    """

    def __init__(self, filepath):
        self.filepath = filepath

        def sanitize(thing):
            if isinstance(thing, pyparsebluray.mpls.movie_playlist.MplsObject):
                thing = vars(thing)

            if isinstance(thing, dict):
                dct = {key: sanitize(value) for key, value in thing.items()}
                del dct['mpls']
                return dct

            elif isinstance(thing, (list, tuple)):
                return tuple(sanitize(value) for value in thing)

            else:
                return thing

        def as_normal_value(mpls_object):
            return sanitize(vars(mpls_object))

        with open(filepath, mode='rb') as fd:
            self['header'] = as_normal_value(pyparsebluray.load_movie_playlist(fd))
            self['appinfo'] = as_normal_value(pyparsebluray.load_app_info_playlist(fd))

            fd.seek(self['header']['playlist_start_address'], os.SEEK_SET)
            self['playlist'] = as_normal_value(pyparsebluray.load_playlist(fd))
