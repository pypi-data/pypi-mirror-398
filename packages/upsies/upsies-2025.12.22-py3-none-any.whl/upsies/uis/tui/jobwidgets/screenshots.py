import functools

from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit

from .. import widgets
from . import JobWidgetBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class ScreenshotsJobWidget(JobWidgetBase):

    is_interactive = False

    def setup(self):
        self._activity_indicator = widgets.ActivityIndicator(
            format='{indicator}',
            style='class:info',
            extend_width=False,
        )
        self._screenshot_progress = widgets.ProgressBar()
        self.job.signal.register('output', self.handle_screenshot_path)
        self.job.signal.register('running', lambda _: self._activity_indicator.enable())
        self.job.signal.register('finished', lambda _: self._activity_indicator.disable())

    def handle_screenshot_path(self, path):
        self._activity_indicator.disable()
        self.invalidate()

        if self.job.screenshots_total > 0:
            self._screenshot_progress.percent = self.job.screenshots_created / self.job.screenshots_total * 100

    @functools.cached_property
    def runtime_widget(self):
        return HSplit(
            children=[
                ConditionalContainer(
                    filter=Condition(lambda: self._activity_indicator.active),
                    content=self._activity_indicator,
                ),
                ConditionalContainer(
                    filter=Condition(lambda: not self._activity_indicator.active),
                    content=self._screenshot_progress,
                ),
            ],
        )
