"""
CLI argument types

All types return normalized values and raise ValueError for invalid values.
"""

import collections
import enum
import functools
import os
import pathlib
import re

import logging  # isort:skip
_log = logging.getLogger(__name__)


@functools.cache
def Integer(min=None, max=None):
    """
    Return :class:`int` subclass with minimum and maximum value

    >>> i = Integer(min=0, max=10)
    >>> i(100)
    >>> ValueError: Maximum is 10
    """
    # There's a Python bug that prevents us from overloading min() and max()
    # with variables in the "class ...:" namespace
    min_ = min
    max_ = max

    class Integer(int):
        min = min_
        """Minimum value"""

        max = max_
        """Maximum value"""

        def __new__(cls, value):
            try:
                i = int(float(value))
            except (ValueError, TypeError) as e:
                raise ValueError(f'Invalid integer value: {value!r}') from e

            if cls.min is not None and i < cls.min:
                raise ValueError(f'Minimum is {cls.min}')
            elif cls.max is not None and i > cls.max:
                raise ValueError(f'Maximum is {cls.max}')
            else:
                return super().__new__(cls, i)

        def __str__(self):
            return str(int(self))

        def __repr__(self):
            string = f'{type(self).__name__}({super().__repr__()}'
            if min is not None:
                string += f', min={min!r}'
            if max is not None:
                string += f', max={max!r}'
            string += ')'
            return string

    return Integer


@functools.cache
def Choice(options, *, empty_ok=False, case_sensitive=True):
    """
    Return :class:`str` subclass that can only have instances that are equal to an item of
    `options`

    :param options: Iterable of allowed instances
    :param bool empty_ok: Whether an emptry string is valid even if it is not in
        `options`
    :param bool case_sensitive: Whether case is considered

    :raise ValueError: if instantiation is attempted with a value that is not in
        `options`
    """
    if case_sensitive:
        options_str = tuple(sorted(str(o) for o in options))
    else:
        options_str = tuple(sorted(str(o).lower() for o in options))

    # There's a Python bug that prevents us from overloading min() and max()
    # with variables in the "class ...:" namespace
    empty_ok_ = empty_ok
    case_sensitive_ = case_sensitive

    class Choice(str):
        options = options_str

        empty_ok = bool(empty_ok_)
        """Whether an empty string is a valid option"""

        case_sensitive = bool(case_sensitive_)
        """Whether case in options matters"""

        def __new__(cls, val):
            val_str = str(val)
            if not case_sensitive:
                val_str = val_str.lower()

            if val_str not in cls.options and (val_str or not empty_ok):
                raise ValueError(f'Not one of {", ".join(cls.options)}: {val}')
            else:
                return super().__new__(cls, val)

        def __str__(self):
            return super().__str__()

        def __repr__(self):
            return f'{type(self).__name__}({super().__repr__()}, options={self.options!r})'

    return Choice


def Imagehost(allowed=None, disallowed=None):
    """
    Return new :class:`Choice` subclass that only accepts `allowed`
    image host names

    :param allowed: Sequence of allowed image host names or `None`
        to allow all supported image host names
    :param disallowed: Sequence of disallowed image host names or `None`
        to allow all supported image host names
    """
    if allowed:
        options = set(allowed)
    else:
        from .. import imagehosts
        options = set(imagehosts.imagehost_names())

    if disallowed:
        for item in disallowed:
            options.discard(item)

    Imagehost = Choice(
        options=tuple(sorted(options)),
        case_sensitive=False,
    )
    Imagehost.__name__ = 'Imagehost'
    Imagehost.__qualname__ = Imagehost.__name__
    Imagehost.__doc__ = "Name of a supported image hosting service"
    return Imagehost


class Bool(str):
    """
    :class:`str` subclass with boolean value

    Truthy strings: ``true``, ``yes``, ``on``, ``1``
    Falsy strings: ``false``, ``no``, ``off``, ``0``
    """

    truthy = ('true', 'yes', '1', 'on', 'aye')
    """Valid `True` values (case-insensitive)"""

    falsy = ('false', 'no', '0', 'off', 'nay')
    """Valid `False` values (case-insensitive)"""

    _truthy = re.compile(r'^(?:' + '|'.join(truthy) + ')$', flags=re.IGNORECASE)
    _falsy = re.compile(r'^(?:' + '|'.join(falsy) + ')$', flags=re.IGNORECASE)

    def __new__(cls, value):
        self = super().__new__(cls, value)
        if cls._truthy.search(self):
            self._bool = True
        elif cls._falsy.search(self):
            self._bool = False
        else:
            raise ValueError(f'Invalid boolean value: {value}')
        return self

    def __bool__(self):
        return self._bool

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other._bool == self._bool
        elif isinstance(other, bool):
            return other == self._bool
        else:
            return NotImplemented

    def __repr__(self):
        return f'{type(self).__name__}({super().__str__()!r})'


