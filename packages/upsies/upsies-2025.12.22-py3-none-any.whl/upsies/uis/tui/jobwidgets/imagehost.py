import functools

from .. import widgets
from . import JobWidgetBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class ImagehostJobWidget(JobWidgetBase):

    is_interactive = False

    def setup(self):
        self._upload_progress = widgets.ProgressBar()
        self.job.signal.register('output', self.handle_image_url)
        self.job.signal.register('error', lambda _: self.invalidate())
        self.job.signal.register('finished', lambda _: self.invalidate())

    def handle_image_url(self, url):
        if self.job.images_total > 0:
            self._upload_progress.percent = self.job.images_uploaded / self.job.images_total * 100
            self.invalidate()

    @functools.cached_property
    def runtime_widget(self):
        return self._upload_progress
