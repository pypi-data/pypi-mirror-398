"""
API for imdb.com
"""

import functools
import json
import re

from ... import utils
from ..types import ReleaseType
from . import common
from .base import WebDbApiBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


GRAPHQL_QUERY_SEARCH = """
{
    advancedTitleSearch(
        first: 30,
        sort: { sortBy: POPULARITY, sortOrder: ASC }
        constraints: {%%%CONSTRAINTS%%%}
    ) {
        total
        edges {
            node {
                title {
                    id
                    titleText {
                        text
                    }
                    originalTitleText {
                        text
                    }
                    titleType {
                        id
                    }
                    releaseYear {
                        year
                    }
                    plot {
                        plotText {
                            plainText
                        }
                    }
                    countriesOfOrigin {
                        countries {
                            text
                        }
                    }
                }
            }
        }
    }
}
"""

GRAPHQL_QUERY_ID = """
query GetTitleInfo {
    title(id: "%%%ID%%%") {
        id
        titleText {
            text
            isOriginalTitle
            country {
                text
            }
        }
        originalTitleText {
            text
        }
        releaseYear {
            year
            endYear
        }
        titleType {
            id
        }
        plot {
            plotText {
                plainText
            }
        }
        ratingsSummary {
            aggregateRating
            voteCount
        }
        primaryImage {
            url
        }
        runtime {
            displayableProperty {
                value {
                    plainText
                }
            }
            seconds
        }
        titleGenres {
            genres {
                genre {
                    text
                }
            }
        }
        principalCredits {
            category {
                text
                id
            }
            credits {
                name {
                    id
                    nameText {
                        text
                    }
                }
            }
        }
        runtimes(first: 10) {
            edges {
                node {
                    id
                    seconds
                    displayableProperty {
                        value {
                            plainText
                        }
                    }
                    attributes {
                        text
                    }
                }
            }
        }
        countriesOfOrigin {
            countries {
                text
            }
        }
    }
}
"""

TYPE_MAP = {
    ReleaseType.movie: ('movie', 'short', 'tvMovie', 'video', 'tvShort'),
    ReleaseType.season: ('tvSeries', 'tvMiniSeries'),
    # Searching for single episodes is currently not supported
    ReleaseType.episode: ('tvSeries', 'tvMiniSeries'),
}

TYPE_MAP_REVERSE = {
    'movie': ReleaseType.movie,
    'short': ReleaseType.movie,
    'tvMovie': ReleaseType.movie,
    'video': ReleaseType.movie,
    'tvShort': ReleaseType.movie,
    'tvSeries': ReleaseType.season,
    'tvMiniSeries': ReleaseType.season,
    'tvEpisode': ReleaseType.episode,
}

WEBSITE_BASE = 'https://www.imdb.com'


