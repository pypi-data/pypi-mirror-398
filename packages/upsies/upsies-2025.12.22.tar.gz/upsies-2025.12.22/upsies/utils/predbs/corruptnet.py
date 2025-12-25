from base64 import b64decode

from .. import html, http
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)


class CorruptnetApi(base.PredbApiBase):
    name = 'corruptnet'
    label = 'pre.corrupt-net.org'

    default_config = {}

    _url_base = 'https://' + b64decode('cHJlLmNvcnJ1cHQtbmV0Lm9yZw==').decode('ascii')
    _search_url = f'{_url_base}/search.php'

    def _join_keywords(self, keywords, group):
        kws = ' '.join(kw.strip() for kw in keywords)
        if group:
            kws += f' group:{group.strip()}'
        return kws

    # This seems to be specified by the server?
    _results_per_page = 50

    # Seems reasonable?
    _max_pages = 10

    async def _search(self, query):
        combined_results = []
        max_page_value = self._max_pages * self._results_per_page
        for page in range(0, max_page_value, self._results_per_page):
            results = list(await self._request_page(query.keywords, query.group, page))
            combined_results.extend(results)
            if len(results) < self._results_per_page:
                break
        return combined_results

    async def _request_page(self, keywords, group, page):
        params = {
            'search': self._join_keywords(keywords, group),
            # This should be the current time in milliseconds, but if we do
            # this, nothing is cached, so we set this to 0.
            'ts': 0,
            # Not sure what these are
            'pretimezone': 0,
            'timezone': 0,
        }
        if page > 0:
            params['page'] = page

        _log.debug('%s search: %r, %r', self.label, self._search_url, params)
        response = await http.get(self._search_url, params=params, cache=True, verify=False, timeout=10)
        return self._yield_release_names(response)

    def _yield_release_names(self, response):
        doc = html.parse(response)
        for tr in doc.find_all('tr'):
            # Release name is in second column
            td_release_name = tr.select_one('td:nth-of-type(2)')
            if td_release_name:
                release_name = td_release_name.get_text().strip()
                yield release_name

    async def _release_files(self, release_name):
        raise NotImplementedError()
