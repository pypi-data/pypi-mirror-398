"""
Create torrent file
"""

import collections
import datetime
import errno
import fnmatch
import os
import re
import time

from .. import __project_name__, __version__, constants, errors, utils
from . import LazyModule, fs, types

torf = LazyModule(module='torf', namespace=globals())


SKIP_SEARCHING = 'skip_searching'
"""
Return value for the `progress_callback` to stop searching for a reusable
torrent (see :func:`create`)
"""


def create(*, content_path, announce, source,
           torrent_path, exclude=(), use_cache=True,
           reuse_torrent_path=None,
           piece_size_calculator=None, piece_size_min_max_calculator=None,
           init_callback, progress_callback):
    """
    Generate and write torrent file

    :param str content_path: Path to the torrent's payload
    :param str announce: Announce URL
    :param str source: Value of the ``source`` field in the torrent. This makes
        the torrent unique for each tracker to avoid cross-seeding issues, so it
        is usually the tracker's abbreviated name.
    :param str torrent_path: Path of the generated torrent file
    :param exclude: Sequence of glob patterns (:class:`str`) and
        :class:`re.Pattern` (return value from :func:`re.compile`) or
        :class:`~.types.Regex` objects

        Files beneath `content_path` are excluded from the torrent.

        Glob patterns are matched case-insensitively. For case-insensitive
        matching with regular expressions, use ``(?i:<pattern>)``.
    :param bool use_cache: Whether to get piece hashes from previously created
        torrents or from `reuse_torrent_path`
    :param reuse_torrent_path: Path to existing torrent file to get hashed
        pieces and piece size from. If the given torrent file doesn't match the
        files in the torrent we want to create, hash the pieces normally.

        If this is a directory, search it recursively for ``*.torrent`` files
        and use the first one that matches.

        Non-existing or otherwise unreadable paths as well as falsy values
        (e.g. ``""`` or `None`) are silently ignored.

        If this is a sequence, its items are expected to be directory or file
        paths and handled as described above.
    :param piece_size_calculator: Function that takes the torrent's content size
        in bytes and returns the piece size

        If this is `None`, the default implementation is used.
    :param piece_size_min_max_calculator: Function that takes the torrent's
        content size in bytes and returns the allowed minimum and maximum piece
        sizes or `None` to use the default minimum or maximum piece size

        If this is `None`, the default minimum and maximum piece sizes are used.
    :param init_callback: Callable that is called once before torrent generation
        commences with a :class:`Files` object
    :param progress_callback: Callable that is called at regular intervals with
        a :class:`CreateTorrentProgress` or :class:`FindTorrentProgress` object
        as a positional argument

    Callbacks can cancel the torrent creation by returning `True` or any other
    truthy value. If `progress_callback` returns :data:`SKIP_SEARCHING`, the
    search for a reusable torrent is cancelled and pieces are hashed normally.

    :raise TorrentCreateError: if anything goes wrong

    :return: `torrent_path` or `None` if cancelled
    """
    if not announce:
        raise errors.TorrentCreateError('Announce URL is empty')
    if not source:
        raise errors.TorrentCreateError('Source is empty')

    # Create Torrent object
    torrent = _get_torrent(
        content_path=content_path,
        exclude=_get_exclude_regexs(exclude),
        announce=announce,
        source=source,
    )

    # Custom piece_size management
    if piece_size_min_max_calculator:
        # Calculate custom piece_size boundaries based on torrent's content size
        torrent.piece_size_min, torrent.piece_size_max = piece_size_min_max_calculator(torrent.size)
    if piece_size_calculator:
        # Calculate custom piece_size based on torrent's content size
        torrent.piece_size = piece_size_calculator(torrent.size)

    # Report files with `exclude` applied
    cancelled = init_callback(Files(torrent))
    if cancelled:
        return None

    if use_cache:
        # Try to get piece hashes from existing torrent
        cancelled = _find_hashes(
            torrent=torrent,
            reuse_torrent_path=reuse_torrent_path,
            callback=progress_callback,
        )
        if cancelled and cancelled != SKIP_SEARCHING:
            return None

    if not torrent.is_ready:
        # Hash pieces
        cancelled = _generate_hashes(
            torrent=torrent,
            callback=progress_callback,
        )
        if cancelled:
            return None

    # Write generic torrent so we can reuse the hashes in the future
    _store_generic_torrent(torrent)

    # Write torrent to `torrent_path`
    _write_torrent_path(torrent, torrent_path)

    return torrent_path


