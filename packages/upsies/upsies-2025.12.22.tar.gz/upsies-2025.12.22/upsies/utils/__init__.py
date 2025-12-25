"""
Swiss Army knife
"""

import asyncio
import collections
import functools
import hashlib
import importlib
import inspect
import itertools
import os
import re
import types as _types

import logging  # isort:skip
_log = logging.getLogger(__name__)


@functools.cache
def is_running_in_development_environment():
    """
    Whether we are running in a development environment or in production

    This is determined by looking for a ``UPSIES_DEV`` variable and interpreting its value as a
    :class:`~.types.Bool`. The default is ``False``.
    """
    from . import types  # noqa: F811 [*] Redefinition of unused `types`
    upsies_dev = os.environ.get('UPSIES_DEV', None)
    try:
        return bool(types.Bool(upsies_dev))
    except ValueError:
        return False


def os_family():
    """
    Return "windows" or "unix"
    """
    return 'windows' if os.name == 'nt' else 'unix'


# https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/util/lazy_loader.py
class LazyModule(_types.ModuleType):
    """
    Lazily import module to decrease execution time

    :param str module: Name of the module
    :param mapping namespace: Usually the return value of `globals()`
    :param str name: Name of the module in `namespace`; defaults to `module`
    """

    def __init__(self, module, namespace, name=None):
        self._module = module
        self._namespace = namespace
        self._name = name or module
        super().__init__(module)

    def _load(self):
        # Import the target module and insert it into the parent's namespace
        module = importlib.import_module(self.__name__)
        self._namespace[self._name] = module

        # Update this object's dict so that if someone keeps a reference to the
        # LazyLoader, lookups are efficient (__getattr__ is only called on
        # lookups that fail).
        self.__dict__.update(module.__dict__)

        return module

    def __getattr__(self, item):
        module = self._load()
        return getattr(module, item)

    def __dir__(self):
        module = self._load()
        return dir(module)


def submodules(package):
    """
    Return list of submodules and subpackages in `package`

    :param str package: Fully qualified name of parent package,
        e.g. "upsies.imagehosts"
    """
    # Get absolute path to parent directory of top-level package
    own_path = os.path.dirname(__file__)
    rel_path = __package__.replace('.', os.sep)
    assert own_path.endswith(rel_path), f'{own_path!r}.endswith({rel_path!r})'
    project_path = own_path[:-len(rel_path)]

    # Add relative path within project to given package
    package_path = os.path.join(project_path, package.replace('.', os.sep))

    # Find and import public submodules
    submods = []
    for name in os.listdir(package_path):
        if not name.startswith('_'):
            name = name.removesuffix('.py')
            if '.' not in name:
                submods.append(
                    importlib.import_module(name=f'.{name}', package=package)
                )
    return submods


def subclasses(basecls, modules):
    """
    Find subclasses in modules

    :param type basecls: Class that all returned classes are a subclass of
    :param modules: Modules to search
    :type modules: list of module objects
    """
    subclses = []
    for mod in modules:
        for _name, member in inspect.getmembers(mod):
            if (
                    member is not basecls and
                    isinstance(member, type) and
                    issubclass(member, basecls)
            ):
                subclses.append(member)
    return tuple(subclses)


def closest_number(n, ns, max=None, default=0):
    """
    Return the number from `ns` that is closest to `n`

    :param n: Given number
    :param ns: Sequence of allowed numbers
    :param max: Remove any item from `ns` that is larger than `max`
    :param default: Return value in case `ns` is empty
    """
    if max is not None:
        ns_ = tuple(n_ for n_ in ns if n_ <= max)
        if not ns_:
            raise ValueError(f'No number equal to or below {max}: {ns}')
    else:
        ns_ = ns
    return min(ns_, key=lambda x: abs(x - n), default=default)


class MonitoredList(collections.abc.MutableSequence):
    """
    :class:`list` that calls `callback` after every change

    :param callback: Callable that gets the instance as a positional argument
    """

    def __init__(self, *args, callback, **kwargs):
        self._list = list(*args, **kwargs)
        self._callback = callback

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        self._list[index] = value
        self._callback(self)

    def __delitem__(self, index):
        del self._list[index]
        self._callback(self)

    def insert(self, index, value):
        self._list.insert(index, value)
        self._callback(self)

    def __len__(self):
        return len(self._list)

    def __eq__(self, other):
        return self._list == other

    def __repr__(self):
        return f'{type(self).__name__}({self._list!r}, callback={self._callback!r})'


def is_sequence(obj):
    """Return whether `obj` is a sequence and not a string"""
    return (
        isinstance(obj, collections.abc.Sequence)
        and not isinstance(obj, str)
    )


def merge_dicts(a, b, path=()):
    """
    Merge nested dictionaries `a` and `b` into new dictionary with same
    structure
    """
    keys = itertools.chain(a, b)
    merged = {}
    for key in keys:
        if (isinstance(a.get(key), collections.abc.Mapping) and
            isinstance(b.get(key), collections.abc.Mapping)):
            merged[key] = merge_dicts(a[key], b[key], (*path, key))
        elif key in b:
            # Value from b takes precedence
            merged[key] = b[key]
        elif key in a:
            # Value from a is default
            merged[key] = a[key]
    return merged


def deduplicate(seq, key=None):
    """
    Return sequence `seq` with all duplicate items removed while maintaining
    the original order

    :param key: Callable that gets each item and returns a hashable identifier
        for that item
    """
    if key is None:
        def key(k):
            return k

    seen_keys = set()
    deduped = []
    for item in seq:
        k = key(item)
        if k not in seen_keys:
            seen_keys.add(k)
            deduped.append(item)
    return deduped


