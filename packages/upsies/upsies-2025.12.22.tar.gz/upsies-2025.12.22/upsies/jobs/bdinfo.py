"""
Wrapper for ``bdinfo`` command
"""

import functools
import os
import re
import tempfile

from .. import errors, utils
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)


class BdinfoJob(base.JobBase):
    """
    Provide (partial) BDInfo report

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``progress``
            Emitted in short intervals after :meth:`playlists_selected` was called at least once
            until all BDInfo reports are available. Registered callbacks get a
            :class:`BdinfoProgress` instance.

        ``bdinfo_report``
            Emitted when a BDInfo report is available. Registered callbacks get a
            :class:`~.BdinfoReport` instance.
    """

    name = 'bdinfo'
    label = 'BDInfo'

    # Caching is done by the daemon process.
    cache_id = None

    _DEFAULT_FORMAT = '{BDINFO}'

    def initialize(self, *, summary=None, format=_DEFAULT_FORMAT):
        """
        Set internal state

        :param summary: Only provide a shorter summary as output

            One of ``full``, ``quick`` or `None`.

            Note that this only affects the :attr:`output`. :attr:`bdinfo_reports`,
            :attr:`full_summaries` and :attr:`quick_summaries` are always available.

        :param format: String that contains the placeholder ``"{BDINFO}"``, which is replaced by the
            actual BDInfo report
        """
        self._summary = summary
        self._format = str(format)
        self._bdinfo_reports = []
        self._reports_by_file = {}
        self._bdinfo_process = None

        self.signal.add('bdinfo_progress')
        self.signal.add('bdinfo_report')
        self.signal.register('bdinfo_report', self._store_bdinfo_report)
        self.signal.register('finished', self._hide_job)

    def _hide_job(self, job):
        # Do not display the BDInfo report as output. It can be very long.
        self.hidden = True

    async def run(self):
        self._bdinfo_process = utils.daemon.DaemonProcess(
            target=_bdinfo_process,
            kwargs={
                'cache_directory': self.cache_directory,
                'ignore_cache': self.ignore_cache,
            },
            info_callback=self._handle_info,
            error_callback=self._handle_error,
        )
        self._bdinfo_process.start()

        # Receive selected playlists from PlaylistsJob and pass them on to _bdinfo_process().
        async for discpath, playlists in self.receive_all('playlists', 'playlists_selected', only_posargs=True):
            _log.debug('Sending playlists to _bdinfo_process(): %r', playlists)
            self._bdinfo_process.send(utils.daemon.MsgType.info, {'playlists_selected': (discpath, playlists)})
        _log.debug('All playlists received')

        # Tell _bdinfo_process() that there won't be any more playlists.
        self._bdinfo_process.send(utils.daemon.MsgType.info, {'playlists_selected': _ALL_PLAYLIST_SELECTIONS_MADE})
        await self._bdinfo_process.join()
        self._add_bdinfo_reports()

    def _add_bdinfo_reports(self):
        if not self._summary:
            reports = self.bdinfo_reports
        elif self._summary == 'full':
            reports = self.full_summaries
        elif self._summary == 'quick':
            reports = self.quick_summaries
        else:
            raise RuntimeError(f'Unexpected summary value: {self._summary!r}')

        for report in reports:
            self.add_output(self._format.format(BDINFO=report))

    def terminate(self, reason=None):
        if self._bdinfo_process:
            self._bdinfo_process.stop()
        super().terminate(reason=reason)

    @base.unless_job_is_finished
    def _handle_info(self, info):
        if 'bdinfo_progress' in info:
            self.signal.emit('bdinfo_progress', info['bdinfo_progress'])

        elif 'bdinfo_report' in info:
            self.signal.emit('bdinfo_report', info['bdinfo_report'])

        else:
            raise RuntimeError(f'Unexpected info: {info!r}')

    @base.unless_job_is_finished
    def _handle_error(self, error):
        if isinstance(error, errors.DependencyError):
            self.error(error)
        else:
            self.exception(error)

    def _store_bdinfo_report(self, bdinfo_report):
        self._bdinfo_reports.append(bdinfo_report)
        self._reports_by_file[bdinfo_report.playlist.filepath] = bdinfo_report

    @property
    def bdinfo_reports(self):
        """Sequence of :class:`~.BdinfoReport` instances"""
        return tuple(self._bdinfo_reports)

    @property
    def reports_by_file(self):
        """Map playlist filepaths (.mpls) to BDInfo reports gathered so far"""
        return self._reports_by_file.copy()

    @property
    def full_summaries(self):
        """Sequence of :attr:`~.BdinfoReport.full_summary` values from :attr:`bdinfo_reports`"""
        return tuple(report.full_summary for report in self.bdinfo_reports)

    @property
    def quick_summaries(self):
        """Sequence of :attr:`~.BdinfoReport.quick_summary` values from :attr:`bdinfo_reports`"""
        return tuple(report.quick_summary for report in self.bdinfo_reports)


