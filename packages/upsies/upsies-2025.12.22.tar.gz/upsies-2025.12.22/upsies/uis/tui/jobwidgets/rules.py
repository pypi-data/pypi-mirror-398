import functools

from .... import errors
from . import JobWidgetBase


class RulesJobWidget(JobWidgetBase):

    def setup(self):
        self.job.signal.register('error', self._handle_error)

    def _handle_error(self, error):
        if isinstance(error, errors.RuleBroken):
            self.job.error('You can override rule checks with --ignore-rules.')

    @functools.cached_property
    def runtime_widget(self):
        return None
