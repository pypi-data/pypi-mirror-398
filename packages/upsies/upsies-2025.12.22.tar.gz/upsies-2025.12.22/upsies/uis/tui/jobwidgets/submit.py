import functools

from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit

from .... import __project_name__, errors
from .. import widgets
from . import JobWidgetBase


class SubmitJobWidget(JobWidgetBase):

    is_interactive = False

    def setup(self):
        # Extend some error messages with additional information specific to this UI,
        # e.g. "use --option to fix this".
        self.job.signal.register('error', self._handle_error)

        # Indicate uploading acitivity.
        self._activity_indicator = widgets.ActivityIndicator(
            style='class:info',
            format='{indicator} Uploading',
            extend_width=False,

        )
        self._activity_indicator.disable()
        self.job.signal.register('submitting', lambda: self._activity_indicator.enable())
        self.job.signal.register('submitted', lambda _: self._activity_indicator.disable())
        self.job.signal.register('finished', lambda _: self._activity_indicator.disable())

    def _handle_error(self, error):
        if isinstance(error, errors.AnnounceUrlNotSetError):
            cmd = f'{__project_name__} set trackers.{error.tracker.name}.announce_url <URL>'
            self.job.error(f'Set it with this command: {cmd}')

        elif isinstance(error, errors.FoundDupeError):
            self.job.error('You can override the dupe check with --ignore-dupes.')

    @functools.cached_property
    def runtime_widget(self):
        return HSplit(
            children=[
                ConditionalContainer(
                    filter=Condition(lambda: self._activity_indicator.active),
                    content=self._activity_indicator,
                ),
            ],
        )
