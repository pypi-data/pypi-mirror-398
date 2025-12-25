"""
Concrete :class:`~.TrackerBase` subclass for ANT
"""

import math
import urllib

from ... import errors, utils
from ..base import TrackerBase
from . import config, rules
from .jobs import AntTrackerJobs

import logging  # isort:skip
_log = logging.getLogger(__name__)


class AntTracker(TrackerBase):
    name = 'ant'
    label = 'ANT'
    torrent_source_field = 'ANT'

    setup_howto_template = (
        '{howto.introduction}\n'
        '\n'
        '{howto.next_section}. API Key\n'
        '\n'
        '   {howto.current_section}.1 On the website, go to USERNAME -> Edit -> Access Settings\n'
        '       and scroll down to "API keys".\n'
        '   {howto.current_section}.2 In the "Create a new Key" row, tick the "Upload" box.\n'
        '   {howto.current_section}.3 Click on "Save profile".\n'
        '   {howto.current_section}.4 Scroll down to "API keys" again and copy the new API_KEY.\n'
        '   {howto.current_section}.5 $ upsies set trackers.{tracker.name}.apikey API_KEY\n'
        '\n'
        '{howto.next_section}. Announce URL\n'
        '\n'
        '   {howto.current_section}.1 On the website, click on "Upload" and copy the ANNOUNCE_URL.\n'
        '   {howto.current_section}.2 $ upsies set trackers.{tracker.name}.announce_url ANNOUNCE_URL\n'
        '\n'
        '{howto.autoseed}\n'
        '\n'
        '{howto.reuse_torrents}\n'
        '\n'
        '{howto.upload}\n'
    )

    TrackerJobs = AntTrackerJobs
    TrackerConfig = config.AntTrackerConfig
    cli_arguments = config.cli_arguments
    rules = rules

    @property
    def _base_url(self):
        return self.options['base_url']

    @property
    def _api_url(self):
        return urllib.parse.urljoin(self._base_url, '/api.php')

    @property
    def apikey(self):
        apikey = self.options.get('apikey')
        if apikey:
            return apikey
        else:
            raise errors.RequestError('No API key configured')

    async def _login(self, *, tfa_otp=None):
        pass

    async def confirm_logged_in(self):
        pass

    async def _logout(self):
        pass

    async def get_announce_url(self):
        if announce_url := self.options.get('announce_url'):
            return announce_url.get_secret_value()
        else:
            raise errors.AnnounceUrlNotSetError(tracker=self)

    async def upload(self, tracker_jobs):
        post_data = tracker_jobs.post_data

        _log.debug('POSTing data:')
        for k, v in post_data.items():
            _log.debug(' * %s = %s', k, v)

        post_files = tracker_jobs.post_files
        _log.debug('POSTing files: %r', post_files)

        json = await self._request(
            method='POST',
            url=self._api_url,
            cache=False,
            data=post_data,
            files=post_files,
        )

        # Unfortunately, the API respnose is just "{'status': 'success'}" and we have no way to
        # return the web page URL of the uploaded torrent.
        if json.get('status') == 'success':
            return tracker_jobs.torrent_filepath
        elif json.get('error'):
            raise errors.RequestError(f'Upload failed: {json["error"]}')
        else:
            raise RuntimeError(f'Unexpected response: {json!r}')

    async def _request(self, method, *args, **kwargs):
        try:
            # `method` is "GET" or "POST"
            response = await getattr(utils.http, method.lower())(
                *args,
                user_agent=True,
                **kwargs,
            )
        except errors.RequestError as e:
            _log.debug(f'Request failed: {e!r}')
            _log.debug(f'url={e.url!r}')
            _log.debug(f'text={e.text!r}')
            _log.debug(f'headers={e.headers!r}')
            _log.debug(f'status_code={e.status_code!r}')
            # The error message in the HTTP response is JSON. Try to parse that
            # to get the actual error message. If that fails, raise the
            # RequestError as is.
            json = e.json(default=None)
            if json:
                return json
            else:
                raise e
        else:
            return response.json()

    @staticmethod
    def calculate_piece_size(bytes):
        # Recommended piece count is 1000.
        exponent = math.ceil(math.log2(bytes / 1000))

        # Piece size range: 1 MiB - 64 MiB
        exponent = max(20, min(26, exponent))
        return int(math.pow(2, exponent))

    @staticmethod
    def calculate_piece_size_min_max(bytes):
        # Maximum torrent file size is 100 KiB. We reserve a maximum of 60 KiB
        # for piece hashes, leaving 40 KiB for other metadata. Each piece hash
        # is 20 bytes long.
        max_piece_count = (60 * 1024) / 20
        min_exponent = math.ceil(math.log2(bytes / max_piece_count))

        # Absolute minimum piece size: 1 MiB
        min_exponent = max(20, min_exponent)

        # For large torrents, the minimum piece size can end up larger then the
        # maximum. Here we limit the minimum piece size to 8 MiB or less.
        min_exponent = min(23, min_exponent)

        return (
            math.pow(2, min_exponent),
            64 * 2**20,  # 64 MiB
        )
