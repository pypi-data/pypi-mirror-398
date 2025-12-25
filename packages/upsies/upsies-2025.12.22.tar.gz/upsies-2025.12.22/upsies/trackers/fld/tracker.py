"""
Concrete :class:`~.TrackerBase` subclass for FLD
"""

from ... import errors, utils
from ..base import TrackerBase
from . import config, rules
from .jobs import FldTrackerJobs

import logging  # isort:skip
_log = logging.getLogger(__name__)


class FldTracker(TrackerBase):
    name = 'fld'
    label = 'FLD'
    torrent_source_field = 'FLD'

    setup_howto_template = (
        '{howto.introduction}\n'
        '\n'
        '{howto.next_section}. Announce Passkey\n'
        '\n'
        '   {howto.current_section}.1 On the website, go to Settings -> Security\n'
        '       and copy your personal ANNOUNCE_KEY.\n'
        '   {howto.current_section}.2 $ upsies set trackers.{tracker.name}.announce_key ANNOUNCE_KEY\n'
        '\n'
        '{howto.next_section}. API Key\n'
        '\n'
        '   {howto.current_section}.1 On the website, go to Settings -> Security\n'
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
    )

    TrackerJobs = FldTrackerJobs
    TrackerConfig = config.FldTrackerConfig
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
            self.options['announce_key'].get_secret_value(),
        ))

    async def upload(self, tracker_jobs):
        _log.debug('Uploading to %r', self.options['upload_url'])
        _log.debug('POSTing data:')
        post_data = tracker_jobs.post_data
        for k, v in post_data.items():
            _log.debug(' * %s = %s', k, v)

        files = {
            'meta_info': {
                'file': tracker_jobs.torrent_filepath,
                'mimetype': 'application/octet-stream',
            },
        }
        _log.debug('Files: %r', files)

        response = await utils.http.post(
            url=self.options['upload_url'],
            cache=False,
            user_agent=True,
            headers={'Authorization': f'Bearer {self.options["apikey"].get_secret_value()}'},
            files=files,
            data=post_data,
        )
        _log.debug('Upload response: %r', response)
        json = response.json()
        _log.debug('Upload response: %r', json)
        try:
            if json['success']:
                # Upload response: {
                #     'success': True,
                #     'message': "Success",
                #     'torrent_id': "<torrent id>",
                #     'torrent_url': "<torrent detail url>",
                #     'torrent_download': "<torrent download url>",
                # }
                return json['torrent_url']
            else:
                # Upload response: {
                #     'success': False,
                #     'message': "<error message>",
                # }
                raise errors.RequestError(f'Upload failed: {json["message"]}')
        except KeyError as e:
            raise RuntimeError(f'Unexpected response: {response}') from e
