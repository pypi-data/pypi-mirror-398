"""
Custom TUI widgets
"""

import asyncio
import collections
import itertools
import textwrap

from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import ANSI, to_formatted_text
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension

import logging  # isort:skip
_log = logging.getLogger(__name__)


hspacer = Window(FormattedTextControl(' '), dont_extend_width=True, dont_extend_height=True)
vspacer = Window(FormattedTextControl(''), dont_extend_width=True, dont_extend_height=True)


class TextField:
    """Single line of non-editable text"""

    def __init__(self, text='', *, width=None, height=1, extend_width=True, style=''):
        self._text = text
        self._width = width
        self._height = height
        self._activity_indicator = ActivityIndicator(callback=self.set_text)
        self.container = Window(
            content=FormattedTextControl(lambda: self.text),
            width=width,
            height=height,
            dont_extend_height=True,
            dont_extend_width=not extend_width,
            wrap_lines=True,
            style=style,
        )

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self.set_text(text)

    def set_text(self, text):
        if isinstance(self._width, int) and self._width > 1:
            width = self._width
            if isinstance(self._height, int):
                height = self._height
            else:
                height = None

            if height == 1:
                # Remove newlines. Don't do word wrapping to avoid replacing
                # long words with "…" with lots of available free space.
                self._text = text.replace('\n', ' ')
            else:
                # prompt_toolkit has no support for word wrapping.
                paragraphs = text.split('\n')
                self._text = '\n\n'.join(textwrap.fill(
                    paragraph,
                    width=width,
                    max_lines=height,
                    placeholder='…',
                ) for paragraph in paragraphs)

        else:
            self._text = text

        get_app().invalidate()

    @property
    def is_loading(self):
        """Whether an activity indicator is displayed"""
        return self._activity_indicator.active

    @is_loading.setter
    def is_loading(self, is_loading):
        self._activity_indicator.active = is_loading

    def __pt_container__(self):
        return self.container


class InputField:
    """Single line of user-editable text"""

    def __init__(self, text='', *, width=None, extend_width=True, read_only=False,
                 on_accepted=None, on_changed=None, style=''):
        self._activity_indicator = ActivityIndicator()
        self.read_only = read_only
        self.on_accepted = on_accepted
        self.buffer = Buffer(
            multiline=False,
            accept_handler=self._accept_handler,
            on_text_changed=on_changed,
            read_only=Condition(lambda: self.read_only),
        )
        self.container = VSplit(
            children=[
                ConditionalContainer(
                    filter=Condition(lambda: self._activity_indicator.active),
                    content=VSplit([
                        self._activity_indicator,
                        hspacer,
                    ]),
                ),
                Window(
                    content=BufferControl(self.buffer),
                    always_hide_cursor=Condition(lambda: self.read_only),
                    width=width,
                    dont_extend_height=True,
                    dont_extend_width=not extend_width,
                ),
            ],
            style=style,
        )
        if text:
            self.set_text(text, ignore_callback=True)

    def _accept_handler(self, buffer):
        if self.on_accepted:
            self.on_accepted(buffer)
        # Do not clear input field on enter
        return True

    @property
    def text(self):
        return self.buffer.text

    @text.setter
    def text(self, text):
        self.set_text(text)

    def set_text(self, text, *, ignore_callback=False, preserve_cursor_position=False):
        if preserve_cursor_position:
            curpos = self.buffer.cursor_position

        if ignore_callback:
            handlers = self.buffer.on_text_changed._handlers
            self.buffer.on_text_changed._handlers = []

        self.buffer.set_document(Document(text), bypass_readonly=True)

        if ignore_callback:
            self.buffer.on_text_changed._handlers = handlers

        if preserve_cursor_position:
            self.buffer.cursor_position = curpos

    @property
    def read_only(self):
        return self._read_only

    @read_only.setter
    def read_only(self, read_only):
        self._read_only = bool(read_only)

    @property
    def is_loading(self):
        """Whether an activity indicator is displayed"""
        return self._activity_indicator.active

    @is_loading.setter
    def is_loading(self, is_loading):
        self._activity_indicator.active = is_loading

    def __pt_container__(self):
        return self.container


