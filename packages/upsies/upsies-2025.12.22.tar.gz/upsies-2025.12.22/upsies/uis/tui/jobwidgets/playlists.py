import functools

from prompt_toolkit.layout.containers import DynamicContainer

from .... import utils
from .. import widgets
from . import JobWidgetBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class PlaylistsJobWidget(JobWidgetBase):

    is_interactive = True

    def setup(self):
        self._activity_indicator = widgets.ActivityIndicator(
            style='class:info',
            extend_width=True,
        )
        self._queued_list_dialogs = []
        self._current_list_dialog = None

        self.job.signal.register('discs_available', self.handle_discs_available)
        self.job.signal.register('playlists_available', self.handle_playlists_available)
        self.job.signal.register('running', lambda _: self._activity_indicator.enable())
        self.job.signal.register('finished', lambda _: self._activity_indicator.disable())

    def handle_discs_available(self, discpaths):
        self.add_list_dialog(
            options=tuple(
                (
                    # Human-readable value.
                    utils.fs.basename(path),
                    # Computer-usable value.
                    path,
                )
                for path in discpaths
            ),
            # Mark all discs as autodetected.
            autodetected_indexes=range(len(discpaths)),
            callback=self.job.discs_selected,
        )

    def handle_playlists_available(self, discpath, playlists):
        options = []
        autodetected_indexes = []
        for index, playlist in enumerate(playlists):
            options.append(
                (
                    # Human-readable value.
                    '   '.join((
                        str(utils.fs.basename(playlist.filepath)).rjust(10),
                        str(playlist.duration),
                        str(playlist.size).rjust(9),
                    )),
                    # Computer-usable value.
                    playlist,
                )
            )
            if playlist.is_main:
                autodetected_indexes.append(index)

        self.add_list_dialog(
            question=discpath,
            options=options,
            autodetected_indexes=autodetected_indexes,
            callback=lambda playlists: self.job.playlists_selected(discpath, playlists),
        )

    def add_list_dialog(self, *, options, callback, question=None, autodetected_indexes=()):
        if self.job.select_multiple:
            list_dialog = widgets.CheckList(
                question=question,
                options=options,
                on_accepted=lambda options: self.handle_checklist_dialog_accepted(callback, options),
                autodetected_indexes=autodetected_indexes,
                focused=(autodetected_indexes[0] if autodetected_indexes else None),
            )
        else:
            list_dialog = widgets.RadioList(
                question=question,
                options=options,
                on_accepted=lambda option: self.handle_radiolist_dialog_accepted(callback, option),
                autodetected_index=autodetected_indexes[0],
                focused=(autodetected_indexes[0] if autodetected_indexes else None),
            )
        self._queued_list_dialogs.append(list_dialog)
        self.maybe_show_next_list_dialog()

    def maybe_show_next_list_dialog(self):
        if not self._current_list_dialog and self._queued_list_dialogs:
            self._current_list_dialog = self._queued_list_dialogs.pop(0)
            self.invalidate()

    def handle_checklist_dialog_accepted(self, callback, options):
        # The first item in each 2-tuple option is the human-readable display value, the second item
        # is what we actually use internally.
        values = tuple(option[1] for option in options)
        callback(values)
        self._current_list_dialog = None
        self.maybe_show_next_list_dialog()

    def handle_radiolist_dialog_accepted(self, callback, option):
        # The first item in `option` the human-readable display value, the second item is what we
        # actually use internally.
        values = (option[1],)
        callback(values)
        self._current_list_dialog = None
        self.maybe_show_next_list_dialog()

    @functools.cached_property
    def runtime_widget(self):
        return DynamicContainer(self.get_runtime_widgets)

    def get_runtime_widgets(self):
        if self._current_list_dialog:
            self._activity_indicator.disable()
            return self._current_list_dialog
        else:
            self._activity_indicator.enable()
            return self._activity_indicator