def _get_exclude_regexs(exclude):
    regexs = []
    for pattern in exclude:
        if isinstance(pattern, re.Pattern):
            regexs.append(pattern)
        elif isinstance(pattern, types.Regex):
            regexs.append(re.compile(pattern.pattern))
        elif isinstance(pattern, str):
            regexs.append(re.compile(fnmatch.translate(str(pattern)), flags=re.IGNORECASE))
        else:
            raise TypeError(f'Unexpected exclude type: {pattern!r}')
    return regexs


def _get_torrent(*, content_path, exclude, announce, source):
    try:
        return torf.Torrent(
            path=content_path,
            exclude_regexs=exclude,
            trackers=((announce,),),
            source=source,
            private=True,
            created_by=f'{__project_name__} {__version__}',
            creation_date=time.time(),
        )
    except torf.TorfError as e:
        raise errors.TorrentCreateError(str(e)) from e


def _generate_hashes(*, torrent, callback):
    wrapped_callback = _CreateTorrentCallback(callback)
    try:
        torrent.generate(
            callback=wrapped_callback,
            interval=1.0,
        )
    except torf.TorfError as e:
        raise errors.TorrentCreateError(str(e)) from e
    else:
        return wrapped_callback.return_value


def _find_hashes(*, torrent, reuse_torrent_path, callback):
    if not torrent.files:
        # All files are excluded (let someone deal with it)
        return False

    wrapped_callback = _FindTorrentCallback(callback)
    try:
        torrent.reuse(
            _get_reuse_torrent_paths(torrent, reuse_torrent_path),
            callback=wrapped_callback,
            interval=1.0,
        )
    except torf.TorfError as e:
        raise errors.TorrentCreateError(str(e)) from e
    else:
        return wrapped_callback.return_value


def _get_reuse_torrent_paths(torrent, reuse_torrent_path):
    reuse_torrent_paths = []
    if reuse_torrent_path:
        if isinstance(reuse_torrent_path, str):
            reuse_torrent_paths.append(reuse_torrent_path)
        elif isinstance(reuse_torrent_path, collections.abc.Iterable):
            reuse_torrent_paths.extend(p for p in reuse_torrent_path if p)
        else:
            raise ValueError(f'Invalid reuse_torrent_path: {reuse_torrent_path!r}')

    generic_torrent_path = _get_generic_torrent_path(torrent=torrent, create_directory=False)
    reuse_torrent_paths.insert(0, generic_torrent_path)
    return tuple(
        os.path.expanduser(path)
        for path in reuse_torrent_paths
    )


def _store_generic_torrent(torrent):
    generic_torrent = torf.Torrent(
        private=True,
        created_by=f'{__project_name__} {__version__}',
        creation_date=time.time(),
        comment='This torrent is used to cache previously hashed pieces.',
    )
    _copy_torrent_info(torrent, generic_torrent)
    generic_torrent_path = _get_generic_torrent_path(generic_torrent, create_directory=True)
    generic_torrent.write(generic_torrent_path, overwrite=True)


def _write_torrent_path(torrent, torrent_path):
    try:
        torrent.write(torrent_path, overwrite=True)
    except torf.TorfError as e:
        raise errors.TorrentCreateError(str(e)) from e


def _get_generic_torrent_path(torrent, *, create_directory=True):
    directory = constants.GENERIC_TORRENTS_DIRPATH
    if create_directory:
        try:
            fs.mkdir(directory)
        except errors.ContentError as e:
            raise errors.TorrentCreateError(f'{directory}: {e}') from e

    cache_id = _get_torrent_id(torrent)
    filename = f'{torrent.name}.{cache_id}.torrent'
    return os.path.join(directory, filename)


def _get_torrent_id_info(torrent):
    return {
        'name': torrent.name,
        'files': tuple((str(f), f.size) for f in torrent.files),
    }


def _get_torrent_id(torrent):
    return utils.semantic_hash(_get_torrent_id_info(torrent))


def _copy_torrent_info(from_torrent, to_torrent):
    from_info, to_info = from_torrent.metainfo['info'], to_torrent.metainfo['info']
    to_info['pieces'] = from_info['pieces']
    to_info['piece length'] = from_info['piece length']
    to_info['name'] = from_info['name']
    if 'length' in from_info:
        to_info['length'] = from_info['length']
    else:
        to_info['files'] = from_info['files']