class BdinfoProgress(dict):
    """
    Simple :class:`dict` subclass with the following keys:

    - ``playlist`` (:class:`~.disc.Playlist`)
    - ``percent`` (:class:`int`)
    - ``time_elapsed`` (:class:`~.types.Timestamp`)
    - ``time_remaining`` (:class:`~.types.Timestamp`)

    Keys are also conveniently available as attributes.
    """

    def __init__(self, *, playlist, percent=0, time_elapsed=0, time_remaining=0):
        self['playlist'] = playlist
        self['percent'] = int(percent)
        self['time_elapsed'] = utils.types.Timestamp(time_elapsed)
        self['time_remaining'] = utils.types.Timestamp(time_remaining)

    def __getattr__(self, name):
        return self[name]


class BdinfoReport(str):
    """
    BDInfo report as special string with the additional properties :attr:`full_summary`,
    :attr:`quick_summary` and :attr:`playlist`
    """

    def __new__(cls, report, playlist):
        self = super().__new__(cls, report)
        self._playlist = playlist
        return self

    def __getnewargs__(self):
        # Make instances picklable by providing positional arguments.
        return (str(self), self.playlist)

    @functools.cached_property
    def full_summary(self):
        """Full summary of the BDInfo report"""
        regex = re.compile(r'^.*(DISC\s+INFO:$.*?)^FILES:$.*', flags=re.DOTALL | re.MULTILINE)
        match = regex.search(self)
        if match:
            return match.group(1).strip()

    @functools.cached_property
    def quick_summary(self):
        """Quick summary of the BDInfo report"""
        regex = re.compile(r'^.*^QUICK\s+SUMMARY:(.*)$', flags=re.DOTALL | re.MULTILINE)
        match = regex.search(self)
        if match:
            return match.group(1).strip()

    @functools.cached_property
    def playlist(self):
        """Source of the BDInfo report as a :class:`~.Playlist` instance"""
        return self._playlist

    def __repr__(self):
        return f'<{type(self).__name__} {self.playlist!r}>'


# NOTE: This cannot be the typical `object()` constant because its identity differs between the main
# process and _bdinfo_process() and `... is _ALL_PLAYLIST_SELECTIONS_MADE` doesn't work as expected.
_ALL_PLAYLIST_SELECTIONS_MADE = '_ALL_PLAYLIST_SELECTIONS_MADE'


def _bdinfo_process(output_queue, input_queue, *, cache_directory, ignore_cache):
    # This process reads user-selected playlists from the main process and runs `bdinfo` on them.
    while True:
        playlists_selected = utils.daemon.read_input_queue_key(input_queue, 'playlists_selected')

        if playlists_selected == _ALL_PLAYLIST_SELECTIONS_MADE:
            # No more values will be sent on `input_queue`.
            break
        else:
            _discpath, playlists = playlists_selected
            for playlist in playlists:
                bdinfo = _get_bdinfo(
                    output_queue, input_queue,
                    playlist=playlist,
                    cache_directory=cache_directory,
                    ignore_cache=ignore_cache,
                )
                bdinfo_report = BdinfoReport(bdinfo, playlist)
                output_queue.put((utils.daemon.MsgType.info, {'bdinfo_report': bdinfo_report}))
                utils.daemon.maybe_terminate(input_queue)


def _get_bdinfo(output_queue, input_queue, *, playlist, cache_directory, ignore_cache):
    # Make sure this is a BDMV path or we get weird exceptions.
    if not utils.disc.is_bluray(playlist.discpath):
        output_queue.put((utils.daemon.MsgType.error, errors.ContentError(f'Not a Blu-ray disc path: {playlist.discpath}')))

    else:
        cache_filepath = _get_cache_filepath(playlist, cache_directory)
        if (
                not ignore_cache
                and (bdinfo := _get_bdinfo_from_cache(cache_filepath))
        ):
            return bdinfo
        else:
            bdinfo = _get_bdinfo_from_bdinfo(output_queue, input_queue, playlist)
            _write_bdinfo_to_cache(bdinfo, cache_filepath)
            return bdinfo


