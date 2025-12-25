"""
Create torrent file
"""

import functools
import os

from .. import btclients, errors, utils
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)


class CreateTorrentJob(base.JobBase):
    """
    Create torrent file

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``announce_url``
            Emitted before and after successful announce URL retrieval.
            Registered callbacks get an :class:`Ellipsis` to indicate the
            retrieval attempt and the announce URL if the attempt was
            successful.

        ``file_tree``
            Emitted when torrent creation begins. Registered callbacks get
            nested `(file_name, file_size)` tuples (see
            :func:`~.utils.torrent.create`) as a positional argument. (See also
            :func:`.fs.format_file_tree`.)

        ``file_list``
            Emitted when torrent creation begins. Registered callbacks get a
            :class:`list` of paths to existing files that are in the torrent as
            a positional argument.

        ``progress_update``
            Emitted at roughly equal intervals to provide information about the
            torrent creation progress. Registered callbacks get a
            :class:`~.torrent.CreateTorrentProgress` or
            :class:`~.torrent.FindTorrentProgress` instance as a positional
            argument.
    """

    name = 'torrent'
    label = 'Torrent'
    cache_id = None

    def initialize(self, *, tracker, content_path, exclude_files=(), reuse_torrent_path=None):
        """
        Set internal state

        :param TrackerBase tracker: Return value of :func:`.trackers.tracker`
        :param content_path: Path to file or directory
        :param reuse_torrent_path: Path to existing torrent file to reuse piece
            hashes from (see :func:`~.utils.torrent.create`)
        :param exclude_files: Sequence of glob patterns (:class:`str`) and
            :class:`re.Pattern` objects (return value from :func:`re.compile`)
            that are matched against the relative path within the generated
            torrent

            Glob patterns are matched case-insensitively.

            .. note:: This sequence is combined with
                      :attr:`.TrackerBase.options`\\ ``["exclude"]``.
        """
        self._tracker = tracker
        self._content_path = content_path
        self._reuse_torrent_path = reuse_torrent_path
        self._torrent_path = os.path.join(
            self.home_directory,
            f'{utils.fs.basename(content_path)}.{tracker.name.lower()}.torrent',
        )

        self._exclude_files = list(self._tracker.options['exclude'])
        self._exclude_files.extend(exclude_files)

        self._torrent_process = None
        self._activity = ''

        self.signal.add('announce_url')
        self.signal.add('file_tree')
        self.signal.add('file_list')
        self.signal.add('progress_update')

    @property
    def activity(self):
        """
        What is currently being done

        ``"announce_url"``
            If we are getting the announce URL.

        ``"hashing"``
            If we are hashing files.

        ``"searching"``
            If we are searching for a torrent we can copy hashes from.

        ``"verifying"``
            If we are hash-checking a potentially matching torrent.

        ``""``
            None of the above is happening (e.g. we are getting the file tree).
        """
        return self._activity

    async def run(self):
        """Get announce URL from `tracker`, then execute torrent creation subprocess"""
        announce_url = await self._get_announce_url()
        if announce_url:
            self._start_torrent_process(announce_url)
            await self._torrent_process.join()

    async def _get_announce_url(self):
        self._activity = 'announce_url'
        self.signal.emit('announce_url', Ellipsis)
        try:
            announce_url = await self._tracker.get_announce_url()
        except errors.RequestError as e:
            self.error(e)
        else:
            self.signal.emit('announce_url', announce_url)
            return announce_url
        finally:
            self._activity = ''

    def _start_torrent_process(self, announce_url):
        self._torrent_process = utils.daemon.DaemonProcess(
            name=self.name,
            target=_torrent_process,
            kwargs={
                'content_path': self._content_path,
                'announce': announce_url,
                'source': self._tracker.torrent_source_field,
                'torrent_path': self._torrent_path,
                'exclude': self._exclude_files,
                'use_cache': not self.ignore_cache,
                'reuse_torrent_path': self._reuse_torrent_path,
                'piece_size_calculator': self._tracker.calculate_piece_size,
                'piece_size_min_max_calculator': self._tracker.calculate_piece_size_min_max,
            },
            init_callback=self._handle_files,
            info_callback=self._handle_info_update,
            error_callback=self._handle_error,
            result_callback=self._handle_torrent_created,
        )
        self._torrent_process.start()

    async def download_torrent(self, url):
        """
        Download torrent file and replace our own torrent

        Some trackers make unpredictable modifications to our torrent file, changing the info hash
        and forcing us to download their version. In that case, this method can be called to
        overwrite our torrent file with the altered version from the tracker.

        .. important:: This method must only be called AFTER this job is finished.

        :raise errors.RequestError: if downloading or writing file fails
        """
        if not self._torrent_process:
            raise RuntimeError('Torrent creation process has not even been started yet')
        elif not self._torrent_process.is_finished:
            raise RuntimeError('Torrent creation process is not finished yet')
        else:
            _log.debug('Downloading %r to %r', url, self._torrent_path)
            response = await utils.http.get(url)
            try:
                with open(self._torrent_path, 'wb') as f:
                    f.write(response.bytes)
            except OSError as e:
                msg = str(e.strerror) if e.strerror else str(e)
                raise errors.RequestError(msg) from None

    def terminate(self, reason=None):
        """Terminate torrent creation subprocess and all tasks"""
        if self._torrent_process:
            self._torrent_process.stop()
        super().terminate(reason=reason)

    def cancel_search(self):
        """
        Stop searching for a torrent we can copy hashes from

        If we are not currently searching for a torrent, do nothing.
        """
        if self._activity == 'searching' and self._torrent_process:
            self._torrent_process.send(utils.daemon.MsgType.terminate, utils.torrent.SKIP_SEARCHING)

    @base.unless_job_is_finished
    def _handle_files(self, files):
        self.signal.emit('file_tree', files.tree)
        self.signal.emit('file_list', files.list)

    @base.unless_job_is_finished
    def _handle_info_update(self, info):
        if isinstance(info, utils.torrent.CreateTorrentProgress):
            self._activity = 'hashing'
            self.signal.emit('progress_update', info)

        elif isinstance(info, utils.torrent.FindTorrentProgress):
            if info.status == 'verifying':
                self._activity = 'verifying'
            elif info.status == 'hit':
                _log.debug('Reusing torrent: %r', info.filepath)
                self._activity = ''
            else:
                self._activity = 'searching'
            self.signal.emit('progress_update', info)

        else:
            self._activity = ''
            raise RuntimeError('Unexpected info update: {info!r}')

    @base.unless_job_is_finished
    def _handle_torrent_created(self, torrent_path=None):
        _log.debug('Torrent created: %r', torrent_path)
        if torrent_path:
            self._torrent_path = torrent_path
            self.add_output(torrent_path)

    @base.unless_job_is_finished
    def _handle_error(self, error):
        if isinstance(error, (str, errors.TorrentCreateError)):
            self.error(error)
        else:
            self.exception(error)


