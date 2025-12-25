"""
Abstract base class for online databases
"""

import abc
import asyncio
import copy
import re
import string

import unidecode

from .. import country, http
from .common import Query

import logging  # isort:skip
_log = logging.getLogger(__name__)


class WebDbApiBase(abc.ABC):
    """
    Base class for all web DB APIs

    Not all DBs provide all information. Methods that take an `id` argument may
    return an empty string, an empty tuple or `None`.
    """

    def __init__(self, config=None):
        self._config = copy.deepcopy(self.default_config)
        if config is not None:
            self._config.update(config.items())

    @property
    @abc.abstractmethod
    def name(self):
        """Unique name of this DB"""

    @property
    @abc.abstractmethod
    def label(self):
        """User-facing name of this DB"""

    @property
    def no_results_info(self):
        """
        Hints for the user to find something

        This should be displayed if there are no search results.
        """
        return ''

    @property
    def config(self):
        """
        User configuration

        This is a deep copy of :attr:`default_config` that is updated with the
        `config` argument from initialization.
        """
        return self._config

    @property
    @abc.abstractmethod
    def default_config(self):
        """Default user configuration as a dictionary"""

    def sanitize_query(self, query):
        """
        Modify :class:`.Query` for specific DB

        If :meth:`get_id_from_text` finds an ID in :attr:`.Query.title`,
        :attr:`.Query.id` is set to that ID, which means all other query
        parameters are ignored.
        """
        if not isinstance(query, Query):
            raise TypeError(f'Not a Query instance: {query!r}')
        else:
            id_from_url = self.get_id_from_text(query.title)
            if id_from_url:
                query.id = id_from_url
            return query

    @abc.abstractmethod
    def get_id_from_text(self, text):
        """Return ID found in `text` or `None`"""

    @abc.abstractmethod
    async def search(self, query):
        """
        Search DB

        :param query: :class:`~.common.Query` instance

        :return: List of :class:`~.common.SearchResult` instances
        """

    @abc.abstractmethod
    async def cast(self, id):
        """Return list of cast names"""

    async def countries(self, id):
        """Return list of country names"""
        countries = await self._countries(id)
        return country.name(countries)

    @abc.abstractmethod
    async def _countries(self, id):
        pass

    @abc.abstractmethod
    async def creators(self, id):
        """Return list of creator names (usually empty for movies and episodes)"""

    @abc.abstractmethod
    async def directors(self, id):
        """Return list of director names (usually empty for series)"""

    @abc.abstractmethod
    async def genres(self, id):
        """Return list of genres"""

    @abc.abstractmethod
    async def poster_url(self, id, season=None):
        """
        Return URL of poster image or empty string

        :param season: Return poster for specific season

            If this is not supported by the concrete implementation, default to
            the URL for the main poster.
        """

    async def poster(self, id, season=None):
        """
        Return poster image as binary data or `None`

        :param season: Return poster for specific season

            If this is not supported by the concrete implementation, default to
            the main poster.
        """
        poster_url = await self.poster_url(id, season=season)
        if poster_url:
            response = await http.get(
                poster_url,
                user_agent='BROWSER',
                cache=True,
            )
            return response.bytes
        return None

    @abc.abstractmethod
    async def rating(self, id):
        """Return rating as a number or `None`"""

    @property
    @abc.abstractmethod
    async def rating_min(self):
        """Minimum :meth:`rating` value"""

    @property
    @abc.abstractmethod
    async def rating_max(self):
        """Maximum :meth:`rating` value"""

    async def runtimes(self, id):
        """
        Return mapping of runtimes

        Keys are descriptive strings (e.g. "Director's Cut", "Ultimate Cut",
        etc) and values are the runtime in minutes (:class:int).

        The key of the default cut is ``default``.
        """
        runtimes = {}
        for key, runtime in (await self._runtimes(id)).items():
            country_name = country.name(key)
            if country_name not in runtimes and runtime not in runtimes.values():
                runtimes[country_name] = runtime
        return runtimes

    @abc.abstractmethod
    async def _runtimes(self, id):
        pass

    @abc.abstractmethod
    async def summary(self, id):
        """Return short plot description"""

    @abc.abstractmethod
    async def _title_original(self, id):
        """Return original title"""

    @abc.abstractmethod
    async def _titles_english(self, id):
        """
        Return sequence of English titles (e.g. for different
        English-speaking countries)

        :meth:`title_english` picks one that is not too similar to the original
        title.
        """

    async def title_original(self, id):
        """
        Return original title

        See also :meth:`title_english`.
        """
        if id:
            return await self._title_original(id)
        return ''

    async def title_english(self, id, *, default_to_original=False):
        """
        Return English title (AKA) or empty string

        If the English title is too similar to the original title, return an
        empty string.

        Titles are considered too similar if they are equal or either one
        contains the other after normalization.

        Titles are normalized by casefolding, removing whitespace, translating
        roman numerals to arabic, etc.

        For example, if the original title is "Föö & Bár II" and the English
        title is "The Foo and Bar 2", the titles are too similar.

        :param default_to_original: Instead of defaulting to an empty string if
            no appropriate English title is found, default to the original title
        """
        if id:
            english_titles = await self._titles_english(id)
            original_title = await self._title_original(id)
            for english_title in english_titles:
                # Don't return English title if it is similar to original title
                # (e.g. english_title="The Foo", original_title="Föó")
                if not self._titles_are_similar(english_title, original_title):
                    # _log.debug('Using English title: %r', english_title)
                    return english_title
                # else:
                #     _log.debug('English title is too similar to original: %r == %r', english_title, original_title)

            # Return the first English title if we can't return empty string
            if default_to_original:
                # _log.debug('Defaulting to original title: %r', original_title)
                return original_title

        return ''

    def _titles_are_similar(self, a, b):
        """Whether normalized `a` contains normalized `b` or vice versa"""
        an = self._normalize_title(a)
        bn = self._normalize_title(b)
        return an and bn and (an in bn or bn in an)

    def _normalize_title(self, title):
        """Return casefolded `title` normalized punctuation, whitespace, etc"""
        # Replace special characters with similar ASCII
        title = title.replace('&', 'and')
        title = unidecode.unidecode(title)

        # Remove all punctuation
        title = re.sub(rf'[{string.punctuation}]+', '', title)

        # Deduplicate whitespace into spaces (U+0020)
        title = ' '.join(title.split())

        # Remove difference between arabic and roman numbers
        def normalize_part(match):
            num = match.group(1)
            if num.isdigit():
                num_arabic = num
                num_roman = int(num) * 'I'
            else:
                num_arabic = len(num)
                num_roman = num
            return f'{num_arabic}/{num_roman}'

        title = re.sub(r'\b((?i:I+|\d+))\b', normalize_part, title)

        # Remove all whitespace
        title = ''.join(title.split())

        # Case-insensitivize
        title = title.casefold()

        return title

    @abc.abstractmethod
    async def type(self, id):
        """Return :class:`~.types.ReleaseType`"""

    @abc.abstractmethod
    async def url(self, id):
        """Return URL for `id`"""

    @abc.abstractmethod
    async def year(self, id):
        """Return release year or empty string"""

    async def gather(self, id, *methods):
        """
        Fetch information concurrently

        :param id: Valid ID for this DB
        :param methods: Names of coroutine methods of this class
        :type methods: sequence of :class:`str`

        :return: Dictionary that maps `methods` to return values
        """
        corofuncs = (getattr(self, method) for method in methods)
        awaitables = (corofunc(id) for corofunc in corofuncs)
        results = await asyncio.gather(*awaitables)
        dct = {'id': id}
        # "The order of result values corresponds to the order of awaitables in `awaitables`."
        # https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently
        dct.update((method, result) for method, result in zip(methods, results))
        return dct