class RadioList:
    """
    List of options from which the user can select one

    :param options: Sequence of options the user can make
    :param question: Text that is displayed above the `options` or any falsy
        value
    :param focused: Focused index or option or `None` to focus the first option
    :param on_accepted: Callback that gets the user choice

    Each option item must be a :class:`str` or a sequence with one or more
    items. The first item is presented to the user. `on_accepted` gets the
    complete option item.
    """

    def __init__(self, options=(), question=None, focused=None, autodetected_index=None, on_accepted=None):
        self.options = options
        self.question = question
        self.on_accepted = on_accepted
        self.autodetected_index = autodetected_index

        if isinstance(focused, int):
            # It seems prompt-toolkit can't handle negative indexes.
            if focused < 0:
                self.focused_index = len(options) + focused
            else:
                self.focused_index = focused
        elif focused:
            self.focused_index = options.index(focused)
        else:
            self.focused_index = 0

        kb = KeyBindings()

        @kb.add('up')
        @kb.add('c-p')
        @kb.add('k')
        @kb.add('s-tab')
        def _(_event):
            self.focused_index = max(0, self.focused_index - 1)

        @kb.add('down')
        @kb.add('c-n')
        @kb.add('j')
        @kb.add('tab')
        def _(_event):
            self.focused_index = min(len(self.options) - 1, self.focused_index + 1)

        @kb.add('enter')
        @kb.add('c-j')
        def _(_event):
            if self.on_accepted is not None:
                try:
                    self.on_accepted(self.options[self.focused_index])
                except IndexError as e:
                    raise RuntimeError(f'No option at index {self.focused_index}: {self.options}') from e

        choices = Window(
            content=FormattedTextControl(
                self._get_text_fragments,
                key_bindings=kb,
                focusable=True,
            ),
            dont_extend_height=True,
            always_hide_cursor=True,
        )

        self.container = HSplit(
            children=[
                choices,
            ],
            style='class:dialog.choice',
        )

        if self.question:
            self.container.children.insert(0, Window(FormattedTextControl([
                ('bold', self.question),
            ])))

    @property
    def focused_option(self):
        """Currently focused item in :attr:`options`"""
        return self.options[self.focused_index]

    @focused_option.setter
    def focused_option(self, option):
        if option not in self.options:
            raise ValueError(f'No such option: {option!r}')
        else:
            self.focused_index = self.options.index(option)

    def _get_text_fragments(self):
        fragments = []
        if not self.options:
            return fragments

        def option_as_string(option):
            if isinstance(option, str):
                return option
            elif isinstance(option, collections.abc.Sequence):
                return str(option[0])
            else:
                raise RuntimeError(f'Invalid option value: {option!r}')

        width = max(len(option_as_string(option)) for option in self.options)
        for i, option in enumerate(self.options):
            option_string = option_as_string(option)
            if i == self.focused_index:
                style = 'class:dialog.choice.focused'
                fragments.append(('[SetCursorPosition]', ''))
                fragments.append((style, ' \N{BLACK CIRCLE}'))
            else:
                style = 'class:dialog.choice'
                fragments.append((style, '  '))
            fragments.append((style, ' '))
            fragments.extend(to_formatted_text(option_string.ljust(width) + ' ', style=style))
            if i == self.autodetected_index:
                fragments.append(('class:dialog.choice', ' (autodetected)'))
            fragments.append(('', '\n'))

        fragments.pop()  # Remove last newline

        return fragments

    def __pt_container__(self):
        return self.container