def _torrent_process(output_queue, input_queue, *args, **kwargs):
    def init_callback(files):
        typ, _msg = utils.daemon.read_input_queue(input_queue)
        if typ == utils.daemon.MsgType.terminate:
            return 'cancel'
        else:
            output_queue.put((utils.daemon.MsgType.init, files))

    def progress_callback(progress):
        typ, msg = utils.daemon.read_input_queue(input_queue)
        if typ == utils.daemon.MsgType.terminate:
            if (
                    # We were told to skip searching (not to cancel torrent creation altogether)
                    msg == utils.torrent.SKIP_SEARCHING
                    # We are searching
                    and isinstance(progress, utils.torrent.FindTorrentProgress)
                    # No match found yet (False = no match, None = Verifying potential match)
                    and progress.status is not True
            ):
                # Stop searching for reusable torrent
                return utils.torrent.SKIP_SEARCHING
            else:
                # Cancel torrent creation altogether
                return 'cancel'
        else:
            output_queue.put((utils.daemon.MsgType.info, progress))

    kwargs['init_callback'] = init_callback
    kwargs['progress_callback'] = progress_callback
    try:
        torrent_path = utils.torrent.create(*args, **kwargs)
    except errors.TorrentCreateError as e:
        output_queue.put((utils.daemon.MsgType.error, e))
    else:
        output_queue.put((utils.daemon.MsgType.result, torrent_path))


