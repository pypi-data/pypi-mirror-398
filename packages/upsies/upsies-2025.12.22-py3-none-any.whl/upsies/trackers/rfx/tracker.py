"""
Concrete :class:`~.TrackerBase` subclass for RFX
"""

import re

from ... import errors, utils
from ..base import TrackerBase
from . import config
from .jobs import RfxTrackerJobs

import logging  # isort:skip
_log = logging.getLogger(__name__)


class RfxTracker(TrackerBase):
    name = 'rfx'
    label = 'RFX'
    torrent_source_field = 'ReelFliX'

    setup_howto_template = (
        '{howto.introduction}\n'
        '\n'
        '{howto.next_section}. API Key\n'
        '\n'
        '   {howto.current_section}.1 On the website, go to your profile > Settings > API Key.\n'
        '   {howto.current_section}.2 If you have no API_KEY yet, generate one.\n'
        '   {howto.current_section}.3 Copy your personal API_KEY.\n'
        '   {howto.current_section}.4 $ upsies set trackers.{tracker.name}.apikey API_KEY\n'
        '\n'
        '{howto.next_section}. Announce URL\n'
        '\n'
        '   {howto.current_section}.1 On the website, go to your profile > Settings > Passkey.\n'
        '   {howto.current_section}.2 Copy your personal PASSKEY.\n'
        '   {howto.current_section}.2 $ upsies set trackers.{tracker.name}.announce_passkey PASSKEY\n'
        '\n'
        '{howto.screenshots}\n'
        '\n'
        '{howto.autoseed}\n'
        '\n'
        '{howto.reuse_torrents}\n'
        '\n'
        '{howto.upload}\n'
    )

    TrackerJobs = RfxTrackerJobs
    TrackerConfig = config.RfxTrackerConfig
    cli_arguments = config.cli_arguments

    async def _login(self, *, tfa_otp=None):
        pass

    async def confirm_logged_in(self):
        pass

    async def _logout(self):
        pass

    async def get_announce_url(self):
        if not self.options['announce_passkey']:
            raise errors.RequestError(f'trackers.{self.name}.announce_passkey is not set')
        else:
            return '/'.join((
                self.options['announce_url'].rstrip('/'),
                self.options['announce_passkey'].get_secret_value(),
            ))

    async def upload(self, tracker_jobs):
        if not self.options['apikey']:
            raise errors.RequestError(f'trackers.{self.name}.apikey is not set')

        _log.debug('Uploading to %r', self.options['upload_url'])
        _log.debug('POSTing data:')
        for k, v in tracker_jobs.post_data.items():
            _log.debug(' * %s = %s', k, v)
        _log.debug('POSTing files:')
        for k, v in tracker_jobs.post_files.items():
            _log.debug(' * %s = %s', k, v)

        response = await utils.http.post(
            url=self.options['upload_url'],
            cache=False,
            user_agent=True,
            headers={'Authorization': f'Bearer {self.options["apikey"].get_secret_value()}'},
            files=tracker_jobs.post_files,
            data=tracker_jobs.post_data,
        )
        _log.debug('Upload response: %r', response)
        json = response.json()
        try:
            if json['success']:
                torrent_url = json['data']
                await tracker_jobs.create_torrent_job.download_torrent(torrent_url)
                return self._torrent_page_url_from_download_url(torrent_url)
            else:
                raise errors.RequestError(f'Upload failed: {json["message"]}')
        except KeyError as e:
            raise RuntimeError(f'Unexpected response: {response}') from e

    def _torrent_page_url_from_download_url(self, torrent_download_url):
        # Torrent URL: .../torrent/download/TORRENT_ID.RANDOM_ASCII_CHARACTERS(?)
        # Website URL: .../torrents/TORRENT_ID
        torrent_page_url = torrent_download_url.replace('/torrent/download/', '/torrents/')
        torrent_page_url = re.sub(r'\.[a-zA-Z0-9]+$', '', torrent_page_url)
        return torrent_page_url