class CheckList:
    """
    List of options from which the user can select multiple

    :param options: Sequence of options the user can make
    :param question: Text that is displayed above the `options` or any falsy
        value
    :param focused: Focused index or option or `None` to focus the first option
    :param on_accepted: Callback that gets the ticked options

    Each option item must be a :class:`str` or a sequence with one or more
    items. The first item is presented to the user. `on_accepted` gets the
    complete option item.
    """

    def __init__(self, options=(), question=None, focused=None, autodetected_indexes=(), on_accepted=None):
        self.options = tuple(options)
        self.question = str(question) if question else ''
        self.on_accepted = on_accepted

        if isinstance(focused, int):
            # It seems prompt-toolkit can't handle negative indexes.
            if focused < 0:
                self.focused_index = len(options) + focused
            else:
                self.focused_index = focused
        elif focused:
            self.focused_index = options.index(focused)
        else:
            self.focused_index = 0

        self.marked_indexes = set(autodetected_indexes)
        self.autodetected_indexes = set(autodetected_indexes)

        kb = KeyBindings()

        @kb.add('up')
        @kb.add('c-p')
        @kb.add('k')
        @kb.add('s-tab')
        def _(_event):
            self.focused_index = max(0, self.focused_index - 1)

        @kb.add('down')
        @kb.add('c-n')
        @kb.add('j')
        @kb.add('tab')
        def _(_event):
            self.focused_index = min(len(self.options) - 1, self.focused_index + 1)

        @kb.add(' ')
        def _(_event):
            if self.focused_index in self.marked_indexes:
                self.marked_indexes.remove(self.focused_index)
            else:
                self.marked_indexes.add(self.focused_index)
            self.focused_index = min(len(self.options) - 1, self.focused_index + 1)

        @kb.add('enter')
        @kb.add('c-j')
        def _(_event):
            if self.on_accepted is not None:
                self.on_accepted(self.marked_options)

        self.container = HSplit(
            children=[
                Window(
                    content=FormattedTextControl(
                        self._get_text_fragments,
                        key_bindings=kb,
                        focusable=True,
                    ),
                    dont_extend_height=True,
                    dont_extend_width=True,
                    always_hide_cursor=True,
                ),
            ],
            style='class:dialog.choice',
        )

        if self.question:
            self.container.children.insert(0, Window(FormattedTextControl([
                ('bold', self.question),
            ])))

    @property
    def marked_options(self):
        """Currently marked items in :attr:`options`"""
        return tuple(
            option
            for index, option in enumerate(self.options)
            if index in self.marked_indexes
        )

    def _get_text_fragments(self):
        fragments = []
        if not self.options:
            return fragments

        def option_as_string(option):
            if isinstance(option, str):
                return option
            elif isinstance(option, collections.abc.Sequence):
                return str(option[0])
            else:
                raise RuntimeError(f'Invalid option value: {option!r}')

        width = max(len(option_as_string(option)) for option in self.options)
        for i, option in enumerate(self.options):
            option_string = option_as_string(option)
            if i == self.focused_index:
                style = 'class:dialog.choice.focused'
                fragments.append(('[SetCursorPosition]', ''))
            else:
                style = 'class:dialog.choice'

            if i in self.marked_indexes:
                fragments.append((style, ' \N{FISHEYE} '))
            else:
                fragments.append((style, ' \N{WHITE CIRCLE} '))

            fragments.append((style, ' '))
            fragments.extend(to_formatted_text(option_string.ljust(width) + ' ', style=style))
            if i in self.autodetected_indexes:
                fragments.append(('class:dialog.choice', ' (autodetected)'))

            fragments.append(('', '\n'))

        fragments.pop()  # Remove last newline
        return fragments

    def __pt_container__(self):
        return self.container


class HLabel:
    _groups = collections.defaultdict(list)

    def __init__(self, text, content, group=None, style=''):
        self.label = Window(
            content=FormattedTextControl(text),
            dont_extend_width=True,
            dont_extend_height=True,
            align=WindowAlign.RIGHT,
        )
        self.container = VSplit(
            [
                # Apply `style` to label text and spacer for background color.
                VSplit([self.label, hspacer], style=style),
                content,
            ],
        )

        self._group = group
        if group is not None:
            self._groups[group].append(self)
            texts = [label.label.content.text for label in self._groups[group]]
            max_width = max(len(text) for text in texts)
            for label in self._groups[group]:
                label.label.width = max_width + 1

    def __pt_container__(self):
        return self.container


class VLabel:
    def __init__(self, text, content, style=''):
        self.container = HSplit([
            Window(
                FormattedTextControl(text=text),
                dont_extend_width=False,
                dont_extend_height=True,
                style=style,
            ),
            content,
        ])

    def __pt_container__(self):
        return self.container


class ProgressBar:
    def __init__(self, text='', width=None):
        self.percent = 0
        self.container = VSplit(
            children=[
                Window(
                    style='class:info.progressbar.progress',
                    width=lambda: Dimension(weight=int(max(0, self.percent))),
                    height=1,
                ),
                Window(
                    style='class:info.progressbar',
                    width=lambda: Dimension(weight=int(100 - min(100, self.percent))),
                    height=1,
                ),
            ],
            width=(
                Dimension(min=10, max=60, preferred=30)
                if width is None else
                Dimension.exact(width)
            ),
        )

    @property
    def percent(self):
        return self._percent

    @percent.setter
    def percent(self, value):
        self._percent = float(value)

    def __pt_container__(self):
        return self.container


