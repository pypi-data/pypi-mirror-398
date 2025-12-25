"""
Wrapper for ``bdinfo`` command
"""

import functools

from .. import errors, utils
from ..utils import LazyModule, daemon
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)

natsort = LazyModule(module='natsort', namespace=globals())


class PlaylistsJob(base.JobBase):
    """
    Ask the user to select playlists from Blu-ray or DVD disc(s)

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``discs_available``
            Emitted when all subdirectories containing "BDMV" directories are found. Registered
            callbacks get a sequence of directory paths that each contain a "BDMV" directory.

        ``discs_selected``
            Emitted when the user has selected Blu-ray path(s). Registered callbacks get a sequence
            of directory paths that each contain a "BDMV" directory.

        ``playlists_available``
            Emitted when the list of playlists is available. Registered callbacks get a dictionary
            with they keys ``disc_path``, the parent path of the "BDMV" directory, and
            ``playlists``, a sequence of playlist dictionaries. Each playlist dictionary has the
            keys ``filepath`` ``size``, ``duration``, ``disc_path`` and ``items``. ``items`` is a
            sequence of ``.m2ts`` file paths. Playlists and playlist items are sorted by ``size`` in
            reverse order.

        ``playlists_selected``
            Emitted when the user has selected playlist(s). Registered callbacks get a sequence of
            playlist ``items`` as described in ``playlists_available``.
    """

    name = 'playlists'
    label = 'Playlists'

    @functools.cached_property
    def cache_id(self):
        """Final segment of `content_path` and "select_multiple" argument"""
        cache_id = [
            utils.fs.basename(self._content_path),
        ]
        if self.select_multiple:
            cache_id.append('select_multiple')
        return cache_id

    @property
    def select_multiple(self):
        """Whether the user may select multiple playlists"""
        return self._select_multiple

    def initialize(self, *, content_path, select_multiple=False):
        """
        Set internal state

        :param content_path: Path to directory that contains "BDMV" or "VIDEO_TS" directory

            May also contain multiple subdirectories that contain "BDMV" or "VIDEO_TS" directories
            (multidisc)

        :param bool select_multiple: Whether the user may select multiple playlists
        """
        self._content_path = content_path
        self._select_multiple = bool(select_multiple)
        self._selected_discpaths = set()
        self._processed_discpaths = set()
        self._selected_playlists = []
        self._playlists_process = None

        self.signal.add('discs_available')
        self.signal.add('discs_selected')
        self.signal.add('playlists_available')
        self.signal.add('playlists_selected', record=True)
        self.signal.register('playlists_selected', self._store_selected_playlists)

    async def run(self):
        self._playlists_process = daemon.DaemonProcess(
            name=self.name,
            target=_playlists_process,
            kwargs={
                'content_path': self._content_path,
            },
            info_callback=self._handle_info,
            error_callback=self._handle_error,
        )
        self._playlists_process.start()
        await self._playlists_process.join()
        await self.finalization()

        for playlist in self._selected_playlists:
            self.add_output(playlist.filepath)

    def terminate(self, reason=None):
        if self._playlists_process:
            self._playlists_process.stop()
        super().terminate(reason=reason)

    @base.unless_job_is_finished
    def _handle_info(self, info):
        if 'discs_available' in info:
            # Don't ask the user to pick discs if there is only one.
            discpaths = info['discs_available']
            for discpath in discpaths:
                _log.debug('Disc found: %r', discpath)
            if len(discpaths) <= 1:
                self.discs_selected(discpaths)
            else:
                self.signal.emit('discs_available', discpaths)

        elif 'playlists_available' in info:
            discpath, playlists = info['playlists_available']
            # Don't ask the user to pick discs if there is only one.
            for playlist in playlists:
                _log.debug('Playlist found: %r', playlist)
            if len(playlists) <= 1:
                self.playlists_selected(discpath, playlists)
            else:
                self.signal.emit('playlists_available', discpath, playlists)

        else:
            raise RuntimeError(f'Unexpected info: {info!r}')

    @base.unless_job_is_finished
    def _handle_error(self, error):
        if isinstance(error, errors.DependencyError):
            self.error(error)
        else:
            self.exception(error)

    def discs_selected(self, discpaths):
        """
        Called by the UI when the user selects disc(s)

        :param str discpaths: Sequence of directory paths that contain a "BDMV" or "VIDEO_TS"
            directory

        Calling this method emits the ``discs_selected`` signal.
        """
        for discpath in discpaths:
            _log.debug('Disc selected: %r', discpath)
        self._selected_discpaths.update(discpaths)
        self._playlists_process.send(daemon.MsgType.info, {'discs_selected': discpaths})
        self.signal.emit('discs_selected', discpaths)

        # If the user deselected all discs, playlists_selected() will never be called, which is
        # supposed to call finalize() to finish the job, so we must call finalize() now.
        if not discpaths:
            self.finalize()

    def playlists_selected(self, discpath, playlists):
        """
        Called by the UI when the user selects playlist(s)

        :param str discpath: Directory path that contains the `playlists`
        :param playlists: Sequence of :class:`~.types.Playlist` instances

        Calling this method emits the ``playlists_selected`` signal.
        """
        for playlist in playlists:
            _log.debug('Playlist selected: %r', playlist)

        self.signal.emit('playlists_selected', discpath, playlists)
        self._processed_discpaths.add(discpath)

        # Check if playlist(s) were selected for every selected disc. Note that it is possible
        # to select zero playlists from any disc or all discs.
        if self._processed_discpaths == self._selected_discpaths:
            _log.debug('All disc paths processed: %r', self._processed_discpaths)
            self.finalize()

        # If we are only interested in one disc and the user selected at least one playlist from
        # this disc, we don't need to prompt for more disks.
        elif playlists and not self.select_multiple:
            _log.debug('No more playlists required - not prompting user for any remaining discs')
            self.finalize()

    def _store_selected_playlists(self, discpath, playlists):
        self._selected_playlists.extend(playlists)

    @property
    def selected_playlists(self):
        """
        Sequence of :class:`~.types.Playlist` instances that were selected by the user

        This sequence will be empty at the beginning and grow as the user makes selections for each
        selected disc.
        """
        return tuple(self._selected_playlists)