class AddTorrentJob(base.JobBase):
    """
    Add torrent(s) to a BitTorrent client

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``adding``
            Emitted when attempting to add a torrent. Registered callbacks get
            the path to the torrent file as a positional argument.

        ``added``
            Emitted when the torrent was added successfully. Registered
            callbacks get the added torrent's info hash as a positional
            argument.
    """

    name = 'add-torrent'
    label = 'Add Torrent'
    cache_id = None  # Don't cache output

    @property
    def hidden(self):
        """
        `True` while this job is not :attr:`started <upsies.jobs.base.JobBase.is_started>`
        (i.e. waiting for a torrent to add), then `False`
        """
        return not self.is_started

    def initialize(self, *, btclient_config, torrent_files=(), download_path=None):
        """
        Set internal state

        :param btclient_config: :class:`~.btclient.BtclientConfig` instance
        :param torrent_files: Sequence of torrent file paths to add
        :param download_path: Download directory of each torrent's files

            This path is translated from a path on the computer that runs this code to a path on the
            BitTorrent client computer. See :attr:`~.btclients.fields.translate_path` and
            :class:`~.PathTranslations`.

        After all `torrent_files` are added, if a job named "torrent" exists,
        :meth:`~.JobBase.receive_all` torrents from that job and add them too.
        """
        self._torrent_filepaths = tuple(torrent_files)
        self._btclient_config = btclient_config
        self._download_path = download_path
        self.signal.add('adding')
        self.signal.add('added')
        self.signal.register('adding', lambda tp: setattr(self, 'info', f'Adding {utils.fs.basename(tp)}'))
        self.signal.register('added', lambda _: setattr(self, 'info', ''))
        self.signal.register('finished', lambda _: setattr(self, 'info', ''))
        self.signal.register('error', lambda _: setattr(self, 'info', ''))

        if not self._btclient_config['client']:
            self.error('No client specified')

    async def run(self):
        for torrent_filepath in self._torrent_filepaths:
            await self._add_torrent(torrent_filepath)

        if 'torrent' in self.siblings:
            async for torrent_filepath, in self.receive_all('torrent', 'output', only_posargs=True):
                await self._add_torrent(torrent_filepath)

    async def _add_torrent(self, torrent_path):
        self.signal.emit('adding', torrent_path)
        try:
            infohash = await self._btclient.add_torrent(
                torrent_path,
                download_path=self._download_path_translated,
            )
        except errors.TorrentAddError as e:
            self.error(e)
        else:
            self.add_output(infohash)
            self.signal.emit('added', infohash)

    @functools.cached_property
    def _btclient(self):
        try:
            return btclients.Btclient.from_config(self._btclient_config)
        except errors.ConfigError as e:
            # Translate ConfigError to TorrentAddError so it is caught by _add_torrent().
            raise errors.TorrentAddError(e) from e

    @functools.cached_property
    def _download_path_translated(self):
        if self._download_path:
            # Translate the (local) path that was provided to us to the (remote) path the client
            # should use to find/download the torrent's files.
            return self._btclient_config['translate_path'].translate(
                os.path.abspath(self._download_path)
            )
        else:
            # Use client's default path.
            return None


class CopyTorrentJob(base.JobBase):
    """
    Copy file(s)

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``copying``
            Emitted when attempting to copy a file. Registered callbacks get the
            source file path as a positional argument.

        ``copied``
            Emitted when the copy attempt ended. Registered callbacks get the
            destination file path (success) or the source file path (failure) as
            a positional argument.
    """

    name = 'copy-torrent'
    label = 'Copy Torrent'
    cache_id = None  # Don't cache output

    @property
    def hidden(self):
        """
        `True` while this job is not :attr:`started <upsies.jobs.base.JobBase.is_started>`
        (i.e. waiting for a torrent to add), then `False`
        """
        return not self.is_started

    def initialize(self, *, destination, torrent_files=()):
        """
        Set internal state

        :param destination: Where to put the torrent(s)
        :param torrent_files: Sequence of torrent file paths to copy to `destination`

        After all `torrent_files` are copied, if a job named "torrent" exists,
        :meth:`~.JobBase.receive_all` torrents from that job and copy them too.
        """
        self._torrent_filepaths = tuple(torrent_files)
        self._destination = None if not destination else str(destination)
        self.signal.add('copying')
        self.signal.add('copied')
        self.signal.register('copying', lambda fp: setattr(self, 'info', f'Copying {utils.fs.basename(fp)}'))
        self.signal.register('copied', lambda _: setattr(self, 'info', ''))
        self.signal.register('finished', lambda _: setattr(self, 'info', ''))
        self.signal.register('error', lambda _: setattr(self, 'info', ''))

    async def run(self):
        for torrent_filepath in self._torrent_filepaths:
            await self._copy_torrent(torrent_filepath)

        if 'torrent' in self.siblings:
            async for torrent_filepath, in self.receive_all('torrent', 'output', only_posargs=True):
                await self._copy_torrent(torrent_filepath)

    MAX_FILE_SIZE = 10 * 2**20  # 10 MiB
    """Upper limit of acceptable file size"""

    async def _copy_torrent(self, torrent_filepath):
        _log.debug('Copying %s to %s', torrent_filepath, self._destination)

        if not os.path.exists(torrent_filepath):
            self.error(f'{torrent_filepath}: No such file')

        elif os.path.getsize(torrent_filepath) > self.MAX_FILE_SIZE:
            self.error(f'{torrent_filepath}: File is too large')

        else:
            self.signal.emit('copying', torrent_filepath)

            import shutil
            try:
                new_path = shutil.copy2(torrent_filepath, self._destination)
            except OSError as e:
                msg = e.strerror if e.strerror else str(e)
                self.error(f'Failed to copy {torrent_filepath} to {self._destination}: {msg}')
            else:
                self.add_output(new_path)
                self.signal.emit('copied', new_path)
