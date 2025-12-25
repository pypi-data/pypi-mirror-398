"""
Normalized representation of a sequence of :mod:`~.disc.bluray` or :mod:`~.disc.dvd` video files
"""

import functools

from ... import utils


class Playlist:
    """Representation of multiple videos in a sequence"""

    def __init__(self, items, filepath, *, discpath=None, duration=None, is_main=False):
        self._items = tuple(items)
        self._filepath = str(filepath)
        self._discpath = str(discpath) if discpath else None
        self._duration = duration
        self.is_main = is_main

    @functools.cached_property
    def type(self):
        """
        Underlying disc format

        "bluray" if :attr:`filename` has the file extension "mpls".
        "dvd" if :attr:`filename` has the file extension "ifo".
        Empty string otherwise.

        Matching is done case-insensitively.
        """
        file_extension = utils.fs.file_extension(self._filepath).lower()
        if file_extension == 'mpls':
            return 'bluray'
        elif file_extension == 'ifo':
            return 'dvd'
        else:
            return ''

    @functools.cached_property
    def label(self):
        """
        Human-readable string that serves as a unique playlist ID

        Combination of :attr:`discpath` (if provided) and :attr:`filename`.
        """
        if self.discname:
            return f'{self.discname}[{utils.fs.strip_extension(self.filename)}]'
        else:
            return utils.fs.strip_extension(self.filename)

    @property
    def items(self):
        """Sequence of file paths in the playlist"""
        return self._items

    @functools.cached_property
    def largest_item(self):
        """Largest file in :attr:`items`"""
        items_sorted = sorted(
            self.items,
            key=lambda filepath: (utils.fs.file_size(filepath) or 0),
            reverse=True,
        )
        return items_sorted[0]

    @property
    def filepath(self):
        """Path of the playlist file (e.g. MPLS or IFO file)"""
        return self._filepath

    @property
    def filename(self):
        """Basename of :attr:`filepath`"""
        return utils.fs.basename(self._filepath)

    @property
    def discpath(self):
        """
        Path of the directory that contains :attr:`filepath`

        Usually, this ia directory path that contains a "BDMV" or "VIDEO_TS" directory.
        """
        return self._discpath

    @property
    def discname(self):
        """Basename of :attr:`discpath`"""
        if self.discpath:
            return utils.fs.basename(self.discpath)

    @functools.cached_property
    def size(self):
        """Combined file size of all :attr:`items` as :attr:`utils.types.Bytes`"""
        return utils.types.Bytes(sum(
            # file_size() returns `None` by default.
            (utils.fs.file_size(item) or 0)
            for item in self.items
        ))

    @functools.cached_property
    def duration(self):
        """Combined runtime of :attr:`items` in seconds"""
        if self._duration is None:
            self._duration = sum(
                utils.mediainfo.get_duration(item)
                for item in self.items
            )
        return utils.types.Timestamp(self._duration)

    @property
    def is_main(self):
        """
        Simple boolean mark to track main playlists

        This property is mutable.
        """
        return self._is_main

    @is_main.setter
    def is_main(self, is_main):
        self._is_main = bool(is_main)

    # Attributes that make an instance unique.
    _id_attributes = ('discpath', 'filepath', 'items', 'duration')

    @property
    def id(self):
        """
        Sequence of values that make this instance unique

        Instances with the same :attr:`id` are equal.
        """
        return tuple(
            getattr(self, attr)
            for attr in self._id_attributes
        )

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.id == other.id
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f'<{type(self).__name__} {self.label}>'


def mark_main_playlists(playlists):
    """Find the main playlist(s) and set their :attr:`~.Playlist.is_main` property to ``True``"""
    if not playlists:
        return

    # Find the largest playlist first. We go by size instead of runtime because the runtime is often
    # wrong while size always goes up as video complexity/quality increases, and the main playlist
    # is most likely of the highest complexity/quality.
    playlists_sorted = sorted(playlists, key=lambda playlist: playlist.size)
    largest_playlist = playlists_sorted[-1]

    # Main playlists have a similar duration as the largest playlist.
    duration_min = largest_playlist.duration * 0.7
    duration_max = largest_playlist.duration * 1.3
    for playlist in playlists:
        playlist.is_main = bool(duration_min <= playlist.duration <= duration_max)
