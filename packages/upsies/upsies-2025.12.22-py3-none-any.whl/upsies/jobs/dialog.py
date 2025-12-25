"""
Get information from the user
"""

import collections
import inspect
import re

from .. import utils
from . import JobBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class ChoiceJob(JobBase):
    """
    Ask the user to choose from a set of values

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``dialog_updated``
            Emitted when the :attr:`options`, :attr:`focused` or
            :attr:`autodetected` properties are set or when :attr:`options` is
            modified. Registered callbacks get no arguments.

        ``autodetecting``
            Emitted when :attr:`autodetect` is called. Registered callbacks
            get the job instance as a positional argument.

        ``autodetected``
            Emitted when :attr:`autodetect` returns. Registered callbacks get
            the job instance as a positional argument.
    """

    @property
    def name(self):
        return self._name

    @property
    def label(self):
        return self._label

    @property
    def question(self):
        """Text that is displayed alongside the :attr:`options`"""
        return self._question

    @question.setter
    def question(self, question):
        """Text that is displayed alongside the :attr:`options`"""
        self._question = question

    @property
    def options(self):
        """
        Sequence of options the user can make

        An option is a :class:`tuple` with 2 items. The first item is a
        human-readable :class:`str` and the second item is any object that is
        available as :attr:`choice` when the job is finished.

        Options may also be passed as a flat iterable of :class:`str`, in which
        case both items in the tuple are identical.

        When setting this property, focus is preserved if the value of the
        focused option exists in the new options. Otherwise, the first option is
        focused.
        """
        return getattr(self, '_options', ())

    @options.setter
    def options(self, options):
        # Build new list of options
        valid_options = []
        for option in options:
            if isinstance(option, str):
                valid_options.append((option, option))
            elif isinstance(option, collections.abc.Sequence):
                if len(option) != 2:
                    raise ValueError(f'Option must be 2-tuple, not {option!r}')
                else:
                    valid_options.append((str(option[0]), option[1]))
            else:
                raise ValueError(f'Option must be 2-tuple, not {option!r}')

        if len(valid_options) < 2:
            raise ValueError(f'There must be at least 2 options: {options!r}')

        # Remember current focus
        prev_focused = self.focused

        # Set new options
        self._options = utils.MonitoredList(
            valid_options,
            callback=lambda _: self.signal.emit('dialog_updated'),
        )

        # Try to restore focus if the previously focused item still exists,
        # default to first option
        self._focused_index = 0
        if prev_focused:
            _prev_label, prev_value = prev_focused
            for index, (_label, value) in enumerate(valid_options):
                if value == prev_value:
                    self._focused_index = index
                    break

        self.signal.emit('dialog_updated')

    @property
    def multichoice(self):
        """Whether multiple options can be selected"""
        return self._multichoice

    def get_index(self, thing):
        """
        Return index in :attr:`options`

        :param thing: Identifier of a option in :attr:`options`

            This can be:

            `None`
                Return `None`

            an index (:class:`int`)
               Return `thing`, but limited to the minimum/maximum valid index.

            one of the 2-tuples in :attr:`options`
                Return the index of `thing` in :attr:`options`.

            an item of one of the 2-tuples in :attr:`options`
                Return the index of the first 2-tuple in :attr:`options` that
                contains `thing`.

            a :func:`regular expression <re.compile>`
                Return the index of the first 2-tuple in :attr:`options` that
                contains something that matches `thing`. Non-string values are
                converted to :class:`str` for matching against the regular
                expression.

        :raise ValueError: if `thing` is not found in :attr:`options`
        """
        if thing is None:
            return None

        elif isinstance(thing, int):
            return max(0, min(thing, len(self.options) - 1))

        elif thing in self.options:
            return self.options.index(thing)

        else:
            for i, (label, value) in enumerate(self.options):
                # Focus by human-readable text or value
                if thing in (label, value):
                    return i

                # Focus by matching regex against human-readable text or value
                elif isinstance(thing, re.Pattern):
                    value_str = str(value)
                    if thing.search(label) or thing.search(value_str):
                        return i

        raise ValueError(f'No such option: {thing!r}')

    def get_option(self, thing):
        """
        Return item in :attr:`options`

        :param thing: See :meth:`get_index`

        If `thing` is `None`, return the currently focused option, which is
        indicated by :attr:`focused_index`.
        """
        option_index = self.get_index(thing)
        if option_index is None:
            option_index = self.focused_index
        return self.options[option_index]

    @property
    def focused_index(self):
        """Index of currently focused option in :attr:`options`"""
        return getattr(self, '_focused_index', None)

    @property
    def focused(self):
        """
        Currently focused option (2-tuple)

        This property can be set to anything that is a valid value for
        :meth:`get_index`.
        """
        focused_index = self.focused_index
        if focused_index is not None:
            return self.options[focused_index]

    @focused.setter
    def focused(self, focused):
        # focused_index can't be set to None, so we default to first option
        self._focused_index = self.get_index(focused)
        if self._focused_index is None:
            self._focused_index = 0
        self.signal.emit('dialog_updated')

    @property
    def autodetected(self):
        """
        Autodetected option (2-tuple) or sequence of autodetected options (if `multichoice`) or
        `None`

        This property can be set to anything that is a valid value for :meth:`get_index`. If
        `multichoice` was `True`, it must be set to a sequence of valid :meth:`get_index` arguments.

        If this property is set to `None`, all options are marked as "not autodetected".
        """
        if self._multichoice:
            return tuple(self.options[index] for index in self.autodetected_indexes)
        elif self.autodetected_indexes:
            return self.options[self.autodetected_indexes[0]]

    @autodetected.setter
    def autodetected(self, autodetected):
        if self._multichoice and utils.is_sequence(autodetected):
            self._autodetected_indexes = tuple(
                index
                for thing in autodetected
                if (index := self.get_index(thing)) is not None
            )
        elif autodetected is not None:
            if (index := self.get_index(autodetected)) is not None:
                self._autodetected_indexes = (index,)
            else:
                self._autodetected_indexes = ()
        else:
            self._autodetected_indexes = ()

        self.signal.emit('dialog_updated')

    @property
    def autodetected_indexes(self):
        """Sequence of autodetected option indexes in :attr:`options`"""
        return tuple(getattr(self, '_autodetected_indexes', ()))

    @property
    def choice(self):
        """
        User-chosen value if job is finished, `None` otherwise

        If `multichoice` was `True`, this is a sequence of chosen values.

        While :attr:`~.base.JobBase.output` contains the user-readable string
        (first item of the chosen 2-tuple in :attr:`options`), this is the
        object attached to it (second item).
        """
        if self._multichoice:
            return getattr(self, '_choice', ())
        else:
            return getattr(self, '_choice', None)

    def _set_choice(self, choice):
        # This method is called via `output` signal (see initialize()), which is emitted by
        # add_output(), so make_choice() doesn't need to call _set_choice().
        if not self._multichoice and hasattr(self, '_choice'):
            raise RuntimeError(f'{self.name}: Choice was already made: {self.choice}')
        elif self._multichoice:
            if utils.is_sequence(choice):
                self._choice = tuple(
                    self.get_option(c)[1]
                    for c in choice
                )
            else:
                self._choice = (self.get_option(choice)[1],)
        else:
            _label, value = self.get_option(choice)
            self._choice = value

    def make_choice(self, thing):
        """
        Make a choice and :meth:`~.JobBase.finalize` this job

        :param thing: See :meth:`get_option`

        After this method is called, this job :attr:`~.JobBase.is_finished`,
        :attr:`~.JobBase.output` contains the human-readable label of the choice
        and :attr:`choice` is the machine-readable value of the choice.
        """
        if self._multichoice and utils.is_sequence(thing):
            chosen = tuple(
                self.get_option(thing)
                for thing in thing
            )
        else:
            chosen = (self.get_option(thing),)

        add_chosen = True
        if self._validate:
            try:
                self._validate(chosen)
            except ValueError as e:
                self.warn(e)
                add_chosen = False

        if add_chosen:
            for option in chosen:
                self.add_output(option[0])
            self.finalize()

    def set_label(self, identifier, new_label):
        """
        Assign new label to option

        :param identifier: Option (2-tuple of `(<current label>, <value>)`) or the
            current label or value of an option
        :param new_label: New label for the option defined by `identifier`

        Do nothing if `identifier` doesn't match any option.
        """
        new_options = []
        for label, value in tuple(self.options):
            if identifier in (
                    label,
                    value,
                    (label, value)
            ):
                new_options.append((str(new_label), value))
            else:
                new_options.append((label, value))
        if self.options != new_options:
            self.options = new_options

    def initialize(self, *, name, label, options, question=None,
                   focused=None, autodetected=None, autodetect=None, autofinish=False,
                   multichoice=None, validate=None):
        """
        Set internal state

        :param name: Name for internal use
        :param label: Name for user-facing use
        :param options: Iterable of options the user can pick from
        :param question: Any text that is displayed alongside the `options`
        :param focused: See :attr:`focused`
        :param autodetected: See :attr:`autodetected`
        :param autodetect: Callable that sets :attr:`autodetected` when job is
            started

            `autodetect` gets the job instance (``self``) as a positional
            argument.
        :param autofinish: Whether to call :meth:`make_choice` if `autodetect`
            returns anything that is not `None`
        :param multichoice: Whether multiple or no items from `options` can be chosen
        :param validate: :class:`callable` that gets the sequence of chosen options and raises
            :class:`ValueError` to inform the user about their mistake

        :raise ValueError: if `options` is shorter than 2 or `focused` is
            invalid
        """
        self._name = str(name)
        self._label = str(label)
        self._autodetect = autodetect
        self._autofinish = bool(autofinish)
        self._multichoice = bool(multichoice)
        self._validate = validate

        self.signal.add('dialog_updated')
        self.signal.add('autodetecting')
        self.signal.add('autodetected')
        self.signal.register('output', self._set_choice)

        self.options = options
        self.question = question
        self.autodetected = autodetected

        if focused is not None:
            self.focused = focused
        elif utils.is_sequence(autodetected):
            self.focused = autodetected[0]
        else:
            self.focused = autodetected

    async def run(self):
        # Always emitting the autodetecting/autodetected signals makes things
        # more reliable and the UI doesn't have to handle special cases.
        self.signal.emit('autodetecting')

        if self._autodetect:
            autodetected = await self._call_autodetect()
            if autodetected is not None:
                if self._multichoice and utils.is_sequence(autodetected):
                    # Select all autodetected items and focus the first one.
                    self.autodetected = autodetected
                    try:
                        self.focused = next(iter(autodetected))
                    except StopIteration:
                        # `autodetected` is empty (e.g. autodetection failed)
                        self.focused = None
                else:
                    self.autodetected = self.focused = autodetected

        self.signal.emit('autodetected')

        if self._autofinish and self.autodetected:
            self.make_choice(self.autodetected)

        # Wait for make_choice() getting called. If it was already called via
        # `autofinish`, finalization() returns immediately.
        await self.finalization()

    async def _call_autodetect(self):
        if self._autodetect is not None:
            if inspect.iscoroutinefunction(self._autodetect):
                return await self._autodetect(self)
            elif callable(self._autodetect):
                return self._autodetect(self)
            else:
                raise RuntimeError(f'Bad autodetect value: {self._autodetect!r}')


