import functools

from prompt_toolkit.layout.containers import DynamicContainer, HSplit, VSplit

from .... import utils
from .. import widgets
from . import JobWidgetBase


class BdinfoJobWidget(JobWidgetBase):

    is_interactive = False

    def setup(self):
        self._activity_indicator = widgets.ActivityIndicator(
            style='class:info',
            extend_width=False,
        )
        self._bdinfo_progress_widgets = {}

        self.job.siblings['playlists'].signal.register('playlists_selected', self.handle_playlists_selected)
        self.job.signal.register('bdinfo_progress', self.handle_bdinfo_progress)
        self.job.signal.register('running', lambda _: self._activity_indicator.enable())
        self.job.signal.register('finished', lambda _: self._activity_indicator.disable())

    def handle_playlists_selected(self, discpath, playlists):
        # Add progress info widgets for each playlist.
        for playlist in playlists:
            label = playlist.label
            if label not in self._bdinfo_progress_widgets:
                self._bdinfo_progress_widgets[label] = BdinfoProgressWidget(label)

    def handle_bdinfo_progress(self, progress):
        self._bdinfo_progress_widgets[progress.playlist.label].update(progress)
        self.invalidate()

    @functools.cached_property
    def runtime_widget(self):
        return DynamicContainer(self.get_runtime_widgets)

    def get_runtime_widgets(self):
        if not self._bdinfo_progress_widgets:
            # Show activity indicator if no BDInfo report generation has started yet.
            self._activity_indicator.enable()
            return self._activity_indicator
        else:
            self._activity_indicator.disable()
            return HSplit(self._bdinfo_progress_widgets.values())


class BdinfoProgressWidget:

    _instances = []

    def __new__(cls, *_args, **_kwargs):
        self = super().__new__(cls)
        cls._instances.append(self)
        return self

    def __init__(self, label):
        self._label = str(label)
        self._activity_indicator = widgets.ActivityIndicator()
        self._bar = widgets.ProgressBar(width=30)
        self._label_widget = widgets.TextField(text=lambda: self.label_padded, extend_width=False)
        self._time_elapsed = utils.types.Timestamp(0)
        self._time_elapsed_widget = widgets.TextField(lambda: str(self._time_elapsed), extend_width=False)
        self._time_remaining = utils.types.Timestamp(0)
        self._time_remaining_widget = widgets.TextField(lambda: str(self._time_remaining), extend_width=False)
        self._container = VSplit(
            children=[
                self._label_widget,
                DynamicContainer(self._get_progress_widgets),
            ],
            style='class:info',
            width=lambda: self.label_width + len(' 0:00:10                                0:01:30'),
        )

    def _get_progress_widgets(self):
        if self.is_waiting_for_first_progress:
            # Show activity indicator if no bdinfo is currently generated and this instance is
            # next in line.
            return VSplit([
                widgets.hspacer,
                self._activity_indicator,
            ])

        elif 0 < self._bar.percent < 100:
            # Show progress if report is being generated.
            return VSplit([
                widgets.hspacer,
                self._time_elapsed_widget,
                widgets.hspacer,
                self._bar,
                widgets.hspacer,
                self._time_remaining_widget,
            ])
        elif self._bar.percent >= 100:
            # Report generation is done.
            return VSplit([
                widgets.hspacer,
                widgets.TextField('✔', extend_width=False),
            ])
        else:
            return widgets.hspacer

    @property
    def is_waiting_for_first_progress(self):
        prev_instance = None
        for instance in type(self)._instances:
            if (
                    instance is self
                    # Report generation hasn't started/finished yet.
                    and instance.percent <= 0
                    # Previous instance finished or this is the first instance.
                    and (
                        prev_instance is None
                        or prev_instance.percent >= 100
                    )
            ):
                self._activity_indicator.enable()
                return True

            prev_instance = instance

        return False

    def update(self, progress):
        self.percent = progress.percent
        self.time_elapsed = progress.time_elapsed
        self.time_remaining = progress.time_remaining

    @property
    def label(self):
        return self._label

    @property
    def label_padded(self):
        return self.label.rjust(self.label_width)

    @property
    def label_width(self):
        return max(
            len(instance.label)
            for instance in type(self)._instances
        )

    @property
    def percent(self):
        return self._bar.percent

    @percent.setter
    def percent(self, percent):
        self._bar.percent = percent
        self._activity_indicator.disable()

    @property
    def time_elapsed(self):
        return self._time_elapsed

    @time_elapsed.setter
    def time_elapsed(self, time_elapsed):
        self._time_elapsed = utils.types.Timestamp(time_elapsed)

    @property
    def time_remaining(self):
        return self._time_remaining

    @time_remaining.setter
    def time_remaining(self, time_remaining):
        self._time_remaining = utils.types.Timestamp(time_remaining)

    def __pt_container__(self):
        return self._container
