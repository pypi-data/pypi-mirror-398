import abc
import functools

from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import ConditionalContainer, DynamicContainer, HSplit, Window, to_container
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import walk

from ... import prompts
from .. import widgets

import logging  # isort:skip
_log = logging.getLogger(__name__)


class JobWidgetBase(abc.ABC):
    """User-interaction and information display for :class:`~.jobs.JobBase` instance"""

    _empty_widget = Window(
        dont_extend_height=True,
        style='class:info',
    )

    def __init__(self, job, app):
        self._job = job
        self._app = app
        self._prompts = []
        self.setup()

        self.job.signal.register('info', lambda _: self.invalidate())
        self.job.signal.register('warning', lambda _: self.invalidate())
        self.job.signal.register('prompt', self.add_prompt)

        main_widget = HSplit(
            children=[
                # Status information or user interaction
                ConditionalContainer(
                    filter=Condition(lambda: not self.job.is_finished),
                    content=self._prompt_or_runtime_widget,
                ),
                # Ephemeral info message that is only shown while job is running
                ConditionalContainer(
                    filter=Condition(lambda: not self.job.is_finished and bool(self.job.info)),
                    content=self.info_widget,
                ),
                # Warnings
                ConditionalContainer(
                    filter=Condition(lambda: bool(self.job.warnings)),
                    content=self.warnings_widget,
                ),
                # Output
                ConditionalContainer(
                    filter=Condition(lambda: self.job.output),
                    content=self.output_widget,
                ),
                # Errors
                ConditionalContainer(
                    filter=Condition(lambda: bool(self.job.errors)),
                    content=self.errors_widget,
                ),
            ],
        )

        label = widgets.HLabel(
            group='jobs',
            text=self.job.label,
            style='class:label',
            content=main_widget,
        )

        self._container = ConditionalContainer(
            filter=Condition(lambda: (
                self.job.errors or self.job.warnings
                or (
                    # Don't display job if it's hidden. (Duh.)
                    not self.job.hidden
                    # If job was terminated, it means something went wrong and we don't want to
                    # display any widgets. Note that we shouldn't use `job.output` here because it
                    # may be empty (`no_output_is_ok=True`).
                    and not self.job.is_terminated
                )
            )),
            content=label,
        )

    @property
    def job(self):
        """Underlying :class:`~.JobBase` instance"""
        return self._job

    @abc.abstractmethod
    def setup(self):
        """
        Called on object creation

        Create widgets and register :attr:`job` callbacks.
        """

    @property
    @abc.abstractmethod
    def runtime_widget(self):
        """
        Interactive or status widget that is displayed while this job is running

        :return: :class:`~.prompt_toolkit.layout.containers.Window` object or
            `None`
        """

    @functools.cached_property
    def _runtime_widget_with_local_keybindings(self):
        if self.runtime_widget:
            container = to_container(self.runtime_widget)
            container.key_bindings = self.keybindings_local
            return container

    @functools.cached_property
    def _prompt_or_runtime_widget(self):
        def get_content():
            if self.current_prompt_widget:
                return self.current_prompt_widget
            elif self._runtime_widget_with_local_keybindings:
                return self._runtime_widget_with_local_keybindings
            else:
                return self._empty_widget

        return DynamicContainer(get_content)

    @property
    def output_widget(self):
        """
        Job :attr:`~.JobBase.output`

        :return: :class:`~.prompt_toolkit.layout.containers.Window` object
        """

        def join_output(job=self.job):
            output = job.output
            if all(
                    (
                        # Maximum length for comma-separated output.
                        len(o) <= 12
                        # Don't use ", " as separator if the output itself contains ",".
                        and ',' not in str(o)
                    )
                    for o in output
            ):
                joined = ', '.join(output)
            else:
                # Newline-separated output.
                joined = '\n'.join(output)

            # FIXME: If output is empty, prompt-toolkit ignores the
            #        "dont_extend_height" argument. Using a space (0x20) as a
            #        placeholder seems to prevent this issue.
            #
            #        WARNING: The bug also manifests if output is ("",) (i.e. a
            #        non-empty list containing one or more empty strings), which
            #        evaluates as `True`, so `if job.output` doesn't work.
            return joined or ' '

        return Window(
            style='class:output',
            content=FormattedTextControl(join_output),
            dont_extend_height=True,
            wrap_lines=True,
        )

    @property
    def info_widget(self):
        """
        :attr:`~.JobBase.info` that is only displayed while this job is running

        :return: :class:`~.prompt_toolkit.layout.containers.Window` object
        """
        return Window(
            style='class:info',
            content=FormattedTextControl(lambda: str(self.job.info)),
            dont_extend_height=True,
            wrap_lines=True,
        )

    @property
    def warnings_widget(self):
        """
        Any :attr:`~.JobBase.warnings`

        :return: :class:`~.prompt_toolkit.layout.containers.Window` object
        """
        return Window(
            style='class:warning',
            content=FormattedTextControl(lambda: '\n'.join(str(e) for e in self.job.warnings)),
            dont_extend_height=True,
            wrap_lines=True,
        )

    @property
    def errors_widget(self):
        """
        Any :attr:`~.JobBase.errors`

        :return: :class:`~.prompt_toolkit.layout.containers.Window` object
        """
        return Window(
            style='class:error',
            content=FormattedTextControl(lambda: '\n'.join(str(e) for e in self.job.errors)),
            dont_extend_height=True,
            wrap_lines=True,
        )

    def add_prompt(self, prompt):
        self._prompts.append(prompt)
        self._clear_cached_prompt_widget()

    @functools.cached_property
    def current_prompt_widget(self):
        if self._prompts:
            current_prompt = self._prompts[0]
            return self._prompt_widget_factory(
                current_prompt,
                callback=self._handle_prompt_accepted,
            )

    def _prompt_widget_factory(self, prompt, callback):
        if isinstance(prompt, prompts.RadioListPrompt):
            return widgets.RadioList(
                question=prompt.parameters['question'],
                options=prompt.parameters['options'],
                focused=prompt.parameters['focused'],
                on_accepted=callback,
            )
        elif isinstance(prompt, prompts.CheckListPrompt):
            return widgets.CheckList(
                question=prompt.parameters['question'],
                options=prompt.parameters['options'],
                focused=prompt.parameters['focused'],
                on_accepted=callback,
            )
        elif isinstance(prompt, prompts.TextPrompt):
            input_field = widgets.InputField(
                text=prompt.parameters['text'],
                on_accepted=lambda buffer: callback(buffer.text),
                style='class:dialog.text',
            )
            # The question or prompt message is optional, but HLabel always puts
            # space between the question and the input field. This looks like
            # the input field is weirdly indented if the question is empty.
            if prompt.parameters['question']:
                return widgets.HLabel(
                    text=prompt.parameters['question'],
                    content=input_field,
                    style='class:dialog.label',
                )
            else:
                return input_field
        else:
            raise ValueError(f'Unsupported prompt: {type(prompt).__name__!r}: {prompt!r}')

    def _clear_cached_prompt_widget(self):
        try:
            del self.current_prompt_widget
        except AttributeError:
            pass
        self.invalidate()

    def _handle_prompt_accepted(self, result):
        current_prompt = self._prompts[0]
        self._prompts.remove(current_prompt)
        self._clear_cached_prompt_widget()
        current_prompt.set_result(result)

    @functools.cached_property
    def is_interactive(self):
        """
        Whether this job may require user interaction at any point

        Subclasses should hardcode this as a class attribute to `True` or
        `False`. The default implementation tries to guess interactivity by
        finding a focusable widget. This is expensive and can be inaccurate
        because widgets come and go.
        """
        for c in walk(to_container(self._prompt_or_runtime_widget), skip_hidden=True):
            if isinstance(c, Window) and c.content.is_focusable():
                return True
        return False

    @functools.cached_property
    def keybindings_global(self):
        """
        Application-wide :class:`prompt_toolkit.key_binding.KeyBindings` instance

        These keybindings are always active as long as the TUI is running,
        regardless of which widget is focused. This also makes it possible to
        bind keys for unfocusable wigets.

        To keep things tidy and intuitive, all keybindings should be sequences
        of multiple keys. The first key should always start with ``c-<x>`` where
        ``c`` stands for ``Control`` and ``<x>`` is a character that is
        associated with the job's :attr:`~.JobBase.label`.

        For example, :class:`~.CreateTorrentJob` keybindings start with ``c-t``
        and :class:`~.SceneCheckJob` keybindings start with ``c-s``.
        """
        return self._app.key_bindings

    @functools.cached_property
    def keybindings_local(self):
        """
        Widget-wide :class:`prompt_toolkit.key_binding.KeyBindings` instance

        These keybindings are only active as long as this widget is focused. If
        there are conflicts, local keybindings take precedence over
        :attr:`global keybindings <keybindings_global>`.
        """
        return KeyBindings()

    def invalidate(self):
        """Schedule redrawing of the TUI"""
        try:
            del self.is_interactive
        except AttributeError:
            pass

        self._app.invalidate()

    def __pt_container__(self):
        return self._container
