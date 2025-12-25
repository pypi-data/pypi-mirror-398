"""
Background workers to keep the UI responsive
"""

import asyncio
import enum
import functools
import multiprocessing
import pickle
import queue

from .. import errors

import logging  # isort:skip
_log = logging.getLogger(__name__)


class MsgType(enum.Enum):
    """
    Enum that specifies the type of an IPC message (info, error, etc)
    """
    init = 'init'
    info = 'info'
    error = 'error'
    result = 'result'
    terminate = 'terminate'


class DaemonProcess:
    """
    :class:`multiprocessing.Process` abstraction with IPC

    Intended to offload heavy work (e.g. torrent creation) onto a different
    process. (Threads can still make the UI unresponsive because of the
    `GIL <https://wiki.python.org/moin/GlobalInterpreterLock>`_.)
    """

    def __init__(self, target, name=None, args=(), kwargs={},
                 init_callback=None, info_callback=None, error_callback=None,
                 result_callback=None, finished_callback=None):
        self._target = target
        self._name = name or target.__qualname__
        self._target_args = args
        self._target_kwargs = kwargs
        self._init_callback = init_callback
        self._info_callback = info_callback
        self._error_callback = error_callback
        self._result_callback = result_callback
        self._finished_callback = finished_callback

        self._ctx = multiprocessing.get_context('spawn')
        self._write_queue = self._ctx.Queue()
        self._read_queue = self._ctx.Queue()
        self._process = None
        self._process_finished = False
        self._read_queue_reader_task = None
        self._exception = None

    def start(self):
        """Start the process"""
        _log.debug('%s: Starting process: %r', self._name, self._target)
        target_wrapped = functools.partial(
            _target_process_wrapper,
            self._target,
            self._read_queue,
            self._write_queue,
        )
        self._process = self._ctx.Process(
            name=self._name,
            target=target_wrapped,
            args=self._make_args_picklable(self._target_args),
            kwargs=self._make_kwargs_picklable(self._target_kwargs),
        )
        self._process.start()
        self._read_queue_reader_task = asyncio.create_task(self._read_queue_reader())
        self._read_queue_reader_task.add_done_callback(self._handle_read_queue_reader_task_done)

    def _make_args_picklable(self, args):
        return tuple(self._get_picklable_value(arg) for arg in args)

    def _make_kwargs_picklable(self, kwargs):
        return {self._get_picklable_value(k): self._get_picklable_value(v)
                for k, v in kwargs.items()}

    def _get_picklable_value(self, value):
        # Try to pickle `value`. If it fails, try to instantiate `value` as one
        # of it's parent classes. Ignore first class (which is identical to
        # type(value)) and the last class, which should always be (`object`).
        types = type(value).mro()[1:-1]
        while True:
            try:
                pickle.dumps(value)
            # Python 3.9.1: This raises AttributeError, but the docs don't mention it.
            except Exception:
                if types:
                    value = types.pop(0)(value)
                else:
                    raise
            else:
                return value

    async def _read_queue_reader(self):
        while True:
            typ, msg = await asyncio.get_running_loop().run_in_executor(None, self._read_queue.get)

            if typ is MsgType.init:
                if self._init_callback:
                    self._init_callback(msg)

            elif typ is MsgType.info:
                if self._info_callback:
                    self._info_callback(msg)

            elif typ is MsgType.error:
                self._handle_error(msg)

            elif typ is MsgType.result:
                if self._result_callback:
                    self._result_callback(msg)
                break

            elif typ is MsgType.terminate:
                break

            else:
                raise RuntimeError(f'Unknown message type: {typ!r}')

    def _handle_read_queue_reader_task_done(self, task):
        # Catch exceptions from _read_queue_reader()
        try:
            task.result()

        except asyncio.CancelledError:
            _log.debug('%s: Cancelled _read_queue_reader()', self._name)

        except BaseException as e:
            _log.debug('%s: Caught _read_queue_reader() exception: %r', self._name, e)
            self._exception = e
            self._handle_error(e)

        finally:
            self._process_finished = True
            if self._finished_callback:
                try:
                    self._finished_callback()
                except BaseException as e:
                    self._exception = e
                    self._handle_error(e)

    def _handle_error(self, error):
        if isinstance(error, tuple):
            exception, traceback = error
            exception = errors.DaemonProcessError(exception, traceback)
        elif isinstance(error, BaseException):
            exception = error
        else:
            exception = errors.DaemonProcessError(errors.UpsiesError(error), '')

        if isinstance(exception, errors.DaemonProcessTerminated):
            return

        self._exception = exception
        if self._error_callback:
            try:
                self._error_callback(self._exception)
            except BaseException as e:
                self._exception = e
                raise
        else:
            raise self._exception

    def stop(self):
        """
        Stop the process

        This has no effect if the process is not alive.
        """
        if not self.is_finished:
            self.send(MsgType.terminate, None)

    def send(self, typ, value):
        """
        Send message to process if it is still alive

        If :attr:`is_alive` is `False`, do nothing.

        :param MsgType typ: General message category
        :param value: Message string, payload, sentinel, etc.
        """
        if self.is_finished:
            raise RuntimeError(f'Cannot send to finished process: {self._name}')
        else:
            self._write_queue.put((typ, value))

    @property
    def is_alive(self):
        """Whether :meth:`start` was called and the process has not finished yet"""
        if self._process:
            return self._process.is_alive()
        else:
            return False

    @property
    def is_finished(self):
        """Whether :meth:`start` was called and the process has finished"""
        return self._process_finished

    @property
    def exception(self):
        """Exception from `target` or callback, `None` if no exception was raised"""
        task = self._read_queue_reader_task
        if task and task.done() and task.exception():
            return task.exception()
        else:
            return self._exception

    async def join(self):
        """Block asynchronously until the process exits"""
        if self._process:
            _log.debug('%s: Joining process: %r', self._name, self._process)
            await asyncio.get_running_loop().run_in_executor(None, self._process.join)
            self._process = None

        if self._read_queue_reader_task:
            if not self._read_queue_reader_task.done():
                # Unblock self._read_queue()
                self._read_queue.put((MsgType.terminate, None))
                await self._read_queue_reader_task
            exc = self.exception
            if exc:
                _log.debug('Re-raising exception: %r', exc)
                raise exc