class ImdbApi(WebDbApiBase):
    """API for imdb.com"""

    name = 'imdb'
    label = 'IMDb'

    default_config = {}

    def get_id_from_text(self, text):
        # Example: https://www.imdb.com/title/tt0048918/
        match = re.search(r'\b(tt\d+)\b', text)
        if match:
            return match.group(1)

    def sanitize_query(self, query):
        """
        Deal with IMDb-specific quirks

        - Remove ``"and"`` from :attr:`.Query.title` because IMDb doesn't find ``"Foo & Bar"`` if we
          search for ``"Foo and Bar"``. It seems to work vice versa, i.e. the query ``"Foo and
          Bar"`` finds ``"Foo & Bar"``, so we keep any ``"&"``.

        - Replace ``"dont"`` with ``"don't"``, ``"cant"`` with ``"can't"``, etc.
        """
        query = super().sanitize_query(query)
        query.title = re.sub(r'\s(?i:and)(\s)', r'\1', query.title)
        query.title = re.sub(r'\b(?i:dont)(\b)', "don't", query.title)
        query.title = re.sub(r'\b(?i:cant)(\b)', "can't", query.title)
        query.title = re.sub(r'\b(?i:wont)(\b)', "won't", query.title)
        return query

    _url_base = 'https://caching.graphql.imdb.com'

    def _get_graphql_query(self, template_name, values):
        template = globals()[f'GRAPHQL_QUERY_{template_name.upper()}']
        query = ' '.join(template.replace('\n', ' ').split())
        for k, v in values.items():
            query = query.replace(f'%%%{k}%%%', v)
        if '%%%' in query:
            raise RuntimeError(f'Unresolved template string in query: {query}')
        else:
            return json.dumps({'query': query})

    async def _get_info(self, id):
        query = self._get_graphql_query('ID', {'ID': id})
        response = (await utils.http.post(
            url=self._url_base,
            data=query,
            headers={'Content-Type': 'application/json'},
            timeout=10,
            cache=True,
            user_agent='BROWSER',
        )).json()
        return response['data']['title']

    async def search(self, query):
        _log.debug('Searching IMDb for %r', query)
        if query.id:
            title_english = await self.title_english(query.id)
            title_original = await self.title_original(query.id)
            return [_ImdbSearchResult(
                imdb_api=self,
                cast=functools.partial(self.cast, query.id),
                countries=functools.partial(self.countries, query.id),
                directors=functools.partial(self.directors, query.id),
                genres=functools.partial(self.genres, query.id),
                id=query.id,
                summary=functools.partial(self.summary, query.id),
                title=title_english or title_original,
                title_english=title_english,
                title_original=title_original,
                type=await self.type(query.id),
                url=await self.url(query.id),
                year=await self.year(query.id),
            )]

        elif not query.title:
            return []

        else:
            constraints = [f'titleTextConstraint: {{searchTerm: "{query.title}"}}']

            if query.type is not ReleaseType.unknown:
                types = TYPE_MAP[query.type]
                types_str = '[' + ', '.join(f'"{t}"' for t in types) + ']'
                constraints.append(f'titleTypeConstraint: {{anyTitleTypeIds: {types_str}}}')

            if query.year is not None:
                constraints.append(
                    f'releaseDateConstraint: {{releaseDateRange: {{start: "{query.year}-01-01", end: "{query.year}-12-31"}}}}'
                )

            constraints.append('explicitContentConstraint: {explicitContentFilter: INCLUDE_ADULT}')

            query = self._get_graphql_query('SEARCH', {'CONSTRAINTS': ', '.join(constraints)})
            response = (await utils.http.post(
                url=self._url_base,
                data=query,
                headers={'Content-Type': 'application/json'},
                timeout=10,
                cache=True,
                user_agent='BROWSER',
            )).json()
            return [
                _ImdbSearchResult(info=result['node']['title'], imdb_api=self)
                for result in response['data']['advancedTitleSearch']['edges']
            ]

    async def cast(self, id):
        if id:
            return await self._get_persons(id, category='cast')
        return ()

    async def creators(self, id):
        if id:
            info = await self._get_info(id)
            _log.debug(json.dumps(info, indent=4))
            return await self._get_persons(id, category='creator')
        return ()

    async def directors(self, id):
        if id:
            return await self._get_persons(id, category='director')
        return ()

    async def _get_persons(self, id, *, category):
        info = await self._get_info(id)
        principal_credits = info.get('principalCredits', ())
        credits = ()
        for credits_ in principal_credits:
            category_ = credits_.get('category') or {}
            if category_.get('id') == category:
                credits = credits_.get('credits', ())
                break

        def get_person(credit):
            name = ((credit.get('name') or {}).get('nameText') or {}).get('text', '')
            id = (credit.get('name') or {}).get('id', '')
            if name and id:
                return common.Person(name, url=f'{WEBSITE_BASE}/name/{id}')

        return tuple(
            person
            for credit in credits
            if (person := get_person(credit))
        )

    async def _countries(self, id):
        countries = []
        if id:
            info = await self._get_info(id)
            items = (info.get('countriesOfOrigin') or {}).get('countries', ())
            countries.extend(
                country
                for item in items
                if (country := item.get('text'))
            )
        return tuple(countries)

    async def genres(self, id):
        genres = []
        if id:
            info = await self._get_info(id)
            items = (info.get('titleGenres') or {}).get('genres', ())
            genres.extend(
                genre.casefold()
                for item in items
                if (genre := ((item.get('genre') or {}).get('text') or None))
            )
        return tuple(genres)

    async def poster_url(self, id, season=None):
        if id:
            info = await self._get_info(id)
            poster_url = (info.get('primaryImage') or {}).get('url', '')
            # Request scaled down poster (300 pixels wide)
            poster_url = re.sub(r'._V1_*.jpg$', '._V1_SX300.jpg', poster_url)
            return poster_url
        return ''

    rating_min = 0.0
    rating_max = 10.0

    async def rating(self, id):
        if id:
            info = await self._get_info(id)
            return (info.get('ratingsSummary') or {}).get('aggregateRating', None)
        return None

    _ignored_runtimes_keys = (
        re.compile(r'^(?i:approx)\w*$'),
    )

    async def _runtimes(self, id):
        if id:
            info = await self._get_info(id)
            runtimes = tuple(
                node
                for edge in (info.get('runtimes') or {}).get('edges', ())
                if (node := edge.get('node'))
            )

            def get_cut_name(runtime):
                attributes = runtime.get('attributes', ())
                name = 'default'
                if attributes:
                    name = attributes[0].get('text') or 'default'
                if name != 'default':
                    # Capitalize words. We can't use "\b" because that results in "Director'S Cut".
                    name = re.sub(r'(?:^|\s)[a-z]', lambda match: match.group(0).upper(), name)
                return name

            def get_runtime_minutes(runtime):
                return round(runtime.get('seconds', 0) / 60)

            return {
                get_cut_name(runtime): get_runtime_minutes(runtime)
                for runtime in runtimes
            }

        return {}

    async def summary(self, id):
        if id:
            info = await self._get_info(id)
            return ((info.get('plot') or {}).get('plotText') or {}).get('plainText', '')
        return ''

    async def _title_original(self, id):
        if id:
            info = await self._get_info(id)
            return (info.get('originalTitleText') or {}).get('text', '')
        return ''

    async def _titles_english(self, id):
        if id:
            info = await self._get_info(id)
            return ((info.get('titleText') or {}).get('text', ''),)
        return ()

    async def type(self, id):
        if id:
            info = await self._get_info(id)
            name = (info.get('titleType') or {}).get('id', '')
            return TYPE_MAP_REVERSE.get(name, ReleaseType.unknown)
        return ReleaseType.unknown

    async def url(self, id):
        if id:
            return f'{WEBSITE_BASE}/title/{id}'
        return ''

    async def year(self, id):
        if id:
            info = await self._get_info(id)
            return str((info.get('releaseYear') or {}).get('year', ''))
        return ''