def _playlists_process(output_queue, input_queue, *, content_path):
    if utils.disc.is_bluray(content_path, multidisc=True):
        disc_module = utils.disc.bluray
    elif utils.disc.is_dvd(content_path, multidisc=True):
        disc_module = utils.disc.dvd
    else:
        raise errors.ContentError(f'No BDMV or VIDEO_TS subdirectory found: {content_path}')

    selected_discs = _get_selected_discs(
        output_queue, input_queue,
        content_path=content_path,
        disc_module=disc_module,
    )
    for discpath in selected_discs:
        utils.daemon.maybe_terminate(input_queue)
        _report_available_playlists(output_queue, discpath=discpath, disc_module=disc_module)


def _get_selected_discs(output_queue, input_queue, *, content_path, disc_module):
    # Find all discs (in case of multi-disc releases).
    discs_available = tuple(natsort.natsorted(disc_module.get_disc_paths(content_path)))
    if not discs_available:
        output_queue.put((utils.daemon.MsgType.error, errors.ContentError(f'No disc found: {content_path}')))
        return ()
    else:
        # Report available discpaths back to main process.
        output_queue.put((utils.daemon.MsgType.info, {'discs_available': discs_available}))
        # Get user-selected disc(s) from main process.
        return utils.daemon.read_input_queue_key(input_queue, 'discs_selected')


def _report_available_playlists(output_queue, *, discpath, disc_module):
    playlists_available = _extend_playlists_info(disc_module.get_playlists(discpath))
    output_queue.put((utils.daemon.MsgType.info, {'playlists_available': (discpath, playlists_available)}))


def _extend_playlists_info(playlists):
    # Sort playlists in natural sort order by file path.
    return tuple(natsort.natsorted(playlists, key=lambda playlist: playlist.filepath))