def _target_process_wrapper(target, write_queue, read_queue, *args, **kwargs):
    try:
        target(write_queue, read_queue, *args, **kwargs)
    except BaseException as e:
        # Because the traceback is not picklable, preserve it as a string before
        # sending it over the Queue
        import traceback
        traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        write_queue.put((MsgType.error, (e, traceback)))
    finally:
        write_queue.put((MsgType.terminate, None))


def maybe_terminate(input_queue):
    """
    Read all queued items and raise :class:`~DaemonProcessTerminated` if there is a
    `MsgType.terminate`

    Put all other items back into the queue in the same order.
    """
    queued_items = read_input_queue_until_empty(input_queue)
    terminate = False
    for typ, msg in queued_items:
        if typ is MsgType.terminate:
            terminate = True
        else:
            input_queue.put((typ, msg))
    if terminate:
        raise errors.DaemonProcessTerminated('Terminated')


def read_input_queue(input_queue, default=(None, None)):
    """
    Return single `(<MsgType>, <payload data>)` tuple from `input_queue` or `default` if it is
    empty
    """
    try:
        typ, msg = input_queue.get_nowait()
    except queue.Empty:
        return default
    else:
        return typ, msg


NO_RETURN_VALUE = object()

def read_input_queue_key(input_queue, key):
    """
    Read :class:`dict` from `input_queue` and return its value for `key` if it exists

    The :class:`dict` must be queued as :class:`MsgType.info`.

    If `MsgType.terminate` is queued, raise :class:`~.DaemonProcessTerminated` instead of looking
    for `key`.

    Put all other items back into the queue in the same order.
    """
    return_value = NO_RETURN_VALUE
    terminate = False
    keep_looking = True
    items_to_requeue = []

    while keep_looking:
        queued_items = read_input_queue_until_empty(input_queue)

        # We must loop over all items here to check if there is a MsgType.terminate.
        for typ, msg in queued_items:
            if typ is MsgType.terminate:
                terminate = True
                keep_looking = False

            # It is important to only find the first matching key, otherwise we will lose all
            # leading matches if multiple matches are queued.
            elif (
                    return_value is NO_RETURN_VALUE
                    and typ == MsgType.info and isinstance(msg, dict)
                    and key in msg
            ):
                return_value = msg[key]
                keep_looking = False

            else:
                items_to_requeue.append((typ, msg))

    # Put all dequeued items back on the queue, except for the ones we processed.
    for item in items_to_requeue:
        input_queue.put(item)

    if terminate:
        raise errors.DaemonProcessTerminated('Terminated')
    else:
        return return_value


def read_input_queue_until_empty(input_queue):
    """
    Keep reading `input_queue` until it is empty

    Return the sequence of items that was read from the queue.

    Raise :class:`~DaemonProcessTerminated` if there is a `MsgType.terminate` queued.
    """
    items = []
    while True:
        try:
            typ, msg = input_queue.get(timeout=0.01)
        except queue.Empty:
            return tuple(items)
        else:
            if typ == MsgType.terminate:
                for item in items:
                    input_queue.put(item)
                raise errors.DaemonProcessTerminated('Terminated')
            else:
                items.append((typ, msg))
