import functools

from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit

from .. import widgets
from . import JobWidgetBase


class CustomJobWidget(JobWidgetBase):

    def setup(self):
        self._activity_indicator = widgets.ActivityIndicator(
            style='class:info',
            extend_width=False,
        )
        # Deactivate activity indicator if we have output, which means the job is done.
        self.job.signal.register('running', lambda _: self._activity_indicator.enable())
        self.job.signal.register('prompt', lambda _: self._activity_indicator.disable())
        self.job.signal.register('output', lambda _: self._activity_indicator.disable())
        self.job.signal.register('finished', lambda _: self._activity_indicator.disable())
        self.job.signal.register('indicate_activity', self._indicate_activity)

    def _indicate_activity(self, indicate_activity, text):
        if indicate_activity is not None:
            self._activity_indicator.active = indicate_activity
        if text is not None:
            self._activity_indicator.format = f'{{indicator}} {text}'
        self.invalidate()

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
