import functools

from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit

from .. import widgets
from . import JobWidgetBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class ChoiceJobWidget(JobWidgetBase):

    is_interactive = True

    def setup(self):
        if self.job.multichoice:
            self._list_widget = widgets.CheckList(
                question=self.job.question,
                options=self.job.options,
                focused=self.job.focused,
                autodetected_indexes=self.job.autodetected_indexes,
                on_accepted=self._handle_accepted,
            )
        else:
            self._list_widget = widgets.RadioList(
                question=self.job.question,
                options=self.job.options,
                focused=self.job.focused,
                autodetected_index=(
                    self.job.autodetected_indexes[0]
                    if self.job.autodetected_indexes else
                    None
                ),
                on_accepted=self._handle_accepted,
            )
        self._activity_indicator = widgets.ActivityIndicator()
        self.job.signal.register('dialog_updated', self._handle_dialog_updated)

        self.job.signal.register('autodetecting', self._handle_autodetecting)
        self.job.signal.register('autodetected', self._handle_autodetected)

        # Immediately hide the radiolist. Otherwise it flashes into view when
        # the job is started only to become hidden when the autodetect function
        # is called a few milliseconds later.
        self.job.signal.register('running', lambda _: self._activity_indicator.enable())

    def _handle_dialog_updated(self):
        self._list_widget.options = self.job.options
        self._list_widget.focused_index = self.job.focused_index
        if isinstance(self._list_widget, widgets.CheckList):
            self._list_widget.autodetected_indexes = self.job.autodetected_indexes
            self._list_widget.marked_indexes.update(self.job.autodetected_indexes)
        else:
            self._list_widget.autodetected_index = (
                self.job.autodetected_indexes[0]
                if self.job.autodetected_indexes else
                None
            )
        self.invalidate()

    def _handle_autodetecting(self):
        self._activity_indicator.enable()
        self.invalidate()

    def _handle_autodetected(self):
        self._activity_indicator.disable()
        self.invalidate()

    def _handle_accepted(self, choice):
        self.job.make_choice(choice)

    @functools.cached_property
    def runtime_widget(self):
        return HSplit(
            children=[
                ConditionalContainer(
                    content=self._activity_indicator,
                    filter=Condition(lambda: self._activity_indicator.active),
                ),
                ConditionalContainer(
                    content=self._list_widget,
                    filter=Condition(lambda: not self._activity_indicator.active),
                ),
            ],
        )


class TextFieldJobWidget(JobWidgetBase):

    is_interactive = True

    def setup(self):
        self._input_field = widgets.InputField(
            text=self.job.text,
            read_only=self.job.read_only,
            style='class:dialog.text',
            on_accepted=self._on_accepted,
        )
        self.job.signal.register('is_loading', self._handle_is_loading)
        self.job.signal.register('read_only', self._handle_read_only)
        self.job.signal.register('text', self._handle_text)

    def _handle_is_loading(self, is_loading):
        self._input_field.is_loading = is_loading
        self.invalidate()

    def _handle_read_only(self, read_only):
        self._input_field.read_only = read_only
        self.invalidate()

    def _handle_text(self, text):
        self._input_field.text = text
        self.invalidate()

    def _on_accepted(self, buffer):
        self.job.add_output(buffer.text)

    @functools.cached_property
    def runtime_widget(self):
        return self._input_field
