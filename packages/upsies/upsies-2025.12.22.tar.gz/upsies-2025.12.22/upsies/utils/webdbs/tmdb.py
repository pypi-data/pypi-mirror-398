"""
API for themoviedb.org
"""

import functools
import re
import urllib.parse

from .. import html, http
from ..types import ReleaseType
from . import common
from .base import WebDbApiBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class TmdbApi(WebDbApiBase):
    """API for themoviedb.org"""

    name = 'tmdb'
    label = 'TMDb'

    no_results_info = f"{label}'s year is often slightly different."

    default_config = {}

    _url_base = 'http://themoviedb.org'
    _soup_cache = {}

    async def _get_soup(self, path, params={}):
        cache_id = (path, tuple(sorted(params.items())))
        if cache_id in self._soup_cache:
            return self._soup_cache[cache_id]
        text = await http.get(
            url=f'{self._url_base}/{path.lstrip("/")}',
            params=params,
            user_agent='BROWSER',
            cache=True,
        )
        self._soup_cache[cache_id] = html.parse(text)
        return self._soup_cache[cache_id]

    def get_id_from_text(self, text):
        # Examples:
        # https://www.themoviedb.org/movie/334536-the-blackcoat-s-daughter
        # https://www.themoviedb.org/tv/45016-bron-broen
        match = re.search(r'\b((?i:movie|tv)/\d+)\b', text)
        if match:
            return match.group(1)

    async def search(self, query):
        _log.debug('Searching TMDb for %s', query)

        if query.id:
            async def generate_result(id):
                _log.debug('Getting ID: %r', id)
                title_english = await self.title_english(id)
                title_original = await self.title_original(id)
                return _TmdbSearchResult(
                    tmdb_api=self,
                    cast=functools.partial(self.cast, id),
                    directors=functools.partial(self.directors, id),
                    genres=functools.partial(self.genres, id),
                    id=id,
                    summary=functools.partial(self.summary, id),
                    title=title_english or title_original,
                    title_english=functools.partial(self.title_english, id),
                    title_original=functools.partial(self.title_original, id),
                    type=await self.type(id),
                    url=await self.url(id),
                    year=await self.year(id),
                )

            if re.search(r'\b(?:movie|tv)\b', query.id):
                return [await generate_result(query.id)]
            else:
                return [await generate_result(f'movie/{query.id}'),
                        await generate_result(f'tv/{query.id}')]

        elif not query.title:
            return []

        else:
            params = {'query': query.title_normalized}
            if query.year is not None:
                params['query'] += f' y:{query.year}'

            if query.type is ReleaseType.movie:
                soup = await self._get_soup('/search/movie', params=params)
            elif query.type in (ReleaseType.season, ReleaseType.episode):
                soup = await self._get_soup('/search/tv', params=params)
            else:
                movie_results = await self.search(query.copy(type=ReleaseType.movie))
                series_results = await self.search(query.copy(type=ReleaseType.series))
                return movie_results + series_results

            # When search for year, unmatching results are included but hidden.
            for tag in soup.find_all('div', class_='hide'):
                tag.clear()

            items = soup.find_all('div', class_='card')
            results = [_TmdbSearchResult(soup=item, tmdb_api=self)
                       for item in items]

            if query.year is not None:
                # Filter the search results for the queried year because TMDb is
                # very smart and returns wrong search results.
                return [result for result in results
                        if result.year == query.year]
            else:
                return results

    _person_url_path_regex = re.compile(r'(/person/\d+(?:-[-a-z]+|))')

    def _get_persons(self, tag, role_tag=None):
        a_tags = tag.find_all('a', href=self._person_url_path_regex)
        persons = []
        for a_tag in a_tags:
            if a_tag.string:
                name = a_tag.string.strip()

                url_match = self._person_url_path_regex.match(a_tag["href"])
                if url_match:
                    url_path = url_match.group(1)
                    url = f'{self._url_base.rstrip("/")}/{url_path.lstrip("/")}'
                else:
                    url = ''

                role = role_tag.string.strip() if role_tag and role_tag.string else ''
                persons.append(common.Person(name, url=url, role=role))

        return tuple(persons)

    async def cast(self, id):
        cast = []
        if id:
            soup = await self._get_soup(id)
            cards = soup.select('.people > .card')
            for card in cards:
                cast.extend(self._get_persons(card, role_tag=card.find('p', {'class': 'character'})))
        return tuple(cast)

    async def _countries(self, id):
        return ()

    async def creators(self, id):
        creators = []
        if id:
            soup = await self._get_soup(id)
            profiles = soup.select('.people > .profile')
            for profile in profiles:
                if profile.find('p', string=re.compile(r'(?i:Creator)')):
                    creators.extend(self._get_persons(profile))
        return tuple(creators)

    async def directors(self, id):
        directors = []
        if id:
            soup = await self._get_soup(id)
            profiles = soup.select('.people > .profile')
            for profile in profiles:
                if profile.find('p', string=re.compile(r'(?i:Director)')):
                    directors.extend(self._get_persons(profile))
        return tuple(directors)

    async def genres(self, id):
        genres = ()
        if id:
            soup = await self._get_soup(id)
            genres_tag = soup.find(class_='genres')
            if genres_tag:
                genres = [
                    k.lower() for k in genres_tag.stripped_strings
                    if k != ','
                ]

            # "short" is not a genre on TMDb and keywords are wonky. But
            # Wikipedia says:
            # > The Academy of Motion Picture Arts and Sciences defines a short
            # > film as "an original motion picture that has a running time of
            # > 40 minutes or less, including all credits".
            runtimes = await self.runtimes(id)
            if runtimes and runtimes['default'] <= 40:
                genres.append('short')

        return tuple(genres)

    async def poster_url(self, id, season=None):
        if id:
            soup = await self._get_soup(id)
            img_tag = soup.find('img', class_='poster')
            if img_tag:
                srcs = img_tag.get('src')
                if srcs:
                    path = srcs.split()[0]
                    return urllib.parse.urljoin(self._url_base, path)
        return ''

    rating_min = 0.0
    rating_max = 100.0

    async def rating(self, id):
        if id:
            soup = await self._get_soup(id)
            rating_tag = soup.find(class_='user_score_chart')
            if rating_tag:
                try:
                    return float(rating_tag['data-percent'])
                except (ValueError, TypeError):
                    pass

    async def _runtimes(self, id):
        runtimes = {}
        if id:
            soup = await self._get_soup(id)
            runtimes_tag = soup.find('span', class_='runtime')
            try:
                text = str(runtimes_tag.string)
            except AttributeError:
                text = ''

            minutes = 0
            for unit, unit_minutes in (('h', 60), ('m', 1)):
                for match in re.finditer(rf'(\d+)\s*{unit}', text):
                    minutes += int(match.group(1)) * unit_minutes
            if minutes > 0:
                runtimes['default'] = minutes

        return runtimes

    _no_overview_texts = (
        "We don't have an overview",
        'No overview found.',
    )

    async def summary(self, id):
        if id:
            soup = await self._get_soup(id)
            overview = ''.join(soup.find('div', class_='overview').stripped_strings)
            if any(text in overview for text in self._no_overview_texts):
                overview = ''
            return overview
        return ''

    async def _title_original(self, id):
        soup = await self._get_soup(id)
        try:
            # Find non-English title
            title_tag = soup.find(string=re.compile(r'Original (?:Title|Name)'))
            parent_tag = title_tag.parent.parent
            strings = tuple(parent_tag.stripped_strings)
            return strings[1]
        except (AttributeError, TypeError, ValueError, IndexError):
            # Default to English title
            english_titles = await self._titles_english(id)
            return english_titles[0]

    async def _titles_english(self, id):
        soup = await self._get_soup(id)
        title_tag = soup.find(class_='title')
        title_parts = list(title_tag.stripped_strings)
        return (title_parts[0],)

    async def type(self, id):
        if id:
            soup = await self._get_soup(id)
            network_tag = soup.find('bdi', string=re.compile(r'^Networks?$'))
            if network_tag:
                return ReleaseType.series
            else:
                return ReleaseType.movie
        else:
            return ReleaseType.unknown

    async def url(self, id):
        if id:
            return f'{self._url_base.rstrip("/")}/{id.strip("/")}'
        return ''

    async def year(self, id):
        if id:
            soup = await self._get_soup(id)
            release_date_tag = soup.find(class_='release_date')
            if release_date_tag:
                year = ''.join(release_date_tag.stripped_strings).strip('()')
                if len(year) == 4 and year.isdigit():
                    return year
        return ''


