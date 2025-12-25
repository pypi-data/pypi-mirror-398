"""
Get information from "BDMV" and "VIDEO_TS" directory trees
"""

from .bluray import is_bluray
from .dvd import is_dvd
from .playlist import Playlist


def is_disc(content_path, *, multidisc=True):
    """Whether `content_path` :func:`~.is_bluray` or :func:`~.is_bluray`"""
    return (
        is_bluray(content_path, multidisc=multidisc)
        or is_dvd(content_path, multidisc=multidisc)
    )