class Bytes(int):
    """:class:`int` subclass with binary or decimal unit prefix"""

    _regex = re.compile(r'^(\d+(?:\.\d+|)) ?([a-zA-Z]{,3})$')
    _multipliers = {
        '': 1,
        'k': 1000,
        'M': 1000**2,
        'G': 1000**3,
        'T': 1000**4,
        'P': 1000**5,
        'Ki': 1024,
        'Mi': 1024**2,
        'Gi': 1024**3,
        'Ti': 1024**4,
        'Pi': 1024**5,
    }

    @classmethod
    def from_string(cls, string):
        """Parse `string` like ``4kB`` or ``1.024 KiB``"""
        match = cls._regex.search(string)
        if not match:
            raise ValueError(f'Invalid size: {string}')
        else:
            number = match.group(1)
            unit = match.group(2)
            if unit and unit[-1] == 'B':
                unit = unit[:-1]
            try:
                multiplier = cls._multipliers[unit]
            except KeyError as e:
                raise ValueError(f'Invalid unit: {unit}') from e
            else:
                return cls(int(float(number) * multiplier))

    def __new__(cls, value):
        if isinstance(value, str):
            return cls.from_string(value)
        else:
            return super().__new__(cls, value)

    def format(self, *, prefix='shortest', decimal_places=2, trailing_zeros=False):
        """
        Return human-readable string

        :param str prefix: Unit prefix, must be one of ``binary`` (1000 -> "1
            kB"), ``decimal`` (1024 -> "1 KiB") or ``shortest`` (automatically
            pick the string representation with the fewest decimal places)
        :param int decimal_places: How many decimal places to include
        :param bool trailing_zeros: Whether to remove zeros on the right of the
            decimal places
        """
        decimal_multipliers = (
            (prefix, multiplier)
            for prefix, multiplier in reversed(tuple(self._multipliers.items()))
            if len(prefix) == 1
        )
        binary_multipliers = (
            (prefix, multiplier)
            for prefix, multiplier in reversed(tuple(self._multipliers.items()))
            if len(prefix) == 2
        )

        string_format = f'{{number:.{decimal_places}f}}'

        def get_string(prefix, multipliers):
            for prefix, multiplier in multipliers:
                if self >= multiplier:
                    number = strip_trailing_zeros(string_format.format(number=self / multiplier))
                    return f'{number} {prefix}B'
            number = strip_trailing_zeros(string_format.format(number=int(self)))
            return f'{number} B'

        def strip_trailing_zeros(string):
            # Only strip zeros from decimal places (not from "100")
            if not trailing_zeros and '.' in string:
                return string.rstrip('0').rstrip('.') or '0'
            else:
                return string

        def number_of_decimal_places(string):
            number = str(''.join(c for c in str(string) if c in '1234567890.'))
            if '.' in number:
                return len(number.split('.', maxsplit=1)[1])
            else:
                return 0

        if prefix == 'binary':
            return get_string(prefix, binary_multipliers)
        elif prefix == 'decimal':
            return get_string(prefix, decimal_multipliers)
        elif prefix == 'shortest':
            decimal_string = get_string(prefix, decimal_multipliers)
            binary_string = get_string(prefix, binary_multipliers)
            sorted_strings = sorted((decimal_string, binary_string),
                                    key=number_of_decimal_places)
            return sorted_strings[0]
        else:
            raise ValueError(f'Invalid prefix: {prefix!r}')

    def __str__(self):
        return self.format()

    def __repr__(self):
        return f'{type(self).__name__}({int(self)!r})'