class Files:
    """Structured torrent file content"""

    def __init__(self, torrent):
        self._list = self._make_file_list(torrent.filepaths)
        self._tree = self._make_file_tree(
            torrent.filetree,
            parent_path=str(torrent.path.parent),
            strip_leading_sep=False,
        )

    def _make_file_list(self, filepaths):
        return tuple(str(filepath) for filepath in filepaths)

    def _make_file_tree(self, filetree, *, parent_path='', strip_leading_sep=True):
        files = []

        for name, file in filetree.items():
            path = os.sep.join((parent_path, name))
            if strip_leading_sep:
                path = path.strip(os.sep)
            else:
                path = path.rstrip(os.sep)

            if isinstance(file, collections.abc.Mapping):
                subtree = self._make_file_tree(file)
                files.append((path, subtree))
            else:
                files.append((path, file.size))

        return tuple(files)

    @property
    def list(self):
        """Sequence of existing file paths (:class:`str`)"""
        return self._list

    @property
    def tree(self):
        """
        Nested files

        This is a tree where each node is a tuple in which the first item is the
        directory name and the second item is a sequence of `(file_name,
        file_size)` or `(file_name, sub_tree)` tuples.

        Example:

        .. code::

           ('Parent',
               ('Foo', (
                   ('Picture.jpg', 82489),
                   ('Music.mp3', 5315672),
                   ('More files', (
                       ('This.txt', 57734),
                       ('And that.txt', 184),
                       ('Also some of this.txt', 88433),
                   )),
               )),
               ('Bar', (
                   ('Yee.mp4', 288489392),
                   ('Yah.mkv', 3883247384),
               )),
           )
        """
        return self._tree


class _CallbackBase:
    def __init__(self, callback):
        self._callback = callback
        self._progress_samples = []
        self._time_started = time.time()
        self.return_value = None

    def __call__(self, progress):
        self.return_value = return_value = self._callback(progress)
        return return_value

    def _calculate_info(self, items_done, items_total):
        time_now = time.time()
        percent_done = items_done / items_total * 100
        seconds_elapsed = time_now - self._time_started
        items_per_second = 0
        items_remaining = items_total - items_done
        seconds_remaining = 0

        self._add_sample(time_now, items_done)

        # Estimate how long torrent creation will take
        samples = self._progress_samples
        if len(samples) >= 2:
            # Calculate the difference between each pair of samples
            diffs = [
                b[1] - a[1]
                for a, b in zip(samples[:-1], samples[1:])
            ]
            items_per_second = self._get_average(diffs, weight_factor=1.1)
            if items_per_second > 0:
                seconds_remaining = items_remaining / items_per_second

        seconds_total = seconds_elapsed + seconds_remaining
        time_finished = self._time_started + seconds_total

        return {
            'percent_done': percent_done,
            'items_remaining': items_remaining,
            'items_per_second': items_per_second,
            'seconds_elapsed': datetime.timedelta(seconds=seconds_elapsed),
            'seconds_remaining': datetime.timedelta(seconds=seconds_remaining),
            'seconds_total': datetime.timedelta(seconds=seconds_total),
            'time_finished': datetime.datetime.fromtimestamp(time_finished),
            'time_started': datetime.datetime.fromtimestamp(self._time_started),
        }

    def _add_sample(self, time_now, items_done):
        def get_sample_age(sample):
            time_sample = sample[0]
            return time_now - time_sample

        samples = self._progress_samples
        samples.append((time_now, items_done))

        # Prune samples older than 10 seconds
        while samples and get_sample_age(samples[0]) > 10:
            del samples[0]

    def _get_average(self, samples, weight_factor, get_value=lambda sample: sample):
        # Give recent samples more weight than older samples
        # https://en.wikipedia.org/wiki/Moving_average
        weights = []
        for _ in range(len(samples)):
            try:
                weight = weights[-1]
            except IndexError:
                weight = 1
            weights.append(weight * weight_factor)

        return sum(
            get_value(sample) * weight
            for sample, weight in zip(samples, weights)
        ) / sum(weights)


