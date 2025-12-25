"""
Concrete :class:`~.TrackerBase` subclass for CBR
"""

import functools
import re
import urllib

from ... import errors, utils
from ..base import TrackerBase
from . import config, rules
from .jobs import CbrTrackerJobs

import logging  # isort:skip
_log = logging.getLogger(__name__)


class CbrTracker(TrackerBase):
    name = 'cbr'
    label = 'CBR'
    torrent_source_field = 'CapybaraBR'

    setup_howto_template = (
        '{howto.introduction}\n'
        '\n'
        '{howto.next_section}. API Key\n'
        '\n'
        '   {howto.current_section}.1 On the website, go to your profile > Settings > API Key.\n'
        '   {howto.current_section}.2 If you have no API key yet, click on "Generate API key".\n'
        '   {howto.current_section}.3 Copy your personal API_KEY.\n'
        '   {howto.current_section}.4 $ upsies set trackers.{tracker.name}.apikey API_KEY\n'
        '\n'
        '{howto.next_section}. Announce URL\n'
        '\n'
        '   {howto.current_section}.1 On the website: Torrents > Upload > URL de Anúncio\n'
        '   {howto.current_section}.2 $ upsies set trackers.{tracker.name}.announce_url URL\n'
        '\n'
        '{howto.screenshots}\n'
        '\n'
        '{howto.autoseed}\n'
        '\n'
        '{howto.reuse_torrents}\n'
        '\n'
        '{howto.upload}\n'
    )

    TrackerJobs = CbrTrackerJobs
    TrackerConfig = config.CbrTrackerConfig
    cli_arguments = config.cli_arguments
    rules = rules

    async def _login(self, *, tfa_otp=None):
        pass

    async def confirm_logged_in(self):
        pass

    async def _logout(self):
        pass

    @functools.cached_property
    def _upload_url(self):
        return urllib.parse.urljoin(self.options['base_url'], '/api/torrents/upload')

    async def get_announce_url(self):
        announce_url = self.options.get('announce_url')
        if announce_url:
            return announce_url.get_secret_value()
        else:
            raise errors.AnnounceUrlNotSetError(tracker=self)

    async def upload(self, tracker_jobs):
        if not self.options['apikey']:
            raise errors.RequestError(f'trackers.{self.name}.apikey is not set')

        _log.debug('Uploading to %r', self._upload_url)
        _log.debug('POSTing data:')
        post_data = tracker_jobs.post_data
        for k, v in post_data.items():
            _log.debug(' * %s = %s', k, v)

        files = tracker_jobs.post_files
        _log.debug('Files: %r', files)

        try:
            response = await utils.http.post(
                url=self._upload_url,
                cache=False,
                user_agent=True,
                files=files,
                data=post_data,
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
            json = e.json(default=False)
            if not json:
                raise errors.RequestError(f'Upload failed: {e.text}') from e
        else:
            _log.debug('Upload response: %r', response)
            json = response.json()

        if json.get('success') is True:
            torrent_url = json['data']
            return self._website_url_from_torrent_url(torrent_url)
        elif json.get('message') and json.get('data'):
            raise errors.RequestError(f'Upload failed: {json["message"]}\n{json["data"]}')
        elif json.get('message'):
            raise errors.RequestError(f'Upload failed: {json["message"]}')
        else:
            raise RuntimeError(f'Unexpected response: {json!r}')

    def _website_url_from_torrent_url(self, torrent_url):
        # Torrent URL: .../torrent/download/<torrent id>.<some kind of hash?>
        # Website URL: .../torrents/<torrent id>
        website_url = torrent_url.replace('/torrent/download/', '/torrents/')
        website_url = re.sub(r'\.[a-zA-Z0-9]+$', '', website_url)
        return website_url
