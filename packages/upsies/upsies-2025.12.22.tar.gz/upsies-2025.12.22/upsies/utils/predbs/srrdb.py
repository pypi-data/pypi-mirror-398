import os
import re
from base64 import b64decode

from ... import errors, utils
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)


class SrrdbApi(base.PredbApiBase):
    name = 'srrdb'
    label = 'srrDB'

    default_config = {}

    _url_base = b64decode('YXBpLnNycmRiLmNvbQ==').decode('ascii')
    _search_url = f'https://{_url_base}/v1/search'
    _details_url = f'https://{_url_base}/v1/details'

    _keyword_separators_regex = re.compile(r'[^a-zA-Z0-9]')

    # We can skip over 50_000 results and get 1000 results per request
    # https://www.srrdb.com/help
    _page_size = 1000
    _max_skip = 50_000

    @staticmethod
    def _make_release_name_from_path(path):
        return utils.fs.strip_extension(utils.fs.basename(path))

    async def _search(self, query):
        # Because srrdb search is so slow, we first try to find the exact
        # release name with the "search/r:RELEASE_NAME" API call. If that yields
        # a result, we know it's a properly named scene release. If there are no
        # results, we have to do a slow keyword search because it might still be
        # a renamed scene release.
        if query.release_info:
            results = await self._search_for_exact_movie_or_episode(query)
            if results:
                return results

            # Because there are no scene season packs, we have to do one
            # "search/r:RELEASE_NAME" call per episode.
            results = await self._search_for_exact_season(query)
            if results:
                return results

        # Default to slow keyword search. Request as many results as possible.
        # They should get filtered somewhere upstream by our callers.
        combined_results = []
        for skip in range(0, self._max_skip + 1, self._page_size):
            keywords_path = self._get_keywords_path(query.keywords, query.group, skip)
            results = await self._request_search_page(keywords_path)
            combined_results.extend(results)
            if len(results) < self._page_size:
                # We didn't get a full page, so we assume this is the last page
                break
        return combined_results

    async def _search_for_exact_movie_or_episode(self, query):
        if query.release_info['type'] in (
                utils.release.ReleaseType.movie,
                utils.release.ReleaseType.episode,
        ):
            release_name = self._make_release_name_from_path(query.release_info.path)
            results = await self._search_for_exact_release_name(release_name)
            return results

    async def _search_for_exact_season(self, query):
        if os.path.isdir(query.release_info.path) and query.release_info['type'] in (
                utils.release.ReleaseType.season,
        ):
            _log.debug('Searching for exact season pack: %r', query.release_info.path)
            combined_results = []
            for video_file in utils.fs.find_main_videos(query.release_info.path):
                release_name = self._make_release_name_from_path(video_file)
                results = await self._search_for_exact_release_name(release_name)
                if not results:
                    # Single non-scene episode makes the season pack non-scene.
                    # Is there a better way to deal with this situation?
                    _log.debug('Non-scene episode: %r', video_file)
                    combined_results.clear()
                    break
                else:
                    combined_results.extend(results)
            return combined_results

    async def _search_for_exact_release_name(self, release_name):
        search_url = f'{self._search_url}/r:{release_name}'
        _log.debug('Quicksearch URL: %r', search_url)
        try:
            response = (await utils.http.get(search_url, cache=True)).json()
        except errors.RequestError as e:
            # SrrDB returns HTTP errors if there are illegal characters in the
            # release name or the request is otherwise unexpected. For example,
            # if there are spaces in `release_name`, we get "403 Forbidden".
            _log.debug('Quicksearch error: %r', e)
            return ()
        else:
            results = response.get('results', [])
            return tuple(r['release'] for r in results)

    async def _request_search_page(self, keywords_path):
        search_url = f'{self._search_url}/{keywords_path}'
        _log.debug('Search URL: %s', search_url)
        response = (await utils.http.get(search_url, cache=True)).json()
        results = response.get('results', [])
        return tuple(r['release'] for r in results)

    def _get_keywords_path(self, keywords, group, skip):
        def sanitize_keyword(kw):
            return kw.lower()

        keywords_sanitized = [
            sanitize_keyword(kw)
            for keyword in keywords
            for kw in self._keyword_separators_regex.split(keyword)
        ]
        if group:
            keywords_sanitized.append(sanitize_keyword(group))

        # Get most recent results
        keywords_sanitized.append('order:date-desc')

        # Skip over `skip` results
        assert (isinstance(skip, int) and 0 <= skip <= self._max_skip), skip
        keywords_sanitized.append(f'skipr:{skip}.{self._page_size}')

        return '/'.join(keywords_sanitized)

    async def _release_files(self, release_name):
        """
        Map file names to dictionaries with the keys ``release_name``,
        ``file_name``, ``size`` and ``crc``

        If no files for `release_name` are found, return an empty :class:`dict`.

        :param str release_name: Exact name of the release

        :raise RequestError: if request fails
        """
        details_url = f'{self._details_url}/{release_name}'
        _log.debug('Details URL: %s', details_url)
        response = await utils.http.get(details_url, cache=True)
        # Response may be empty string
        if response:
            # Response may be empty list
            info = response.json()
            if info:
                # If info is not an empty list, it should be a dictionary
                files = info['archived-files']
                release_name = info['name']
                return {
                    f['name']: {
                        'release_name': release_name,
                        'file_name': f['name'],
                        'size': f['size'],
                        'crc': f['crc'],
                    }
                    for f in sorted(files, key=lambda f: f['name'].casefold())
                }

        return {}
