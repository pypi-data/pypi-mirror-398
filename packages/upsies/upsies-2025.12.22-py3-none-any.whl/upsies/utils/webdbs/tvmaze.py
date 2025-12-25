"""
API for tvmaze.com
"""

import collections
import functools
import json
import re

from ... import errors, utils
from .. import html, http
from ..types import ReleaseType
from . import common
from .base import WebDbApiBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class TvmazeApi(WebDbApiBase):
    """API for tvmaze.com"""

    name = 'tvmaze'
    label = 'TVmaze'

    default_config = {}

    _url_base = 'http://api.tvmaze.com'

    def sanitize_query(self, query):
        """Set :attr:`~.common.Query.type` to :attr:`~.types.ReleaseType.unknown`"""
        query = super().sanitize_query(query)
        query.type = ReleaseType.unknown
        return query

    def get_id_from_text(self, text):
        match = re.search(r'^(\d+)$', text)
        if match:
            return match.group(1)

        # Example URL: https://www.tvmaze.com/shows/36906/gary-and-his-demons
        match = re.search(r'\b(?i:shows)/(\d+)\b', text)
        if match:
            return match.group(1)

    async def search(self, query):
        _log.debug('Searching TVmaze for %s', query)

        if query.id:
            show = await self._get_show(query.id)
            return [_TvmazeSearchResult(show=show, tvmaze_api=self)]

        elif not query.title or query.type is ReleaseType.movie:
            return []

        else:
            url = f'{self._url_base}/search/shows'
            params = {'q': query.title_normalized}
            results_str = await http.get(url, params=params, cache=True)
            try:
                items = json.loads(results_str)
                assert isinstance(items, list)
            except (ValueError, TypeError, AssertionError) as e:
                raise errors.RequestError(f'Unexpected search response: {results_str}') from e
            else:
                results = tuple(
                    _TvmazeSearchResult(show=item['show'], tvmaze_api=self)
                    for item in items
                )
                # The API doesn't allow us to search for a specific year
                if query.year:
                    return tuple(
                        result
                        for result in results
                        if str(result.year) == query.year
                    )
                else:
                    return results

    async def _get_json(self, url):
        response = await http.get(url, cache=True)
        try:
            info = json.loads(response)
            assert isinstance(info, (collections.abc.Mapping, collections.abc.Sequence))
        except (ValueError, TypeError, AssertionError) as e:
            raise errors.RequestError(f'Unexpected search response: {response}') from e
        else:
            return info

    async def _get_show(self, id):
        url = f'{self._url_base}/shows/{id}?embed[]=cast&embed[]=crew&embed[]=akas'
        return await self._get_json(url)

    async def cast(self, id):
        if id:
            show = await self._get_show(id)
            cast = show.get('_embedded', {}).get('cast', ())
            return tuple(
                common.Person(
                    item['person']['name'],
                    url=item['person'].get('url', ''),
                    role=item['character']['name'],
                )
                for item in utils.deduplicate(cast, key=lambda item: item['person']['name'])
            )
        return ()

    async def _countries(self, id):
        if id:
            show = await self._get_show(id)
            return _get_countries(show)
        return ()

    async def creators(self, id):
        if id:
            show = await self._get_show(id)
            crew = show.get('_embedded', {}).get('crew', ())
            return tuple(
                common.Person(
                    item['person']['name'],
                    url=item['person'].get('url', ''),
                )
                for item in crew
                if item.get('type') == 'Creator' and item.get('person', {}).get('name')
            )
        return ()

    async def directors(self, id):
        return ()

    async def genres(self, id):
        if id:
            show = await self._get_show(id)
            return _get_genres(show)
        return ()

    async def poster_url(self, id, season=None):
        if id:
            info = {}
            if season:
                url = f'{self._url_base}/shows/{id}/seasons'
                seasons = await self._get_json(url)
                for s in seasons:
                    if str(s.get('number')) == str(season) and s.get('image'):
                        info = s
                        break
            if not info:
                info = await self._get_show(id)
            return (info.get('image') or {}).get('original', None)
        return ''

    rating_min = 0.0
    rating_max = 10.0

    async def rating(self, id):
        if id:
            show = await self._get_show(id)
            return show.get('rating', {}).get('average')
        return None

    async def _runtimes(self, id):
        runtimes = {}
        if id:
            show = await self._get_show(id)
            runtime = show.get('runtime', 0)
            if runtime:
                runtimes['default'] = round(int(runtime))
        return runtimes

    async def summary(self, id):
        if id:
            show = await self._get_show(id)
            return _get_summary(show)
        return ''

    async def _title_original(self, id):
        akas = await self._get_akas(id)
        return akas['ORIGIN']

    async def _titles_english(self, id):
        akas = await self._get_akas(id)
        return akas.values()

    async def _get_akas(self, id):
        show = await self._get_show(id)
        akas = {}
        for aka in show.get('_embedded', {}).get('akas', ()):
            # `aka['country']` may also be `None`, which indicates the
            # original country
            country = aka.get('country')
            if country is None:
                akas['ORIGIN'] = aka['name']
            else:
                code = country.get('code', '')
                if code in self._english_country_codes:
                    akas['code'] = aka['name']

        if 'ORIGIN' not in akas:
            akas['ORIGIN'] = show['name']

        return akas

    _english_country_codes = (
        'US',
        'UK',
        'AU',
        'NZ',
    )

    async def type(self, id):
        # TVmaze does not support movies and we can't distinguish between season
        # and episode by ID.
        return ReleaseType.unknown

    async def url(self, id):
        if id:
            show = await self._get_show(id)
            return show.get('url', '')
        return ''

    async def year(self, id):
        if id:
            show = await self._get_show(id)
            return _get_year(show)
        return ''

    async def imdb_id(self, id):
        """Return IMDb ID for TVmaze ID `id` or `None`"""
        if id:
            show = await self._get_show(id)
            imdb_id = show.get('externals', {}).get('imdb')
            if imdb_id:
                return imdb_id
        return ''

    async def episode(self, id, season, episode):
        """
        Get episode information

        :param id: Show ID
        :param season: Season number
        :param episode: Episode number

        :return: :class:`dict` with these keys:

            - ``date`` (:class:`str` as "YYYY-MM-DD")
            - ``episode`` (:class:`str`)
            - ``season`` (:class:`str`)
            - ``summary`` (:class:`str`)
            - ``title`` (:class:`str`)
            - ``url`` (:class:`str`)
        """
        if id:
            url = f'{self._url_base}/shows/{id}/episodebynumber?season={season}&number={episode}'
            episode = await self._get_json(url)
        else:
            episode = {}
        return {
            'date': episode.get('airdate', ''),
            'episode': str(episode.get('number', '')) or '',
            'season': str(episode.get('season', '')) or '',
            'summary': _get_summary(episode),
            'title': episode.get('name', ''),
            'url': episode.get('url', ''),
        }

    async def status(self, id):
        """Return something like "Running", "Ended" or empty string"""
        if id:
            show = await self._get_show(id)
            return show.get('status')
        return ''


