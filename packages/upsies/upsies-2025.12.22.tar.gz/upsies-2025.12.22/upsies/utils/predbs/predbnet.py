from base64 import b64decode

from ... import errors
from .. import http
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)


class PredbnetApi(base.PredbApiBase):
    name = 'predbnet'
    label = 'PreDB.net'

    default_config = {}

    _url_base = b64decode('cHJlZGIubmV0').decode('ascii')
    _search_url = f'https://api.{_url_base}'

    async def _search(self, query):
        params = self._get_params(query.keywords, query.group)
        return await self._request_all_pages(params)

    def _get_params(self, keywords, group):
        return {
            'type': 'search',
            'q': ' '.join(
                kw_sanitized
                for kw in keywords
                if (kw_sanitized := str(kw).lower().strip())
            ),
            'group': group,
            'limit': self._max_results_per_page,
        }

    # We could request 1000 pages, but we are limited to 30 requests in 60 seconds.
    _max_pages = 30
    _max_results_per_page = 100

    async def _request_all_pages(self, params):
        combined_results = []
        page = 1
        while page <= self._max_pages:
            results, next_page = await self._request_page(params, page)
            combined_results.extend(results)

            if next_page < 0:
                # Negative next page means there are no more pages
                break
            else:
                page += 1

        return combined_results

    async def _request_page(self, params, page):
        params = {**params, 'page': page}
        _log.debug('%s search: %r, %r', self.label, self._search_url, params)
        response = (await http.get(self._search_url, params=params, cache=True, raise_on_error_status=False)).json()

        if response.get('data'):
            # We found at least one release
            results = tuple(result['release'] for result in response['data'])

        elif (
                response.get('status') != 'success'
                and response.get('message')
                and 'no results' not in response['message'].lower()
        ):
            # Report error from API
            raise errors.RequestError(f'{self.label}: {response["message"]}')

        else:
            results = ()

        _log.debug('Found %d results', len(results))

        # Is there another page of results?
        if len(results) >= self._max_results_per_page:
            next_page = page + 1
        else:
            next_page = -1

        return results, next_page

    async def _release_files(self, release_name):
        raise NotImplementedError()
