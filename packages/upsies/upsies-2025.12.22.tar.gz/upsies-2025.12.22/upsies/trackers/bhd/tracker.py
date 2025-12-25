"""
Concrete :class:`~.TrackerBase` subclass for BHD
"""

import re

from ... import errors, utils
from ..base import TrackerBase
from . import config, rules
from .jobs import BhdTrackerJobs

import logging  # isort:skip
_log = logging.getLogger(__name__)


class BhdTracker(TrackerBase):
    name = 'bhd'
    label = 'BHD'
    torrent_source_field = 'BHD'

    setup_howto_template = (
        '{howto.introduction}\n'
        '\n'
        '{howto.next_section}. Announce Passkey\n'
        '\n'
        '   {howto.current_section}.1 On the website, go to My Settings -> Security -> Passkey\n'
        '       and copy your personal PASSKEY.\n'
        '   {howto.current_section}.2 $ upsies set trackers.{tracker.name}.announce_passkey PASSKEY\n'
        '\n'
        '{howto.next_section}. API Key\n'
        '\n'
        '   {howto.current_section}.1 On the website, go to My Settings -> Security -> API Key\n'
        '       and copy your personal API_KEY.\n'
        '   {howto.current_section}.2 $ upsies set trackers.{tracker.name}.apikey API_KEY\n'
        '\n'
        '{howto.screenshots}\n'
        '\n'
        '{howto.autoseed}\n'
        '\n'
        '{howto.reuse_torrents}\n'
        '\n'
        '{howto.upload}\n'
        '   $ {executable} submit {tracker.name} /path/to/content --draft\n'
    )

    TrackerJobs = BhdTrackerJobs
    TrackerConfig = config.BhdTrackerConfig
    cli_arguments = config.cli_arguments
    rules = rules

    async def _login(self, *, tfa_otp=None):
        pass

    async def confirm_logged_in(self):
        pass

    async def _logout(self):
        pass

    async def get_announce_url(self):
        return '/'.join((
            self.options['announce_url'].rstrip('/'),
            self.options['announce_passkey'].get_secret_value(),
        ))

    def get_upload_url(self):
        """
        Return URL for torrent uploads (includes API key)

        :raise RequestError: if ``apikey`` option is not set
        """
        if not self.options['apikey']:
            # We raise RequestError because this method should only be used by
            # upload(), which should only raise RequestError
            raise errors.RequestError(f'trackers.{self.name}.apikey is not set')
        else:
            return '/'.join((
                self.options['upload_url'].rstrip('/'),
                self.options['apikey'].get_secret_value(),
            ))

    DRAFT_UPLOADED_MESSAGE = 'Draft uploaded'

    async def upload(self, tracker_jobs):
        _log.debug('Uploading to %r', self.options['upload_url'])
        _log.debug('POSTing data:')
        post_data = tracker_jobs.post_data
        for k, v in post_data.items():
            _log.debug(' * %s = %s', k, v)

        files = {
            'file': {
                'file': tracker_jobs.torrent_filepath,
                'mimetype': 'application/octet-stream',
            },
            'mediainfo': {
                'file': tracker_jobs.mediainfo_filehandle,
                'filename': 'mediainfo',
                'mimetype': 'application/octet-stream',
            },
        }
        _log.debug('Files: %r', files)

        response = await utils.http.post(
            url=self.get_upload_url(),
            cache=False,
            user_agent=True,
            files=files,
            data=post_data,
        )
        _log.debug('Upload response: %r', response)
        json = response.json()
        _log.debug('Upload response: %r', json)
        try:
            if json['status_code'] == 0:
                # Upload response: {
                #     'status_code': 0,
                #     'status_message': "<error message>",
                #     'success': False,
                # }
                raise errors.RequestError(f'Upload failed: {json["status_message"]}')

            elif json['status_code'] == 1:
                # Upload response: {
                #     'status_code': 1,
                #     'status_message': 'Draft has been successfully saved.',
                #     'success': True,
                # }
                self.warn(json['status_message'])
                self.warn('You have to activate your upload manually '
                          'on the website when you are ready to seed.')
                return tracker_jobs.torrent_filepath

            elif json['status_code'] == 2:
                # Upload response: {
                #     'status_code': 2,
                #     'status_message': '<torrent file URL>',
                #     'success': True,
                # }
                torrent_url = json['status_message']
                return self._torrent_page_url_from_download_url(torrent_url)
            else:
                raise RuntimeError(f'Unexpected response: {response}')
        except KeyError as e:
            raise RuntimeError(f'Unexpected response: {response}') from e

    def _torrent_page_url_from_download_url(self, torrent_download_url):
        # Download URL: .../torrent/download/<torrent name>.123456.d34db33f
        # Website URL: .../torrents/<torrent name>.123456
        torrent_page_url = torrent_download_url.replace('/torrent/download/', '/torrents/')
        torrent_page_url = re.sub(r'\.[a-zA-Z0-9]+$', '', torrent_page_url)
        return torrent_page_url

    @staticmethod
    def calculate_piece_size(bytes):
        # Upload page says:
        #
        #  4 -   8 GB = 1 MB piece size
        #  8 -  16 GB = 2 MB piece size
        # 16 -  72 GB = 4 MB piece size
        # 72 - 190 GB = 8 MB piece size
        #
        # We assume "[MG]B" means "[MG]iB" because piece sizes in MB would be
        # weird.

        piece_size_map = {
            (1, 8 * 1024 * 1024 * 1024 - 1): 1 * 1024 * 1024,                         # 1 MiB
            (8 * 1024 * 1024 * 1024, 16 * 1024 * 1024 * 1024 - 1): 2 * 1024 * 1024,   # 2 MiB
            (16 * 1024 * 1024 * 1024, 72 * 1024 * 1024 * 1024 - 1): 4 * 1024 * 1024,  # 4 MiB
            (72 * 1024 * 1024 * 1024, float('inf')): 8 * 1024 * 1024,                 # 8 MiB
        }

        for (min_size, max_size), piece_size in piece_size_map.items():
            if min_size <= bytes <= max_size:
                return piece_size

        raise RuntimeError(f'Cannot calculate piece size for {bytes} bytes')