class _ImdbSearchResult(common.SearchResult):
    def __init__(self, *, imdb_api, info=None, cast=None, countries=None,
                 directors=None, genres=None, id=None, poster=None, summary=None, title=None,
                 title_english=None, title_original=None, type=None, url=None,
                 year=None):
        info = info or {}
        self._imdb_api = imdb_api
        id = id or self._get_id(info)
        super().__init__(
            cast=cast or functools.partial(imdb_api.cast, id),
            countries=countries or functools.partial(imdb_api.countries, id),
            directors=directors or functools.partial(imdb_api.directors, id),
            genres=genres or functools.partial(imdb_api.genres, id),
            id=id,
            poster=functools.partial(imdb_api.poster, id),
            summary=summary or self._get_summary(info),
            title=title or self._get_title(info),
            title_english=title_english or functools.partial(imdb_api.title_english, id),
            title_original=title_original or functools.partial(imdb_api.title_original, id),
            type=type or self._get_type(info),
            url=url or self._get_url(info),
            year=year or self._get_year(info),
        )

    def _get_id(self, info):
        return info.get('id', '')

    def _get_summary(self, info):
        return ((info.get('plot') or {}).get('plotText') or {}).get('plainText', '')

    def _get_title(self, info):
        return (info.get('titleText') or {}).get('text', '')

    def _get_type(self, info):
        name = (info.get('titleType') or {}).get('id', '')
        return TYPE_MAP_REVERSE.get(name, ReleaseType.unknown)

    def _get_url(self, info):
        id = self._get_id(info)
        if id:
            return f'{WEBSITE_BASE}/title/{id}'
        return ''

    def _get_year(self, info):
        return (info.get('releaseYear') or {}).get('year', '')
