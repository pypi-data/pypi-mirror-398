import functools

from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl

from ....utils.types import SceneCheckResult
from .. import widgets
from . import JobWidgetBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class SceneSearchJobWidget(JobWidgetBase):

    is_interactive = False

    def setup(self):
        pass

    @functools.cached_property
    def runtime_widget(self):
        return None


class SceneCheckJobWidget(JobWidgetBase):

    is_interactive = True

    def setup(self):
        self._question = FormattedTextControl('')
        self._radiolist = widgets.RadioList()
        self._activity_indicator = widgets.ActivityIndicator(
            format='\n'.join((
                '{indicator} Checking for scene release',
                'Press <Ctrl-s n> to mark this as a non-scene release.',
            )),
            style='class:info',
            extend_width=True,
        )
        self.job.signal.register('running', lambda _: self._activity_indicator.enable())
        self.job.signal.register('finished', lambda _: self._activity_indicator.disable())
        self.job.signal.register('ask_release_name', self._ask_release_name)
        self.job.signal.register('ask_is_scene_release', self._ask_is_scene_release)

        @self.keybindings_global.add(
            'c-s', 'n',
            filter=Condition(lambda: self._question.text == ''),
        )
        def _(_event):
            if not self.job.is_finished:
                self.job.stop_checking()
                self.job.set_result(SceneCheckResult.false)

    def _ask_release_name(self, release_names):
        _log.debug('Asking for release name: %r', release_names)

        self._activity_indicator.active = False

        def handle_release_name(choice):
            _log.debug('Got release name: %r', choice)
            # Remove current question
            self._radiolist.options = ()
            self.invalidate()

            # Verify user choice
            self.job.user_selected_release_name(choice[1])
            self._activity_indicator.active = True

        self._radiolist.on_accepted = handle_release_name
        self._radiolist.options = [(release_name, release_name) for release_name in release_names]
        self._radiolist.options.append(('This is not a scene release', None))

        self._question.text = 'Pick the correct release name:'

        # We must tell the TUI to invalidate the job list because we are now
        # focusable, and the keypress focus may still be unset (keypresses are
        # ignored).
        self.job.signal.emit('refresh_ui')
        self.invalidate()

    def _ask_is_scene_release(self, is_scene_release):
        _log.debug('Confirming guess: %r', is_scene_release)

        self._activity_indicator.active = False

        def make_choice(choice):
            if choice:
                string = 'Yes'
                if is_scene_release is SceneCheckResult.true:
                    string += ' (autodetected)'
                return (string, SceneCheckResult.true)
            else:
                string = 'No'
                if is_scene_release is SceneCheckResult.false:
                    string += ' (autodetected)'
                return (string, SceneCheckResult.false)

        def handle_is_scene_release(choice):
            _log.debug('Got decision from user: %r', choice)
            self.job.set_result(choice[1])
            self.invalidate()

        self._radiolist.options = (make_choice(choice=True), make_choice(choice=False))
        self._radiolist.focused_option = make_choice(is_scene_release)
        self._radiolist.on_accepted = handle_is_scene_release

        self._question.text = 'Is this a scene release?'

        # We must tell the TUI to invalidate the job list because we are now
        # focusable, and the keypress focus may still be unset (keypresses are
        # ignored).
        self.job.signal.emit('refresh_ui')
        self.invalidate()

    @functools.cached_property
    def runtime_widget(self):
        return HSplit(
            children=[
                ConditionalContainer(
                    filter=Condition(lambda: self._activity_indicator.active),
                    content=self._activity_indicator,
                ),
                ConditionalContainer(
                    filter=Condition(lambda: bool(self._radiolist.options)),
                    content=HSplit(
                        children=[
                            Window(self._question),
                            self._radiolist,
                        ],
                    ),
                ),
            ],
        )