class Timestamp(float):
    """
    Subclass of :class:`float` that can parse and format timestamp/duration strings

    :param seconds: Number of seconds or hours, minutes and seconds as ":"-separated string
    :type seconds: int or float or "[[H+:]M+:]S+"

    :raise ValueError: if `seconds` is not a valid timestamp
    :raise TypeError: if `seconds` is not a :class:`int`, :class:`float` or :class:`str`
    """
    def __new__(cls, seconds):
        if isinstance(seconds, str):
            return cls.from_string(seconds)
        elif not isinstance(seconds, (int, float)):
            raise TypeError(f'Not a string or number: {seconds!r}')
        elif seconds < 0:
            raise ValueError(f'Timestamp must not be negative: {seconds!r}')
        else:
            return super().__new__(cls, round(seconds, 3))

    def __str__(self):
        text = ':'.join((
            f'{int(self / 3600)}',
            f'{int(self % 3600 / 60):02d}',
            f'{int(self % 3600 % 60):02d}',
        ))
        decimal_places = round(self - int(self), 3)
        if decimal_places > 0:
            text += f'.{str(decimal_places)[2:]}'
        return text

    def __repr__(self):
        return f'{type(self).__name__}({str(self)!r})'

    @classmethod
    def from_string(cls, string):
        """
        Parse string of the format "[[H+:]MM:]SS"

        :param str string: Hours, minutes and seconds as ":"-separated string or number of seconds

        :raise ValueError: if `string` has an invalid format
        """
        try:
            parts = tuple(float(part) for part in str(string).split(':'))
        except ValueError as e:
            raise ValueError(f'Invalid timestamp: {string!r}') from e

        for part in parts:
            if part < 0:
                raise ValueError(f'Timestamp must not be negative: {string}')

        if len(parts) == 3:
            hours, mins, secs = parts
        elif len(parts) == 2:
            hours = 0
            mins, secs = parts
        elif len(parts) == 1:
            hours = mins = 0
            secs = parts[0]
        else:
            raise ValueError(f'Invalid timestamp: {string}')

        return cls((hours * 3600) + (mins * 60) + secs)


class ReleaseType(enum.Enum):
    """
    Enum with the values ``movie``, ``season``, ``episode`` and
    ``unknown``

    ``series`` is an alias for ``season``.

    All values are truthy except for ``unknown``.
    """

    movie = 'movie'
    season = 'season'
    series = 'season'
    episode = 'episode'
    unknown = 'unknown'

    def __bool__(self):
        return self is not self.unknown

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f'{type(self).__name__}.{self.value}'


class SceneCheckResult(enum.Enum):
    """
    Enum with the values ``true``, ``false``, ``renamed``, ``altered`` and
    ``unknown``

    All values are falsy except for ``true``.
    """

    true = 'true'
    false = 'false'
    renamed = 'renamed'
    altered = 'altered'
    unknown = 'unknown'

    def __bool__(self):
        return self is self.true

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f'{type(self).__name__}.{self.value}'


class Regex:
    """
    Special class that behaves like :class:`re.Pattern` (return value of
    :func:`re.compile`) but more intuitively

    Its string representation is :attr:`re.Pattern.pattern` instead of
    ``re.compile('<pattern>')``.

    Instead of raising :class:`re.error`, it raises :class:`ValueError` on
    invalid regular expressions.

    :raise ValueError: instead of :class:`re.error`
    """

    def __init__(self, pattern):
        if isinstance(pattern, type(self)):
            self._regex = pattern._regex
        else:
            try:
                self._regex = re.compile(pattern)
            except re.error as e:
                orig_msg = str(e)
                msg = orig_msg[0].upper() + orig_msg[1:]
                raise ValueError(f'{pattern}: {msg}') from e

    def __getattr__(self, name):
        return getattr(self._regex, name)

    def __str__(self):
        return self._regex.pattern

    def __repr__(self):
        return f'{type(self).__name__}({self._regex.pattern!r})'

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._regex.pattern == other._regex.pattern
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self._regex)

    # Prevent maximum recursion error in __getattr__().
    # See: https://docs.python.org/3/library/pickle.html#object.__reduce__
    def __reduce__(self):
        return (type(self), (self._regex.pattern,))

    # If we copy.deepcopy() instances of this class (e.g. `ListOf(Regex)` that
    # is used for trackers.*.exclude settings, we end up with `re.compile(...)`
    # instances for some reason. Implementing __deepcopy__() fixes that.
    def __deepcopy__(self, memo):
        return type(self)(self._regex.pattern)


