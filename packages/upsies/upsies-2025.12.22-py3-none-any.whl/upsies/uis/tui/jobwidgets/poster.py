import functools

from .... import utils
from .. import widgets
from . import JobWidgetBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class PosterJobWidget(JobWidgetBase):

    is_interactive = True

    def setup(self):
        self._activity_indicator = widgets.ActivityIndicator(
            style='class:info',
            extend_width=True,
        )
        self.job.signal.register('running', lambda _: self._activity_indicator.enable())
        self.job.signal.register('finished', lambda _: self._activity_indicator.disable())

        self.job.signal.register('downloading', self.handle_downloading)
        self.job.signal.register('resizing', self.handle_resizing)
        self.job.signal.register('uploading', self.handle_uploading)

    def handle_downloading(self, url):
        self._activity_indicator.format = f'{{indicator}} Downloading {url}'

    def handle_resizing(self, filepath):
        self._activity_indicator.format = f'{{indicator}} Resizing {utils.fs.basename(filepath)}'

    def handle_uploading(self, imagehost):
        self._activity_indicator.format = f'{{indicator}} Uploading to {imagehost.name}'

    @functools.cached_property
    def runtime_widget(self):
        return self._activity_indicator