def _get_bdinfo_from_bdinfo(output_queue, input_queue, playlist):
    # Write BDInfo report to temporary directory that will be deleted automatically.
    with tempfile.TemporaryDirectory() as bdinfo_directory:
        # Because BDInfo may be running inside a docker container with a different user ID, we
        # can't restrict permissions or the report cannot be written. This should not be an
        # issue because the BDInfo report isn't private information.
        os.chmod(bdinfo_directory, 0o777)

        for progress in _generate_bdinfo(
                playlist=playlist,
                bdinfo_directory=bdinfo_directory,
        ):
            utils.daemon.maybe_terminate(input_queue)
            output_queue.put((utils.daemon.MsgType.info, {'bdinfo_progress': progress}))

        return _find_bdinfo_in_directory(bdinfo_directory)


def _get_cache_filepath(playlist, cache_directory):
    return os.path.join(
        cache_directory,
        f'{playlist.label}.{int(playlist.size)}.bdinfo',
    )


def _get_bdinfo_from_cache(cache_filepath):
    try:
        with open(cache_filepath, 'r') as f:
            return f.read()
    except OSError as e:
        msg = e.strerror if e.strerror else str(e)
        _log.debug(f'Failed to read cache file {cache_filepath}: {msg}')


def _write_bdinfo_to_cache(bdinfo, cache_filepath):
    try:
        with open(cache_filepath, 'w') as f:
            return f.write(bdinfo)
    except OSError as e:
        msg = e.strerror if e.strerror else str(e)
        _log.debug(f'Failed to write cache file {cache_filepath}: {msg}')


def _generate_bdinfo(*, playlist, bdinfo_directory):
    # Initial zero progress report while `bdinfo` executable is starting up, which can take a few
    # seconds. This allows the UI to switch to a "report is being generated" display instead of just
    # doing nothing.
    yield BdinfoProgress(playlist=playlist)

    # Execute bdinfo with `communicate=True` so we can yield progress reports while it is running.
    argv = (
        'bdinfo',
        '--mpls=' + playlist.filename,
        playlist.discpath,
        bdinfo_directory,
    )
    process = utils.subproc.run(argv=argv, communicate=True)

    # Monitor bdinfo scanning progress.
    regex = re.compile(r'\D*?\b(?P<percent>\d+)(?:\.\d+|)\s?%.*?(?P<elapsed>\d+:\d+:\d+).*?(?P<remaining>\d+:\d+:\d+)')
    time_elapsed = utils.types.Timestamp(0)
    try:
        for line in process.stdout:
            match = regex.search(line)
            if match:
                time_elapsed = match.group('elapsed')
                yield BdinfoProgress(
                    playlist=playlist,
                    percent=match.group('percent'),
                    time_elapsed=time_elapsed,
                    time_remaining=match.group('remaining'),
                )

        stderr = '\n'.join(process.stderr)
        if stderr:
            raise RuntimeError(f'Command failed: {argv}:\n{stderr}')

        # Final progress report so the UI can reliably tell if a report is fully generated. This may
        # be redundant, but we can't rely on upstream bdinfo executable to always print "100%".
        yield BdinfoProgress(
            playlist=playlist,
            percent=100,
            time_elapsed=time_elapsed,
            time_remaining=0,
        )

    finally:
        # Always make sure the bdinfo process is terminated. Otherwise, it may continue to run even
        # after our main Python process terminates.
        process.terminate()


def _find_bdinfo_in_directory(bdinfo_directory):
    # Find report file. It should be the only file in `bdinfo_directory`.
    files = os.listdir(bdinfo_directory)
    if len(files) < 1:
        raise RuntimeError(f'No BDInfo report found in temporary BDInfo report directory: {bdinfo_directory}')
    elif len(files) > 1:
        raise RuntimeError(f'Unexpected files in temporary BDInfo report directory: {bdinfo_directory}: {sorted(files)}')
    else:
        bdinfo_file_path = os.path.join(bdinfo_directory, files[0])
        with open(bdinfo_file_path, 'r') as f:
            return f.read()