class _TvmazeSearchResult(common.SearchResult):
    def __init__(self, *, show, tvmaze_api):
        super().__init__(
            cast=functools.partial(tvmaze_api.cast, show['id']),
            countries=_get_countries(show),
            directors=(),
            id=show['id'],
            genres=_get_genres(show),
            poster=functools.partial(tvmaze_api.poster, show['id']),
            summary=_get_summary(show),
            title=show['name'],
            title_english=functools.partial(tvmaze_api.title_english, show['id']),
            title_original=functools.partial(tvmaze_api.title_original, show['id']),
            type=ReleaseType.series,
            url=show['url'],
            year=_get_year(show),
        )


def _get_summary(show):
    summary = show.get('summary', None)
    if summary:
        soup = html.parse(summary)
        return '\n'.join(paragraph.text for paragraph in soup.find_all('p'))
    else:
        return ''

def _get_year(show):
    premiered = show.get('premiered', None)
    if premiered:
        year = str(premiered).split('-')[0]
        if year.isdigit() and len(year) == 4:
            return year
    else:
        return ''

def _get_genres(show):
    genres = show.get('genres', None)
    if genres:
        return tuple(str(g).lower() for g in genres)
    else:
        return ()

def _get_countries(show):
    info = show.get('network', None) or show.get('webChannel', None)
    if info:
        country = info.get('country', None)
        if country:
            name = country.get('name', None)
            if name:
                return (name,)
    return ''