class ActivityIndicator:
    """
    Activity indicator that cycles through a sequence of strings

    :param callable callback: Callable that receives a single string from
        `states` as a positional argument
    :param states: Sequence of strings that are cycled through and passed to
        `callback` individually
    :param float interval: Delay between calls to `callback`
    :param str format: See :attr:`format`
    :param str style: prompt-toolkit style
    :param bool extend_width: Whether to maximize horizontally
    """

    def __init__(self, *, callback=None, states=('⠷', '⠯', '⠟', '⠻', '⠽', '⠾'),
                 interval=0.3, format='{indicator}', style='', extend_width=False):
        self._iterator = itertools.cycle(states)
        self._interval = float(interval)
        self._callback = callback or None
        self._format = format
        self._text = self._format.format(indicator=next(self._iterator))
        self._iterate_task = None

        self.container = Window(
            content=FormattedTextControl(lambda: self.text),
            dont_extend_height=True,
            dont_extend_width=not extend_width,
            style=style,
        )

    @property
    def active(self):
        """
        Whether :attr:`text` is continuously updated and `callback` called

        .. note:: This updates :attr:`text` in an asynchronous task. If you
            try to set this attribute outside of an asynchronous context, you
            get ``RuntimeError: no running event loop``.
        """
        return bool(self._iterate_task)

    @active.setter
    def active(self, active):
        if active:
            if not self._iterate_task:
                self._iterate_task = asyncio.get_running_loop().create_task(self._iterate())
        elif self._iterate_task:
            self._iterate_task.cancel()
            self._iterate_task = None

    def enable(self):
        """Calling this method sets :attr:`active` to `True`"""
        self.active = True

    def disable(self):
        """Calling this method sets :attr:`active` to `False`"""
        self.active = False

    @property
    def format(self):
        """
        Format string

        ``{indicator}`` is replaced with the current state in `states`.
        """
        return self._format

    @format.setter
    def format(self, format):
        self._format = format

    @property
    def text(self):
        """Formatted :attr:`format` string"""
        return self._text

    async def _iterate(self):
        while True:
            self._text = self._format.format(indicator=next(self._iterator))
            get_app().invalidate()

            if self._callback:
                self._callback(self._text)

            await asyncio.sleep(self._interval)

    def __pt_container__(self):
        return self.container


class Image:
    def __init__(self, bytes=b'', width=None, height=None):
        self._activity_indicator = ActivityIndicator()
        self._width = width
        self._height = height
        self.container = VSplit(
            children=[
                ConditionalContainer(
                    filter=Condition(lambda: self.is_loading),
                    content=self._activity_indicator,
                ),
                ConditionalContainer(
                    filter=Condition(lambda: not self.is_loading),
                    content=Window(
                        content=FormattedTextControl(lambda: self._image),
                        dont_extend_height=True,
                        dont_extend_width=True,
                    ),
                ),
            ],
        )

        self.is_loading = False
        self.set_image_bytes(bytes)

    def set_image_bytes(self, bytes):
        if bytes:
            import io

            import PIL
            import term_image.image

            # Prevent DecompressionBombWarning: Image size (... pixels) exceeds
            # limit of ... pixels, could be decompression bomb DOS attack.
            # This happens when a poster is very large.
            PIL.Image.MAX_IMAGE_PIXELS = None

            escape_codes = str(
                # FIXME: This hack doesn't work with KittyImage
                # objects. Probably because the ANSI class doesn't know the
                # kitty graphics protocol and interprets the escape sequences as
                # normal text. To fix this, we always use BlockImage, even on
                # more capable terminals.
                term_image.image.BlockImage(
                    PIL.Image.open(io.BytesIO(bytes)),
                    width=self._width,
                    height=self._height,
                )
            )
        else:
            escape_codes = ''
        self._image = ANSI(escape_codes)

    # Add `text` property like InputField, TextField, etc. This is useful for
    # WebDbSearchJobWidget, which handles a lot of widgets. Avoiding a special
    # case for the poster widget makes things a lot simpler.
    @property
    def text(self):
        return self._image

    @text.setter
    def text(self, bytes):
        self.set_image_bytes(bytes)

    @property
    def is_loading(self):
        return self._activity_indicator.active

    @is_loading.setter
    def is_loading(self, value):
        self._activity_indicator.active = bool(value)

    def __pt_container__(self):
        return self.container