class _CreateTorrentCallback(_CallbackBase):
    def __call__(self, torrent, filepath, pieces_done, pieces_total):
        info = self._calculate_info(pieces_done, pieces_total)
        piece_size = torrent.piece_size
        bytes_per_second = types.Bytes(info['items_per_second'] * piece_size)
        progress = CreateTorrentProgress(
            pieces_done=pieces_done,
            pieces_total=pieces_total,
            percent_done=info['percent_done'],
            bytes_per_second=bytes_per_second,
            piece_size=piece_size,
            total_size=torrent.size,
            filepath=filepath,
            seconds_elapsed=info['seconds_elapsed'],
            seconds_remaining=info['seconds_remaining'],
            seconds_total=info['seconds_total'],
            time_finished=info['time_finished'],
            time_started=info['time_started'],
        )
        return super().__call__(progress)


class _FindTorrentCallback(_CallbackBase):
    def __call__(self, torrent, filepath, files_done, files_total, status, exception):
        info = self._calculate_info(files_done, files_total)

        # Ignore "No such file or directory". This should only happen if the
        # generic torrent does not exist yet. For all other paths, torrent files
        # are collected from traversing directories.
        if isinstance(exception, torf.ReadError) and exception.errno == errno.ENOENT:
            exception = None

        if status is True:
            status = 'hit'
        elif status is False:
            status = 'miss'
        else:
            status = 'verifying'

        progress = FindTorrentProgress(
            files_done=files_done,
            files_total=files_total,
            percent_done=info['percent_done'],
            files_per_second=info['items_per_second'],
            filepath=filepath,
            status=status,
            exception=errors.TorrentCreateError(str(exception)) if exception else None,
            seconds_elapsed=info['seconds_elapsed'],
            seconds_remaining=info['seconds_remaining'],
            seconds_total=info['seconds_total'],
            time_finished=info['time_finished'],
            time_started=info['time_started'],
        )
        return super().__call__(progress)


class CreateTorrentProgress(collections.namedtuple(
    typename='CreateTorrentProgress',
    field_names=(
        'bytes_per_second',
        'filepath',
        'percent_done',
        'piece_size',
        'pieces_done',
        'pieces_total',
        'seconds_elapsed',
        'seconds_remaining',
        'seconds_total',
        'time_finished',
        'time_started',
        'total_size',
    ),
)):
    """
    :func:`~.collections.namedtuple` with these attributes:

        - ``bytes_per_second`` (:class:`~.types.Bytes`)
        - ``filepath`` (:class:`str`)
        - ``percent_done`` (:class:`float`)
        - ``piece_size`` (:class:`~.types.Bytes`)
        - ``pieces_done`` (:class:`int`)
        - ``pieces_total`` (:class:`int`)
        - ``seconds_elapsed`` (:class:`~.datetime.datetime.timedelta`)
        - ``seconds_remaining`` (:class:`~.datetime.datetime.timedelta`)
        - ``seconds_total`` (:class:`~.datetime.datetime.timedelta`)
        - ``time_finished`` (:class:`~.datetime.datetime.datetime`)
        - ``time_started`` (:class:`~.datetime.datetime.datetime`)
        - ``total_size`` (:class:`~.types.Bytes`)
    """


class FindTorrentProgress(collections.namedtuple(
    typename='CreateTorrentProgress',
    field_names=(
        'exception',
        'filepath',
        'files_done',
        'files_per_second',
        'files_total',
        'percent_done',
        'seconds_elapsed',
        'seconds_remaining',
        'seconds_total',
        'status',
        'time_finished',
        'time_started',
    ),
)):
    """
    :func:`~.collections.namedtuple` with these attributes:

        - ``exception`` (:class:`~.errors.TorrentCreateError` or `None`)
        - ``filepath`` (:class:`str`)
        - ``files_done`` (:class:`int`)
        - ``files_per_second`` (:class:`int`)
        - ``files_total`` (:class:`int`)
        - ``percent_done`` (:class:`float`)
        - ``seconds_elapsed`` (:class:`~.datetime.datetime.timedelta`)
        - ``seconds_remaining`` (:class:`~.datetime.datetime.timedelta`)
        - ``seconds_total`` (:class:`~.datetime.datetime.timedelta`)
        - ``status`` (``hit``, ``miss`` or ``verifying``)
        - ``time_finished`` (:class:`~.datetime.datetime.datetime`)
        - ``time_started`` (:class:`~.datetime.datetime.datetime`)
    """
