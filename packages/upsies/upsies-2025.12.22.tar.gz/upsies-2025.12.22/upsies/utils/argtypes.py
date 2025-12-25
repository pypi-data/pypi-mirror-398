"""
CLI argument types

All types return normalized values and raise ValueError for invalid values.

A custom error message can be provided by raising
:class:`argparse.ArgumentTypeError`.
"""

import argparse
import functools
import os

from .. import errors, utils
from . import fs, types

natsort = utils.LazyModule(module='natsort', namespace=globals())


ArgumentTypeError = argparse.ArgumentTypeError
"""
Exception that should be raised by any callable that is passed to
:func:`argparse.ArgumentParser.add_argument` as `type` if it gets an invalid
value
"""


def comma_separated(argtype):
    """
    Multiple comma-separated values

    :param argtype: Any callable that returns a validated object for one of the
        comma-separated values or raises :class:`ValueError`, :class:`TypeError`
        or :class:`argparse.ArgumentTypeError`

    :return: Sequence of `argtype` return values
    """

    def comma_separated(value):
        values = []
        for string in str(value).split(','):
            string = string.strip()
            if string:
                try:
                    values.append(argtype(string))
                except (ValueError, TypeError) as e:
                    raise argparse.ArgumentTypeError(f'Invalid value: {string}') from e
        return values

    return comma_separated


def content(value):
    """Existing path to release file(s)"""
    path = release(value)
    return existing_path(path)


def existing_path(value):
    """Path to existing path"""
    path = str(value)
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f'No such file or directory: {value}')
    else:
        return path


def imagehost(value):
    """Name of a image hosting service from :mod:`~.imagehosts`"""
    from .. import imagehosts
    if value in imagehosts.imagehost_names():
        return value.lower()
    else:
        raise argparse.ArgumentTypeError(f'Unsupported image hosting service: {value}')


def imagehosts(value):
    """Comma-separated list of names of image hosting services from :mod:`~.imagehosts`"""
    names = []
    for name in value.split(','):
        name = name.strip()
        if name:
            names.append(imagehost(name))
    return names


def bool_or_none(value):
    """Convert `value` to :class:`~.types.Bool` or `None` if `value` is `None`"""
    if value is None:
        return None
    else:
        try:
            return types.Bool(value)
        except ValueError as e:
            raise argparse.ArgumentTypeError(e) from e


def integer(value, *, min=None, max=None):
    """
    Natural number (:class:`float` is rounded down)

    :param int min: Minimum value
    :param int max: Maximum value
    """
    try:
        return types.Integer(min=min, max=max)(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(e) from e


@functools.cache
def make_integer(*, min, max):
    """
    Return function that takes a number and passes it to :func:`integer` together with `min` and
    `max`

    :param int min: Minimum number of screenshots
    :param int max: Maximum number of screenshots
    """
    return functools.partial(integer, min=min, max=max)


@functools.cache
def files_with_extension(extension, *, allow_no_hits=True):
    """
    Return function that recursively searches a directory for files with
    `extension`

    If the returned function gets a file path with the wanted extension, it is
    simply returned.

    :param str extension: Wanted file name extension (e.g. "png")
    :param bool allow_no_hits: Whether :exc:`argparse.ArgumentTypeError` is
        raised if no matching files are found
    """

    def is_match(filepath):
        if fs.file_extension(filepath).casefold() == extension.casefold():
            try:
                fs.assert_file_readable(filepath)
            except errors.ContentError as e:
                raise argparse.ArgumentTypeError(e) from e
            else:
                return True
        return False

    def files_with_extension(value):
        matching_files = []

        if os.path.isdir(value):
            for dirpath, _dirnames, filenames in os.walk(value):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if is_match(filepath):
                        matching_files.append(filepath)

            if not matching_files and not allow_no_hits:
                raise argparse.ArgumentTypeError(f'{value}: No {extension} files found')

        else:
            if os.path.exists(value):
                if is_match(value):
                    matching_files = (value,)
                else:
                    msg = f'Expected file extension {extension}'
                    if ext := fs.file_extension(value):
                        msg += f', not {ext}'
                    msg += f': {value}'
                    raise argparse.ArgumentTypeError(msg)

            if not matching_files and not allow_no_hits:
                raise argparse.ArgumentTypeError(f'{value}: Not a {extension} file')

        return tuple(natsort.natsorted(
            matching_files,
            key=lambda filepath: fs.basename(filepath).casefold(),
        ))

    return files_with_extension


@functools.cache
def one_of(values):
    """
    Return function that returns an item of `values` or raises
    :class:`argparse.ArgumentTypeError`

    :param values: Allowed values
    """
    values = tuple(values)

    def one_of_values(value):
        if value in values:
            return value
        else:
            raise argparse.ArgumentTypeError(f'Invalid value: {value}')

    return one_of_values


def regex(value):
    """:class:`re.Pattern` object"""
    try:
        return types.Regex(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(e) from e


def release(value):
    """Same as :func:`content`, but doesn't have to exist"""
    from .. import errors
    from . import predbs
    path = str(value)
    try:
        predbs.assert_not_abbreviated_filename(path)
    except errors.SceneAbbreviatedFilenameError as e:
        raise argparse.ArgumentTypeError(e) from e
    else:
        return path


def predb_name(value):
    """Name of a scene release database from :mod:`~.utils.predbs`"""
    from . import predbs
    if value in predbs.predb_names():
        return value.lower()
    else:
        raise argparse.ArgumentTypeError(f'Unsupported scene release database: {value}')


def predb(value):
    """
    :class:`~.PredbApiBase` instance from a corresponding
    :attr:`~.PredbApiBase.name`
    """
    from . import predbs
    try:
        return predbs.predb(value.lower())
    except ValueError as e:
        raise argparse.ArgumentTypeError(e) from e


def timestamp(value):
    """Turn `value` into :class:`types.Timestamp`"""
    try:
        return types.Timestamp.from_string(value)
    except (ValueError, TypeError) as e:
        raise argparse.ArgumentTypeError(e) from e


def tracker(value):
    """Name of a tracker from :mod:`~.trackers`"""
    from .. import trackers
    if value in trackers.tracker_names():
        return value.lower()
    else:
        raise argparse.ArgumentTypeError(f'Unsupported tracker: {value}')


def webdb(value):
    """Name of a movie/series database from :mod:`~.webdbs`"""
    from . import webdbs
    if value in webdbs.webdb_names():
        return value.lower()
    else:
        raise argparse.ArgumentTypeError(f'Unsupported database: {value}')


@functools.cache
def webdb_id(webdb_name):
    """
    Return function that finds a web DB ID in a string, e.g. an URL

    :param str webdb_name: Name of a web DB, e.g. "imdb"

    The returned function takes any object and passes it to
    :meth:`~.WebDbApiBase.get_id_from_text`.
    """

    from . import webdbs
    db = webdbs.webdb(webdb_name)

    def webdb_id(value):
        id = db.get_id_from_text(str(value))
        if id:
            return id
        else:
            raise argparse.ArgumentTypeError(f'Invalid {db.name} ID: {value}')

    return webdb_id


def subtitle(value):
    """:class:`~.Subtitle` instance from language code"""
    subtitle = utils.mediainfo.text.Subtitle.from_string(value)
    if subtitle.language == '?':
        raise argparse.ArgumentTypeError(f'Unknown language code: {value}')
    else:
        return subtitle
