"""
Classes and functions that are used by all :class:`~.base.WebDbApiBase`
subclasses
"""

import os
import re

from .. import country, release, signal
from ..types import ReleaseType

import logging  # isort:skip
_log = logging.getLogger(__name__)


class Query:
    """
    Search query for databases like IMDb

    :param str title: Name of the movie or TV series
    :param type: :class:`~.types.ReleaseType` enum or one of its value names
    :param year: Year of release
    :type year: str or int
    :param str id: Known ID for a specific DB
    :param bool feeling_lucky: Whether an only search result should be
        autoselected

        This can be convenient if `id` is provided.

    :raise ValueError: if an invalid argument is passed
    """

    @staticmethod
    def _normalize_title(title):
        return ' '.join(title.casefold().strip().split())

    _kwarg_defaults = {
        'year': None,
        'type': ReleaseType.unknown,
        'id': None,
        'feeling_lucky': False,
    }

    def __init__(self, title='', **kwargs):
        for k in kwargs:
            if k not in self._kwarg_defaults:
                raise TypeError(f'Unkown argument: {k!r}')
        self._signal = signal.Signal(id=f'{title}-query', signals=('changed',))
        self.title = title
        self.type = kwargs.get('type', self._kwarg_defaults['type'])
        self.year = kwargs.get('year', self._kwarg_defaults['year'])
        self.id = kwargs.get('id', self._kwarg_defaults['id'])
        self.feeling_lucky = kwargs.get('feeling_lucky', self._kwarg_defaults['feeling_lucky'])

    @property
    def type(self):
        """:class:`~.types.ReleaseType` value"""
        return self._type

    @type.setter
    def type(self, type):
        before = getattr(self, '_type', None)

        self._type = ReleaseType(type)

        if self._type != before:
            self.signal.emit('changed', self)

    @property
    def title(self):
        """Name of the movie or TV series"""
        return self._title

    @title.setter
    def title(self, title):
        before = getattr(self, '_title_normalized', None)

        self._title = str(title)
        self._title_normalized = self._normalize_title(self.title)

        if self._title_normalized != before:
            self.signal.emit('changed', self)

    @property
    def title_normalized(self):
        """Same as :attr:`title` but in stripped lower case with deduplicated spaces"""
        return self._title_normalized

    @property
    def year(self):
        """Year of release"""
        return self._year

    @year.setter
    def year(self, year):
        before = getattr(self, '_year', None)

        if not year:
            self._year = None
        else:
            try:
                year_int = int(year)
            except (TypeError, ValueError) as e:
                raise ValueError(f'Invalid year: {year}') from e
            else:
                if not 1800 < year_int < 2100:
                    raise ValueError(f'Invalid year: {year}')
                else:
                    self._year = str(year_int)

        if self._year != before:
            self.signal.emit('changed', self)

    @property
    def id(self):
        """Known ID for a specific DB"""
        return self._id

    @id.setter
    def id(self, id):
        before = getattr(self, '_id', None)

        self._id = str(id) if id else None

        if self._id != before:
            self.signal.emit('changed', self)

    @property
    def feeling_lucky(self):
        """Whether an only search result should be autoselected"""
        return self._feeling_lucky

    @feeling_lucky.setter
    def feeling_lucky(self, feeling_lucky):
        before = getattr(self, '_feeling_lucky', None)

        self._feeling_lucky = bool(feeling_lucky)

        if self._feeling_lucky != before:
            self.signal.emit('changed', self)

    def update(self, query, *, silent=False):
        """
        Copy property values from other query

        :param query: :class:`Query` instance to copy values from
        :param bool silent: Whether to prevent any :attr:`signal` emissions
        """
        before = str(self)

        with self.signal.suspend('changed'):
            for attr in ('title', 'type', 'year', 'id', 'feeling_lucky'):
                other_value = getattr(query, attr)
                setattr(self, attr, other_value)

        if not silent and str(self) != before:
            self.signal.emit('changed', self)

    def copy(self, **updates):
        """
        Return new :class:`Query` instance with updated attributes

        :param updates: Updated attributes
        """
        kwargs = {
            'title': self.title,
            'type': self.type,
            'year': self.year,
            'id': self.id,
            'feeling_lucky': self.feeling_lucky,
        }
        kwargs.update(updates)
        return type(self)(**kwargs)

    _types = {
        ReleaseType.movie: ('movie', 'film'),
        ReleaseType.season: ('season', 'series', 'tv', 'show', 'tvshow'),
        ReleaseType.episode: ('episode',),
    }
    _kw_regex = {
        'year': r'year:(\S*)',
        'type': r'type:(\S*)',
        'id': r'id:(\S*)',
    }

    @classmethod
    def from_string(cls, query):
        """
        Create instance from string

        The returned :class:`Query` is case-insensitive and has any superfluous
        whitespace removed.

        Keyword arguments are extracted by looking for ``"year:YEAR"``,
        ``"type:TYPE"`` and ``"id:ID"`` in `query` where ``YEAR`` is a
        four-digit number, ``TYPE`` is something like "movie", "film", "tv", etc
        and ``ID`` is a known ID for the DB this query is meant for.
        """
        def get_kwarg(string):
            for kw, regex in cls._kw_regex.items():
                match = re.search(f'^{regex}$', string)
                if match:
                    value = match.group(1)
                    if kw == 'type':
                        if value in cls._types[ReleaseType.movie]:
                            return 'type', ReleaseType.movie
                        elif value in cls._types[ReleaseType.season]:
                            return 'type', ReleaseType.season
                        elif value in cls._types[ReleaseType.episode]:
                            return 'type', ReleaseType.episode
                        elif not value:
                            return 'type', ReleaseType.unknown
                    elif kw == 'year':
                        return 'year', value
                    elif kw == 'id':
                        return 'id', value
                    raise ValueError(f'Invalid {kw}: {value}')
            return None, None

        query = query.strip()
        title = []
        kwargs = {}

        # "I'm feeling lucky" if query starts with "!".
        if query and query[0] == '!':
            kwargs['feeling_lucky'] = True
            query = query[1:]

        # Extract "key:value" pairs (e.g. "year:2015")
        for part in str(query).strip().split():
            kw, value = get_kwarg(part)
            if (kw, value) != (None, None):
                kwargs[kw] = value
            else:
                title.append(part)

        if title:
            kwargs['title'] = ' '.join(title)

        return cls(**kwargs)

    @classmethod
    def from_release(cls, info):
        """
        Create instance from :class:`~.release.ReleaseInfo` or
        :class:`~.release.ReleaseName` instance
        """
        kwargs = {'title': info['title']}
        if info.get('year') and info.get('year') != 'UNKNOWN_YEAR':
            kwargs['year'] = info['year']
        if info.get('type'):
            kwargs['type'] = info['type']
        return cls(**kwargs)

    @classmethod
    def from_path(cls, path):
        """
        Create instance from file or directory name

        `path` is passed to :class:`~.release.ReleaseInfo` to get the
        arguments for instantiation.
        """
        info = release.ReleaseInfo(str(path))
        return cls.from_release(info)

    @classmethod
    def from_any(cls, obj):
        """
        Try to guess correct `from_…` method

        :raise TypeError: if `obj` is not supported
        """
        if isinstance(obj, cls):
            return obj
        elif isinstance(obj, str):
            if os.sep in obj or os.path.exists(obj):
                return cls.from_path(obj)
            else:
                return cls.from_string(obj)
        elif isinstance(obj, (release.ReleaseInfo, release.ReleaseName)):
            return cls.from_release(obj)
        else:
            raise TypeError(f'Unsupported type: {type(obj).__name__}: {obj!r}')

    @property
    def signal(self):
        """
        :class:`~.signal.Signal` instance

        Available signals:

        ``changed``
            Emitted after query parameters changed. Registered callbacks get the
            instance as a positional argument.
        """
        return self._signal

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return (
                self.title_normalized == other.title_normalized
                and self.year == other.year
                and self.type is other.type
                and self.id == other.id
            )
        else:
            return NotImplemented

    def __str__(self):
        if self.id:
            text = f'id:{self.id}'
        else:
            parts = [self.title]
            for attr in ('type', 'year', 'id'):
                value = getattr(self, attr)
                if value:
                    parts.append(f'{attr}:{value}')
            text = ' '.join(parts)

        if self.feeling_lucky:
            text = f'!{text}'

        return text

    def __repr__(self):
        kwargs = ', '.join(
            f'{k}={v!r}'
            for k, v in (
                ('title', self.title),
                ('year', self.year),
                ('type', self.type),
                ('id', self.id),
                ('feeling_lucky', self.feeling_lucky),
            )
            if v
        )
        return f'{type(self).__name__}({kwargs})'


