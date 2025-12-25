"""
Generic user dialogs

Prompts take arbitrary keyword arguments that are used by the user interface
to create the dialog.

When the user makes a choice, the user interface must pass it on to the prompt
object via :meth:`~.Prompt.set_result`. The prompt object then takes care of
passing the result to any callbacks.
"""

import asyncio

import logging  # isort:skip
_log = logging.getLogger(__name__)


class Prompt:
    """
    Base class of all prompts

    Every prompt takes a sequence of callbacks. Any other keyword arguments
    are specified by the subclass. The user interface can access them as
    :attr:`parameters` to create UI widgets.

    Prompt instances are awaitable. The `await` will return when the user
    provided input. The return value of the `await` call is the same as the
    :attr:`result` property. Prompts can be awaited multiple times at any
    time.
    """

    def __init__(self, *, callbacks=(), **parameters):
        self._callbacks = list(callbacks)
        self._parameters = parameters
        self._result_arrived = asyncio.Event()
        self._result = None

    @property
    def parameters(self):
        """Keyword arguments from instantiation (except for `callbacks`)"""
        return self._parameters

    async def wait(self):
        """Block until :meth:`set_result` is called"""
        await self._result_arrived.wait()

    def __await__(self):
        async def get_result():
            await self.wait()
            return self.result
        return get_result().__await__()

    def on_result(self, callback):
        """Schedule `callback` to be called when :meth:`set_result` is called"""
        self._callbacks.append(callback)

    def set_result(self, result):
        """
        Take the result from the user dialog and make it available to
        callbacks and via the :attr:`result` property
        """
        _log.debug('Setting result: %r', result)
        self._result = result

        # Call callbacks
        for callback in self._callbacks:
            _log.debug('Reporting result to %r: %r', callback, result)
            callback(result)

        # Unblock any wait() calls
        self._result_arrived.set()

    @property
    def result(self):
        """Input from the user"""
        return self._result

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._parameters == other._parameters
        else:
            return NotImplemented

    def __repr__(self):
        arguments = []
        if self._parameters:
            arguments.append(', '.join((
                f'{k}={v!r}'
                for k, v in self._parameters.items()
            )))
        arguments.append(f'callbacks={self._callbacks}')
        arguments_string = ', '.join(arguments)
        return f'{type(self).__name__}({arguments_string})'


class RadioListPrompt(Prompt):
    """
    Pick one of two or more options

    :param options: Sequence of choices
    :param question: Question to show alongside the options or `None`
    :param focused: One of the `options` to focus initially or `None` to focus
        the first option
    """

    def __init__(self, *, callbacks=(), options, question=None, focused=None):
        super().__init__(
            callbacks=callbacks,
            options=options,
            question=question,
            focused=focused,
        )


class CheckListPrompt(Prompt):
    """
    Pick multiple of two or more options

    :param options: Sequence of choices
    :param question: Question to show alongside the options or `None`
    :param focused: One of the `options` to focus initially or `None` to focus
        the first option
    """

    def __init__(self, *, callbacks=(), options, question=None, focused=None):
        super().__init__(
            callbacks=callbacks,
            options=options,
            question=question,
            focused=focused,
        )


class TextPrompt(Prompt):
    """
    Input of arbitrary text

    :param question: Question to show alongside the options or `None`
    :param text: Prefilled text the user can delete or edit
    """

    def __init__(self, *, callbacks=(), question=None, text=''):
        super().__init__(callbacks=callbacks, question=question, text=text)