def as_groups(sequence, group_sizes, default=None):
    """
    Iterate over items from `sequence` in equally sized groups

    :params sequence: List of items to group
    :params group_sizes: Sequence of acceptable number of items in a group

        Find the group size with the lowest number of `default` items in
        the last group. That group size is then used for all groups.
    :param default: Value to pad last group with if
        ``len(sequence) % group_size != 0``

    Example:

    >>> sequence = range(1, 10)
    >>> for group in as_groups(sequence, [4, 5], default="_"):
    ...     print(group)
    (1, 2, 3, 4, 5)
    (6, 7, 8, 9, '_')
    >>> for group in as_groups(sequence, [3, 4], default="_"):
    ...     print(group)
    (1, 2, 3)
    (4, 5, 6)
    (7, 8, 9)
    """
    # Calculate group size that results in the least number of `default` values
    # in the final group
    gs_map = collections.defaultdict(list)
    for gs in group_sizes:
        # How many items from `sequence` are in the last group
        overhang = len(sequence) % gs
        # How many `default` values are in the last group
        default_count = 0 if overhang == 0 else gs - overhang
        gs_map[default_count].append(gs)

    lowest_default_count = sorted(gs_map)[0]
    group_size = max(gs_map[lowest_default_count])
    args = [iter(sequence)] * group_size
    yield from itertools.zip_longest(*args, fillvalue=default)


_unsupported_semantic_hash_types = (
    collections.abc.Iterator,
    collections.abc.Iterable,
    collections.abc.Generator,
)

def semantic_hash(obj):
    """
    Return SHA256 hash for `obj` that stays the same between Python interpreter
    sessions

    https://github.com/schollii/sandals/blob/master/json_sem_hash.py
    """
    def as_str(obj):
        if isinstance(obj, str):
            return obj

        elif isinstance(obj, collections.abc.Mapping):
            stringified = ((as_str(k), as_str(v)) for k, v in obj.items())
            return as_str(sorted(stringified))

        elif isinstance(obj, (collections.abc.Sequence, collections.abc.Set)):
            stringified = (as_str(item) for item in obj)
            return ''.join(sorted(stringified))

        elif isinstance(obj, _unsupported_semantic_hash_types):
            raise RuntimeError(f'Unsupported type: {type(obj)}: {obj!r}')

        else:
            return str(obj)

    return hashlib.sha256(bytes(as_str(obj), 'utf-8')).hexdigest()


def run_task(coro, callback):
    """
    Run awaitable in background task and return immediately

    This method should be used to call coroutine functions and other awaitables
    in a synchronous context.

    The returned task must be collected (e.g. in a :class:`list`) and awaited or
    cancelled eventually.

    :param coro: Any awaitable object
    :param callback: Callable that is called with the returned task when
        `coro` returns, is cancelled or raises any other exception

    :return: :class:`asyncio.Task` instance
    """
    if not callable(callback):
        raise ValueError(f'Not callable: {callable!r}')

    def handle_task_done(task):
        # Call callback no matter what
        try:
            task.result()
        except BaseException:
            callback(task)
        else:
            callback(task)

    task = asyncio.create_task(coro)
    task.add_done_callback(handle_task_done)
    return task


async def run_async(function, *args, **kwargs):
    """
    Run synchronous `function` asynchronously in a thread

    See :meth:`asyncio.BaseEventLoop.run_in_executor`.
    """
    loop = asyncio.get_running_loop()
    wrapped = functools.partial(function, *args, **kwargs)
    return await loop.run_in_executor(None, wrapped)


_NOTHING = object()

def blocking_memoize(coro_func):
    """
    Asynchronous memoization decorator that blocks concurrent calls with the
    same arguments

    The first call calls the decorated function while subsequent calls wait
    until the first call returns and the return value is cached. Subsequent
    calls then get the return value from the cache.

    Exceptions raised by `coro_func` are also cached and re-raised on subsequent
    calls.

    The decorated function provides a `clear_cache` method that removes any
    cached return values.
    """
    cache = {}
    lock = collections.defaultdict(asyncio.Lock)

    @functools.wraps(coro_func)
    async def wrapper(*args, **kwargs):
        cache_key = semantic_hash((str(coro_func), args, kwargs))
        async with lock[cache_key]:
            result = cache.get(cache_key, _NOTHING)

            if result is _NOTHING:
                try:
                    result = await coro_func(*args, **kwargs)
                except BaseException as e:
                    result = e
                cache[cache_key] = result

            if isinstance(result, BaseException):
                raise result
            else:
                return result

    def clear_cache():
        cache.clear()

    wrapper.clear_cache = clear_cache

    return wrapper


def flatten_nested_lists(thing):
    """
    Return flattened :class:`list`

    :param thing: Arbitrarily nested iterables

    If `thing` is not an iterable (and not a string), it is returned inside a
    list.
    """
    def flatten(x):
        if isinstance(x, collections.abc.Iterable) and not isinstance(x, (str, bytes)):
            for item in x:
                yield from flatten(item)
        else:
            yield x

    return list(flatten(thing))


# We must import these here to prevent circular imports
from . import (  # noqa: E402 isort:skip
    argtypes,
    bbcode,
    browser,
    config,
    country,
    daemon,
    disc,
    fs,
    html,
    http,
    image,
    mediainfo,
    predbs,
    release,
    signal,
    string,
    subproc,
    torrent,
    types,
    update,
    webdbs,
)