@functools.cache
def ListOf(item_type, separator=None):
    """
    Return immutable sequence type that can only contain `item_type` objects

    :param item_type: Any callable that returns a valid object for any items added to the list or
        raises :class:`ValueError` or :class:`TypeError`

    :raise ValueError: if any invalid value is added to the list

    :return: subclass of :class:`~.collections.abc.Sequence`
    """

    # Avoid NameError bug (https://github.com/python/cpython/issues/87546)
    item_type_ = item_type
    separator_ = separator

    class ListOf(collections.abc.Sequence):

        item_type = item_type_
        separator = separator_

        @classmethod
        def _convert(cls, item):
            if isinstance(item, str):
                # Empty string.
                if not item:
                    yield from ()

                # Split `item` into multiple items at `separator`.
                elif separator and separator in item:
                    for subitem in item.split(separator):
                        yield from cls._convert(subitem.strip())

                # `item` is a single item.
                else:
                    try:
                        yield cls.item_type(item)
                    except (ValueError, TypeError) as e:
                        raise ValueError(f'Invalid value: {item}') from e

            # `item` is multiple values
            elif isinstance(item, collections.abc.Iterable):
                for subitem in item:
                    yield from cls._convert(subitem)

            # `item` is single value
            else:
                try:
                    yield cls.item_type(item)
                except (ValueError, TypeError) as e:
                    raise ValueError(f'Invalid value: {item!r}') from e

        def __new__(cls, items=()):
            self = super().__new__(cls)
            self._sequence = tuple(self._convert(items))
            return self

        def __getitem__(self, key):
            return self._sequence[key]

        def __len__(self):
            return len(self._sequence)

        def __eq__(self, other):
            if hasattr(other, 'item_type') and hasattr(other, '_sequence'):
                return (
                    self.item_type is other.item_type
                    and self._sequence == other._sequence
                )
            elif isinstance(other, collections.abc.Sequence):
                return self._sequence == tuple(other)
            else:
                return NotImplemented

        def __hash__(self):
            return hash((
                self.item_type,
                self._sequence,
            ))

        def __str__(self):
            return ', '.join(
                str(item)
                for item in self._sequence
            )

        def __repr__(self):
            return f'{type(self).__name__}({self._sequence!r})'

    # Specify class name for easier debugging (e.g. "ListOfSomeClassName")
    ListOf.__name__ = (
        'ListOf'
        + item_type.__name__[0].upper()
        + item_type.__name__[1:]
    )
    ListOf.__qualname__ = ListOf.__name__
    ListOf.__doc__ = f"""Immutable list of {item_type_.__qualname__}"""

    # Instantiate custom list with provided items
    return ListOf


class PathTranslation:
    """
    Translate beginning of path

    :param str string: Translation in the form of ``/from/path -> /to/path``

    Windows paths are detected by a single ASCII letter followed by a colon (e.g. ``c:``) at the
    beginning of a path. All other paths are interpreted as POSIX.

    ``~`` is interpreted via :func:`os.path.expanduser` for local paths.
    """

    @staticmethod
    def _get_pure_path(path, *, is_local=False):
        if isinstance(path, pathlib.PurePath):
            return path
        elif isinstance(path, str):
            path = os.path.expanduser(path) if is_local else path
            if re.search(r'^[a-zA-Z]:', path):
                return pathlib.PureWindowsPath(path)
            else:
                return pathlib.PurePath(path)
        else:
            raise TypeError(f'Unsupported path type: {type(path).__name__}: {path!r}')

    _regex = re.compile(r'^\s*(.+?)\s*->\s*(.+?)\s*$')

    def __init__(self, string):
        match = self._regex.search(str(string))
        if match:
            local, remote = match.groups()
            self._local = self._get_pure_path(local, is_local=True)
            self._remote = self._get_pure_path(remote, is_local=False)
        else:
            raise ValueError(f'Invalid path translation: {string}')

    @property
    def local(self):
        """:class:`pathlib.PurePath` instance of the first/source path"""
        return self._local

    @property
    def remote(self):
        """:class:`pathlib.PurePath` instance of the second/target path"""
        return self._remote

    def translate(self, path):
        """
        Replace :attr:`local` at the beginning of `path` with :attr:`remote`

        The returned path is always translated to the :attr:`remote` path flavour (POSIX or
        Windows).

        If `path` does not start with :attr:`local`, return ``None``.
        """
        pure = self._get_pure_path(path)
        matching_parts = self.local.parts
        if pure.parts[:len(matching_parts)] == matching_parts:
            tail = pure.parts[len(matching_parts):]
            translated = str(self.remote.joinpath(*tail))
            _log.debug('Translated path: %r with %r to %r', path, self, translated)
            return translated
        else:
            _log.debug('Path translation does not match: %r != %r', pure.parts[:len(matching_parts)], matching_parts)

    def __str__(self):
        return f'{self.local} -> {self.remote}'

    def __repr__(self):
        return f'<{type(self).__name__} {self.local!r} -> {self.remote!r}>'


class PathTranslations(ListOf(PathTranslation)):
    """
    :class:`~.types.ListOf` :class:`PathTranslation` instances
    """

    def translate(self, path):
        """
        Use the first matching :class:`PathTranslation` to translate `path`

        Return `path` unmodified by default.
        """
        for translation in self:
            if path_translated := translation.translate(path):
                return path_translated
        return path