class _TmdbSearchResult(common.SearchResult):
    def __init__(self, *, tmdb_api, soup=None, cast=None, countries=None,
                 directors=None, id=None, genres=None, poster=None, summary=None, title=None,
                 title_english=None, title_original=None, type=None, url=None,
                 year=None):
        soup = soup or html.parse('')
        id = id or self._get_id(soup)
        super().__init__(
            cast=cast or functools.partial(tmdb_api.cast, id),
            countries=countries or (),
            directors=directors or functools.partial(tmdb_api.directors, id),
            id=id,
            genres=genres or functools.partial(tmdb_api.genres, id),
            poster=functools.partial(tmdb_api.poster, id),
            summary=summary or functools.partial(tmdb_api.summary, id),
            title=title or self._get_title(soup),
            title_english=title_english or functools.partial(tmdb_api.title_english, id),
            title_original=title_original or functools.partial(tmdb_api.title_original, id),
            type=type or self._get_type(soup),
            url=url or self._get_url(soup),
            year=year or self._get_year(soup),
        )

    def _get_id(self, soup):
        a_tag = soup.find('a', class_='result')
        if a_tag:
            href = a_tag.get('href')
            return re.sub(r'^.*/((?:movie|tv)/[0-9]+).*?$', r'\1', href)
        return ''

    def _get_url(self, soup):
        id = self._get_id(soup)
        if id:
            return f'{TmdbApi._url_base}/{id}'
        return ''

    def _get_type(self, soup):
        a_tag = soup.find('a', class_='result')
        if a_tag:
            href = a_tag.get('href')
            if href:
                tmdb_type = re.sub(r'(?:^|/)(\w+)/.*$', r'\1', href)
                if tmdb_type == 'movie':
                    return ReleaseType.movie
                elif tmdb_type == 'tv':
                    return ReleaseType.series
        return ReleaseType.unknown

    def _get_title(self, soup):
        header = soup.select('.result > h2')
        if header:
            # Title tag may contain other information in smaller font or dimmed.
            title_tag = header[0].contents[0]
            return html.as_text(title_tag)
        else:
            return ''

    def _get_year(self, soup):
        release_date = soup.find(class_='release_date')
        if release_date:
            match = re.search(r'(\d{4})$', release_date.string)
            if match:
                return match.group(1)
        return ''
