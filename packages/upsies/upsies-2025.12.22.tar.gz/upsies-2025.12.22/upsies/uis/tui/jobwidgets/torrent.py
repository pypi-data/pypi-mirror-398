import functools

from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, HorizontalAlign, HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension

from .... import __project_name__, errors, utils
from .. import widgets
from . import JobWidgetBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class CreateTorrentJobWidget(JobWidgetBase):

    is_interactive = False

    def setup(self):
        # Extend some error messages with additional information specific to this UI,
        # e.g. "use --option to fix this".
        self.job.signal.register('error', self.handle_error)

        self._progress = widgets.ProgressBar()
        self._file_tree = FormattedTextControl()
        self._throughput = FormattedTextControl()
        self._throughput_unit = ''
        self._percent_done = FormattedTextControl()
        self._seconds_elapsed = FormattedTextControl()
        self._seconds_remaining = FormattedTextControl()
        self._seconds_total = FormattedTextControl()
        self._time_started = FormattedTextControl()
        self._time_finished = FormattedTextControl()
        self._current_file_name = ''

        status_column1 = HSplit(
            children=[
                self.make_readout(' Started:', '_time_started', width=8),
                self.make_readout('Finished:', '_time_finished', width=8),
            ],
        )
        status_column2 = HSplit(
            children=[
                self.make_readout('  Elapsed:', '_seconds_elapsed', width=8),
                self.make_readout('Remaining:', '_seconds_remaining', width=8),
                self.make_readout('    Total:', '_seconds_total', width=8),
            ],
        )
        status_column3 = HSplit(
            children=[
                self.make_readout(
                    lambda: '%'.ljust(len(self._throughput_unit)),
                    '_percent_done',
                    width=6,
                    value_align='right',
                    label_side='right',
                ),
                self.make_readout(
                    lambda: self._throughput_unit.ljust(len(self._throughput_unit)),
                    '_throughput',
                    width=6,
                    value_align='right',
                    label_side='right',
                ),
            ],
        )
        status = VSplit(children=[status_column1, status_column2, status_column3], padding=3)

        self._activity_indicator = widgets.ActivityIndicator(
            style='class:info',
        )
        self.job.signal.register('finished', lambda _: self._activity_indicator.disable())

        self._runtime_widget = HSplit(
            children=[
                ConditionalContainer(
                    filter=Condition(lambda: not self.job.output and self._progress.percent > 0),
                    content=HSplit([
                        # Estimated times, progress per second, etc
                        status,
                        # Progress bar
                        self._progress,
                    ]),
                ),
                VSplit([
                    # Moving character to indicate activity
                    ConditionalContainer(
                        filter=Condition(lambda: self._activity_indicator.active),
                        content=VSplit([
                            self._activity_indicator,
                            widgets.hspacer,
                        ]),
                    ),
                    # "Hashing", "Searching", "Press ... to skip hashing", etc.
                    Window(
                        FormattedTextControl(self._get_current_activity),
                        # Make sure that the activity is always displayed in
                        # full and the current file name is trimmed to make it fit
                        width=Dimension(weight=10),
                        dont_extend_width=True,
                    ),
                    widgets.hspacer,
                    # Current file name (torrent or content file)
                    ConditionalContainer(
                        filter=Condition(lambda: not self.job.output and self._current_file_name),
                        content=Window(
                            FormattedTextControl(lambda: self._current_file_name),
                        ),
                    ),
                ]),
                ConditionalContainer(
                    filter=Condition(lambda: not self.job.output and self._file_tree.text),
                    content=Window(self._file_tree),
                ),
            ],
            style='class:info',
            width=Dimension(min=55, max=150),
        )

        @self.keybindings_global.add(
            'c-t', 'h',
            filter=Condition(lambda: self.job.activity in ('searching', 'verifying')),
        )
        def _(_event):
            self.job.cancel_search()

        self.job.signal.register('file_tree', self.handle_file_tree)
        self.job.signal.register('progress_update', self.handle_progress_update)
        self.job.signal.register('finished', lambda _: self.invalidate())
        self.job.signal.register('output', lambda _: self.invalidate())

    def make_readout(self, label, attribute, value_align='left', width=None, label_side='left'):
        readout_widget = Window(
            getattr(self, attribute),
            dont_extend_width=True,
            dont_extend_height=True,
            style='class:info.readout',
            width=width,
            align=getattr(WindowAlign, value_align.upper()),
        )
        label_widget = Window(FormattedTextControl(label), dont_extend_width=True)

        if label_side == 'left':
            children = [label_widget, readout_widget]
        elif label_side == 'right':
            children = [readout_widget, label_widget]

        return VSplit(
            children=children,
            padding=1,
            align=HorizontalAlign.CENTER,
        )

    def handle_error(self, error):
        if isinstance(error, errors.AnnounceUrlNotSetError):
            cmd = f'{__project_name__} set trackers.{error.tracker.name}.announce_url <URL>'
            self.job.error(f'Set it with this command: {cmd}')

    def handle_file_tree(self, file_tree):
        self._file_tree.text = utils.fs.format_file_tree(file_tree)

    def handle_progress_update(self, info):
        self._progress.percent = info.percent_done
        self._percent_done.text = f'{info.percent_done:.2f}'

        self._time_started.text = info.time_started.strftime('%H:%M:%S')
        self._time_finished.text = info.time_finished.strftime('%H:%M:%S')

        def timedelta_string(delta):
            hours, rest = divmod(delta.total_seconds(), 3600)
            minutes, seconds = divmod(rest, 60)
            return f'{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}'

        self._seconds_elapsed.text = timedelta_string(info.seconds_elapsed)
        self._seconds_remaining.text = timedelta_string(info.seconds_remaining)
        self._seconds_total.text = timedelta_string(info.seconds_total)

        if isinstance(info, utils.torrent.CreateTorrentProgress):
            # Torrent is hashed from content files
            throughput = info.bytes_per_second.format(
                prefix='binary',
                decimal_places=2,
                trailing_zeros=True,
            )
            self._throughput.text, self._throughput_unit = throughput.split(' ')
            self._throughput_unit += '/s'
            self._current_file_name = utils.fs.basename(info.filepath)

        elif isinstance(info, utils.torrent.FindTorrentProgress):
            # Torrent is searched by hash in existing torrents
            if info.exception:
                self.job.warn(info.exception)
            elif info.status == 'verifying':
                self._activity_indicator.active = True
            else:
                self._activity_indicator.active = False

            self._throughput.text = f'{info.files_per_second}'
            self._throughput_unit = 'files/s'
            self._current_file_name = utils.fs.basename(info.filepath)

        self.invalidate()

    def _get_current_activity(self):
        if self.job.activity in ('announce_url', 'verifying'):
            self._activity_indicator.active = True
        else:
            self._activity_indicator.active = False

        if self.job.activity == 'announce_url':
            activity = 'Getting announce URL'
        elif self.job.activity == 'searching':
            activity = 'Press <Ctrl-t h> to skip searching for a reusable torrent'

        # TODO: Remove this. CreateTorrentJob doesn't login() and logout() anymore.
        elif self.job.output:
            # If have output (i.e. the torrent file path), but we are not
            # finished yet, the only reason this can happen is if
            # get_announce_url() called login() and we have to wait for
            # logout().
            activity = 'Logging out'

        else:
            activity = self.job.activity.capitalize()

        return activity

    @functools.cached_property
    def runtime_widget(self):
        return self._runtime_widget


class AddTorrentJobWidget(JobWidgetBase):

    is_interactive = False

    def setup(self):
        pass

    @functools.cached_property
    def runtime_widget(self):
        return None


class CopyTorrentJobWidget(JobWidgetBase):

    is_interactive = False

    def setup(self):
        pass

    @functools.cached_property
    def runtime_widget(self):
        return None