class SearchResult:
    """
    Information about a search result

    Keyword arguments are available as attributes.

    Normal attributes:

    :param str id: ID for the relevant DB
    :param str title: Title of the movie or series
    :param str type: :class:`~.types.ReleaseType` value
    :param str url: Web page of the search result
    :param str year: Release year; for series this should be the year of the
        first airing of the first episode of the first season

    These attributes are coroutine functions that return the value when called
    with no arguments:

    :param cast: Short list of actor names
    :type cast: sequence of :class:`str`
    :param str countries: List of country names of origin
    :param genres: Short sequence of genres, e.g. `["horror", "comedy"]`
    :type genres: sequence of :class:`str`
    :param str directors: Sequence of directors
    :type directors: sequence of :class:`str`
    :param summary: Short text that describes the movie or series
    :param str title_english: English title of the movie or series
    :param str title_original: Original title of the movie or series

    The values of coroutine functions can be supplied via a coroutine function
    or as a plain object (:class:`str`, :class:`list`, etc).
    """

    def __init__(self, *, id, type, url, year, cast=(), countries=(), directors='',
                 genres=(), poster=None, summary='', title, title_english='', title_original=''):
        self._info = {
            # Normal attributes functions
            'id': id,
            'title': str(title),
            'type': ReleaseType(type),
            'url': str(url),
            'year': str(year),
            # Coroutine functions
            'cast': self._ensure_async_getter('cast', cast),
            'countries': self._ensure_async_getter('countries', countries),
            'directors': self._ensure_async_getter('directors', directors),
            'genres': self._ensure_async_getter('genres', genres),
            'poster': self._ensure_async_getter('poster', poster),
            'summary': self._ensure_async_getter('summary', summary),
            'title_english': self._ensure_async_getter('title_english', title_english),
            'title_original': self._ensure_async_getter('title_original', title_original),
        }

    def __getattr__(self, name):
        try:
            return self._info[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def _ensure_async_getter(self, name, value):
        async def async_getter():
            # TODO: If Python 3.9 is no longer supported, use
            #       inspect.iscoroutinefunction() instead of callable().
            if callable(value):
                return self._upgrade_value(name, await value())
            else:
                return self._upgrade_value(name, value)

        async_getter.__qualname__ = f'async_get_{name}'
        return async_getter

    def _upgrade_value(self, name, value):
        if name == 'countries':
            return country.name(value)
        else:
            return value

    def __repr__(self):
        kwargs = ', '.join(f'{k}={v!r}' for k, v in self._info.items())
        return f'{type(self).__name__}({kwargs})'


class Person(str):
    """
    :class:`str` subclass with an `url` attribute

    The optional `role` should only be used for actors and be the name of the character they
    portray.
    """

    __slots__ = ('role', 'url')

    def __new__(cls, name, *, url='', role=''):
        obj = super().__new__(cls, name)
        obj.url = (str(url) or '').strip()
        obj.role = (str(role) or '').strip()
        return obj

    def __repr__(self):
        args = repr(str(self))
        if self.url:
            args += f', url={self.url!r}'
        if self.role:
            args += f', role={self.role!r}'
        return f'{type(self).__name__}({args})'
