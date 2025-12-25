import functools
import os

from .. import widgets
from . import JobWidgetBase


class MediainfoJobWidget(JobWidgetBase):

    is_interactive = False

    def setup(self):
        self._activity_indicator = widgets.ActivityIndicator(
            style='class:info',
            extend_width=False,
        )
        self.job.signal.register('generating_report', self.handle_generating_report)
        self.job.signal.register('generated_report', self.handle_generated_report)
        self.job.signal.register('running', lambda _: self._activity_indicator.enable())
        self.job.signal.register('finished', lambda _: self._activity_indicator.disable())

    def handle_generating_report(self, video_filepath):
        # Display the path relative to the user-provided content path. Keep in mind that
        # `content_path` might be relative or have no parent directory.
        common_path = os.path.commonpath((self.job.content_path, video_filepath))
        relative_path = video_filepath[len(common_path):].strip(os.sep)
        self._activity_indicator.format = f'{{indicator}} {relative_path}'

    def handle_generated_report(self, video_filepath, report):
        # Remove file path from activity indicator in case we are waiting for the user to select
        # more playlists.
        self._activity_indicator.format = '{indicator}'

    @functools.cached_property
    def runtime_widget(self):
        return self._activity_indicator
