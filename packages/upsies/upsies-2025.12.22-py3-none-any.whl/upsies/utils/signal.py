"""
Managing callbacks
"""

import asyncio
import collections
import contextlib
import enum

import logging  # isort:skip
_log = logging.getLogger(__name__)


class Signal:
    """Simple callback registry"""

    class Stopped(enum.Flag):
        """Three-way boolean enum: `false`, `true` and `immediately`"""

        false = 0
        true = 1
        immediately = 2

    def __init__(self, id=None, *, signals):
        self.id = id
        self._signals = {}
        self._suspended_signals = set()
        self._emissions = []
        self._emissions_recorded = []
        self._record_signals = []
        self._queues = collections.defaultdict(list)  # List of asyncio.Queue
        self._is_stopped = self.Stopped.false
        for signal in signals:
            self.add(signal)

    @property
    def id(self):
        """Instance ID used for debugging"""
        return self._id

    @id.setter
    def id(self, id):
        if id in ('', None):
            self._id = 'anonymous'
        else:
            self._id = id

    def add(self, signal, *, record=False):
        """
        Create new `signal`

        :param hashable signal: Any hashable object
        :param bool record: Whether emissions of this signal are recorded in
            :attr:`emissions_recorded`

        :raise TypeError: if `signal` is not hashable
        :raise RuntimeError: if `signal` has been added previously
        """
        if not isinstance(signal, collections.abc.Hashable):
            raise TypeError(f'{self._id}: Unhashable signal: {signal!r}')
        elif signal in self._signals:
            raise RuntimeError(f'{self._id}: Signal already added: {signal!r}')
        else:
            self._signals[signal] = []
            if record:
                self.record(signal)

    @property
    def signals(self):
        """Mutable dictionary of signals mapped to lists of callbacks"""
        return self._signals

    def record(self, signal):
        """Record emissions of `signal` in :attr:`emissions`"""
        if signal not in self._signals:
            raise ValueError(f'{self._id}: Unknown signal: {signal!r}')
        else:
            self._record_signals.append(signal)

    @property
    def recording(self):
        """class:`list` of signals that are recorded"""
        return self._record_signals

    def register(self, signal, callback):
        """
        Call `callback` when `signal` is emited

        :param hashable signal: Previously added signal
        :param callable callback: Any callback. The signature depends on the caller of
            :meth:`emit`.

        :raise ValueError: if `signal` was not added first
        :raise TypeError: if `callback` is not callable
        """
        if signal not in self._signals:
            raise ValueError(f'{self._id}: Unknown signal: {signal!r}')
        elif not callable(callback):
            raise TypeError(f'{self._id}: Not a callable: {callback!r}')
        else:
            self._signals[signal].append(callback)

    def emit(self, signal, *args, **kwargs):
        """
        Call callbacks that are registered to `signal` and make any ongoing :meth:`receive_all`
        calls iterate and any ongoing :meth:`receive_one` calls return

        :param hashable signal: Previously added signal

        Any other arguments are passed on to the callbacks.
        """
        if self.is_stopped:
            raise RuntimeError(f'{self._id}: Cannot emit signal {signal!r} after stop() was called')

        if signal not in self._suspended_signals:
            for callback in self._signals[signal]:
                callback(*args, **kwargs)

            # Store emission.
            self._emissions.append((signal, {'args': args, 'kwargs': kwargs}))

            # Store recorded emission separately.
            if signal in self._record_signals:
                self._emissions_recorded.append((signal, {'args': args, 'kwargs': kwargs}))

            # Tell receive_(all|one)() calls about the emission.
            for queue in self._queues[signal]:
                queue.put_nowait((args, kwargs))

    async def receive_all(self, signal, *, only_posargs=False):
        """
        Iterate over ``(args, kwargs)`` from :meth:`emit` calls for `signal`

        This will always produce all emitted signals, both from the past and the future, until
        :meth:`stop` is called. The only exception is when :meth:`stop` is called with
        ``immediately=True``, in which case iteration stops immediately.

        :param hashable signal: Previously added signal
        :param bool only_posargs: Whether to ignore any keyword arguments from the :meth:`emit` call
            and only iterate over positional arguments
        """
        # Create queue that will get signals via emit(). We do this first because we don't want to
        # miss any new emissions while we are yielding old emissions.
        queue = asyncio.Queue()
        self._queues[signal].append(queue)

        # Yield old emissions that were emitted before we were called, but only if emissions should
        # not stop IMMEDIATELY.
        if self.is_stopped is not self.Stopped.immediately:
            for signal_, emission in self.emissions:
                if signal_ == signal:
                    if only_posargs:
                        yield emission['args']
                    else:
                        yield emission['args'], emission['kwargs']

        if not self._is_stopped:
            # Yield new emissions as they appear until stop() is called.
            while True:
                args, kwargs = await queue.get()
                if args is kwargs is None:
                    break
                elif only_posargs:
                    yield args
                else:
                    yield args, kwargs

    async def receive_one(self, signal, *, only_posargs=False):
        """Same as :meth:`receive_all`, but return just one emission"""
        async for emission in self.receive_all(signal, only_posargs=only_posargs):
            return emission
        # stop() was called before any `signal` was emitted
        return () if only_posargs else ((), {})

    async def wait_for(self, signal):
        """Wait for emission of `signal` and return `None`"""
        await self.receive_one(signal)

    def stop(self, *, immediately=False):
        """
        Do not :meth:`emit` any more signals

        Calling this method disallows further calls to :meth:`emit`, iterating over any ongoing
        :meth:`receive_all` calls stops, and any ongoing :meth:`receive_one` calls return `None`

        :param bool immediately: If truthy :meth:`receive_all` calls stop iterating NOW without
            producing any more emissions and :meth:`receive_one` calls return `None`

            Otherwise, any emissions made before :meth`stop` is called are processed normally before
            iteration stops.
        """
        if immediately:
            self._is_stopped = self.Stopped.immediately

            # Dump all items from all queues so receive_all() stops iteration immediately.
            for queues in self._queues.values():
                for queue in queues:
                    try:
                        queue.get_nowait()
                    except asyncio.queues.QueueEmpty:
                        pass
        else:
            self._is_stopped = self.Stopped.true

        # Put termination sentinels into queues.
        args = kwargs = None
        for queues in self._queues.values():
            for queue in queues:
                queue.put_nowait((args, kwargs))

    @property
    def is_stopped(self):
        """
        Whether :meth:`stop` was called (see :attr:`Stopped`)

        This means :meth:`emit` can no longer be called, any ongoing :meth:`receive_all` calls will
        stop iterating, and any ongoing :meth:`receive_one` calls return `None`.
        """
        return self._is_stopped

    @property
    def emissions(self):
        """
        Sequence of :meth:`emit` calls made so far

        Each call is stored as a tuple like this::

            (<signal>, {"args": <positional arguments>,
                        "kwargs": <keyword arguments>})
        """
        return tuple(self._emissions)

    @property
    def emissions_recorded(self):
        """
        Sequence of only recorded :meth:`emit` calls made so far

        Each call is stored as a tuple like this::

            (<signal>, {"args": <positional arguments>,
                        "kwargs": <keyword arguments>})
        """
        return tuple(self._emissions_recorded)

    def replay(self, emissions):
        """:meth:`emit` previously recorded :attr:`emissions`"""
        for signal, payload in emissions:
            self.emit(signal, *payload['args'], **payload['kwargs'])

    @contextlib.contextmanager
    def suspend(self, *signals):
        """
        Context manager that blocks certain signals in its body

        :param signals: Which signals to block

        :raise ValueError: if any signal in `signals` is not registered
        """
        for signal in signals:
            if signal not in self._signals:
                raise ValueError(f'{self._id}: Unknown signal: {signal!r}')

        self._suspended_signals.update(signals)

        try:
            yield
        finally:
            self._suspended_signals.difference_update(signals)