class TextFieldJob(JobBase):
    """
    Ask the user for text input

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``text``
            Emitted when :attr:`text` was changed without user input. Registered
            callbacks get the new text as a positional argument.

        ``is_loading``
            Emitted when :attr:`is_loading` was changed. Registered callbacks
            get the new :attr:`is_loading` value as a positional argument.

        ``read_only``
            Emitted when :attr:`read_only` was changed. Registered callbacks get
            the new :attr:`read_only` value as a positional argument.

        ``obscured``
            Emitted when :attr:`obscured` was changed. Registered callbacks get
            the new :attr:`obscured` value as a positional argument.
    """

    @property
    def name(self):
        return self._name

    @property
    def label(self):
        return self._label

    @property
    def text(self):
        """Current text"""
        return getattr(self, '_text', '')

    @text.setter
    def text(self, text):
        # Don't call validator here because it should be possible to set invalid texts and let the
        # user fix it manually. We only validate when we commit to `text` (see add_output()).
        self._text = self._normalizer(str(text))
        if not self.is_finished:
            self.signal.emit('text', self.text)

    @property
    def obscured(self):
        """
        Whether the text is unreadable, e.g. when entering passwords

        This is currently not fully implemented.
        """
        return getattr(self, '_obscured', False)

    @obscured.setter
    def obscured(self, obscured):
        self._obscured = bool(obscured)
        if not self.is_finished:
            self.signal.emit('obscured', self.obscured)

    @property
    def read_only(self):
        """
        Whether the user should be able change the text

        This is just a boolean flag that is not enforced by the job so that autodetection will still
        work. The user interface must track its status via the ``read_only`` signal and enforce it.
        """
        return getattr(self, '_read_only', False)

    @read_only.setter
    def read_only(self, read_only):
        self._read_only = bool(read_only)
        if not self.is_finished:
            self.signal.emit('read_only', self.read_only)

    @property
    def is_loading(self):
        """Whether :attr:`text` is currently being changed automatically"""
        return getattr(self, '_is_loading', False)

    @is_loading.setter
    def is_loading(self, is_loading):
        self._is_loading = bool(is_loading)
        if not self.is_finished:
            self.signal.emit('is_loading', self.is_loading)

    def initialize(self, *, name, label,
                   text='', default=None, finish_on_success=False,
                   warn_exceptions=(), error_exceptions=(),
                   validator=None, normalizer=None, obscured=False, read_only=False):
        """
        Set internal state

        :param name: Name for internal use
        :param label: Name for user-facing use
        :param text: Initial text or callable (synchronous or asynchronous)
            which will be called when the job is :meth:`started
            <upsies.jobs.base.JobBase.start>`. The return value is used as the
            initial text.
        :param default: Text to use if `text` is `None`, returns `None` or
            raises `warn_exceptions`
        :param finish_on_success: Whether to call :meth:`~.JobBase.finalize`
            after setting :attr:`text` to `text`

            .. note:: :meth:`~.JobBase.finalize` is not called if :attr:`text`
                      is set to `default`.
        :param warn_exceptions: Sequence of exception classes that are caught if raised by `text`
            and passed on to :meth:`~.JobBase.warn`
        :param error_exceptions: Sequence of exception classes that are caught if raised by `text`
            and passed on to :meth:`~.JobBase.error`
        :param validator: Callable that gets text before job is finished. If
            `ValueError` is raised, it is displayed as a warning instead of
            finishing the job.
        :type validator: callable or None
        :param normalizer: Callable that gets text and returns the new text. It
            is called before `validator`. It should not raise any exceptions.
        :type normalizer: callable or None
        :param bool obscured: Whether :attr:`obscured` is set to `True`
            initially (currently fully implemented)
        :param bool read_only: Whether :attr:`read_only` is set to `True`
            initially
        """
        self._name = str(name)
        self._label = str(label)
        self._validator = validator or (lambda _: None)
        self._normalizer = normalizer or (lambda text: text)
        self.signal.add('text')
        self.signal.add('is_loading')
        self.signal.add('read_only')
        self.signal.add('obscured')
        self.obscured = obscured
        self.read_only = read_only

        if isinstance(text, str):
            # Set text attribute immediately
            self.text = text

        self._run_arguments = (text, default, finish_on_success, warn_exceptions, error_exceptions)

    async def run(self):
        text, default, finish_on_success, warn_exceptions, error_exceptions = self._run_arguments

        if inspect.isawaitable(text):
            await self.fetch_text(
                coro=text,
                default=default,
                finish_on_success=finish_on_success,
                warn_exceptions=warn_exceptions,
                error_exceptions=error_exceptions,
            )

        elif inspect.iscoroutinefunction(text):
            await self.fetch_text(
                coro=text(),
                default=default,
                finish_on_success=finish_on_success,
                warn_exceptions=warn_exceptions,
                error_exceptions=error_exceptions,
            )

        else:
            self.set_text(
                text=text,
                default=default,
                finish_on_success=finish_on_success,
                warn_exceptions=warn_exceptions,
                error_exceptions=error_exceptions,
            )

        # If fetch_text() or set_text() failed for some reason, we must not
        # finish until the user fixed the situation, usually by entering text
        # manually that we failed to autodetect.
        await self.finalization()

    def set_text(self, text, *, default=None, finish_on_success=False, warn_exceptions=(), error_exceptions=()):
        """
        Change :attr:`text` value

        :param text: New text value

            If this is callable, it must return the new :attr:`text` or `None` to use `default`

        :param default: Text to use if `text` is `None`, returns `None` or raises `warn_exceptions`

        :param finish_on_success: Whether to call :meth:`finish` after setting :attr:`text` to
            `text`

            .. note:: :meth:`finish` is not called when :attr:`text` is set to `default`.

        :param warn_exceptions: Sequence of exception classes that may be raised by `coro` and are
            passed on to :`~.JobBase.warn`

        :param error_exceptions: Sequence of exception classes that may be raised by `coro` and are
            passed on to :`~.JobBase.error`
        """
        self.is_loading = self.read_only = True
        try:
            if callable(text):
                new_text = text()
            elif text is not None:
                new_text = str(text)
            else:
                new_text = None
        except Exception as e:
            _log.debug('%s: Caught exception: %r', self.name, e)
            self._set_text(default)
            self._handle_exception(e, warn_exceptions=warn_exceptions, error_exceptions=error_exceptions)
        else:
            self._set_text(new_text, default=default, finish=finish_on_success)
        finally:
            # Always re-enable text field after we're done messing with it
            self.is_loading = self.read_only = False

    async def fetch_text(self, coro, *, default=None, finish_on_success=False, warn_exceptions=(), error_exceptions=()):
        """
        Get :attr:`text` from coroutine

        :param coro: Coroutine that returns the new :attr:`text` or `None` to
            use `default`

        :param default: Text to use if `text` is `None`, returns `None` or raises `warn_exceptions`

        :param finish_on_success: Whether to call :meth:`finish` after setting :attr:`text` to
            `coro` return value

            .. note:: :meth:`finish` is not called when :attr:`text` is set to `default`.

        :param warn_exceptions: Sequence of exception classes that may be raised by `coro` and are
            passed on to :`~.JobBase.warn`

        :param error_exceptions: Sequence of exception classes that may be raised by `coro` and are
            passed on to :`~.JobBase.error`
        """
        self.is_loading = self.read_only = True
        try:
            new_text = await coro
        except Exception as e:
            _log.debug('%s: Caught exception: %r', self.name, e)
            self._set_text(default)
            self._handle_exception(e, warn_exceptions=warn_exceptions, error_exceptions=error_exceptions)
        else:
            self._set_text(new_text, default=default, finish=finish_on_success)
        finally:
            # Always re-enable text field after we're done messing with it
            self.is_loading = self.read_only = False

    def _set_text(self, text, *, default=None, finish=False):
        # Fill in text
        if text is not None:
            self.text = text
            # Only finish if the intended text was set
            if finish:
                # We must call add_output() because it handles output caching, and it also finishes
                # the job.
                self.add_output(text)

        elif default is not None:
            self.text = default

    def _handle_exception(self, exception, warn_exceptions=(), error_exceptions=()):
        # Fatal error that terminates the job and all its siblings.
        if isinstance(exception, error_exceptions):
            self.error(exception)

        # Display error and allow user to manually fix the situation.
        elif isinstance(exception, warn_exceptions):
            self.warn(exception)

        # An exception we didn't expect.
        else:
            raise exception

    def add_output(self, output):
        """
        Validate `output` before actually adding it

        Pass `output` to `validator` (see :meth:`initialize`). If :class:`ValueError` is raised,
        pass it to :meth:`warn` and do not finalize. Otherwise, pass `output` to
        :meth:`~.base.JobBase.add_output` and :meth:`~.base.JobBase.finalize` this job.
        """
        # Normalize, e.g. remove leading and trailing whitespace.
        output = self._normalizer(output)

        # Remove any warning from previously failed validation.
        self.clear_warnings()

        # Validate normalized output.
        try:
            self._validator(output)
        except ValueError as e:
            self.warn(e)
        else:
            # Add normalized and validated output.
            super().add_output(output)
            self.finalize()
