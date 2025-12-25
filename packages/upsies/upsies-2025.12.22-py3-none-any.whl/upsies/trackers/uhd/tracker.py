"""
Concrete :class:`~.TrackerBase` subclass for UHD
"""

import asyncio
import re
import urllib

from ... import __project_name__, errors, utils
from ..base import TrackerBase
from . import config, rules
from .jobs import UhdTrackerJobs

import logging  # isort:skip
_log = logging.getLogger(__name__)


class UhdTracker(TrackerBase):
    name = 'uhd'
    label = 'UHD'
    torrent_source_field = '[UHDBits]'

    setup_howto_template = (
        '{howto.introduction}\n'
        '\n'
        '{howto.next_section}. Login Credentials\n'
        '\n'
        '   {howto.current_section}.1 $ upsies set trackers.{tracker.name}.username USERNAME\n'
        '   {howto.current_section}.2 $ upsies set trackers.{tracker.name}.password PASSWORD\n'
        '   {howto.current_section}.3 Store the login session cookie. (optional)\n'
        '       $ upsies set trackers.{tracker.name}.cookies_filepath "~/.cache/upsies/{tracker.name}.cookies"\n'
        '       WARNING: Anyone with acces to that file has full control over your {tracker.label} account.\n'
        '\n'
        '{howto.next_section}. Announce URL (Optional)\n'
        '\n'
        '   The announce URL is fetched from the website on demand, but you can\n'
        '   also configure it explicitly.\n'
        '\n'
        '   {howto.current_section}.1 $ upsies set trackers.{tracker.name}.announce_url ANNOUNCE_URL\n'
        '\n'
        '{howto.screenshots}\n'
        '\n'
        '{howto.autoseed}\n'
        '\n'
        '{howto.reuse_torrents}\n'
        '\n'
        '{howto.upload}\n'
    )

    TrackerJobs = UhdTrackerJobs
    TrackerConfig = config.UhdTrackerConfig
    cli_arguments = config.cli_arguments
    rules = rules

    @property
    def _base_url(self):
        return self.options['base_url']

    @property
    def _login_url(self):
        return urllib.parse.urljoin(self._base_url, '/login.php')

    @property
    def _logout_url(self):
        return urllib.parse.urljoin(self._base_url, '/logout.php')

    @property
    def _ajax_url(self):
        return urllib.parse.urljoin(self._base_url, '/ajax.php')

    @property
    def _upload_url(self):
        return urllib.parse.urljoin(self._base_url, '/upload.php')

    @property
    def _torrents_url(self):
        return urllib.parse.urljoin(self._base_url, '/torrents.php')

    async def _request(self, method, *args, error_prefix='', **kwargs):
        try:
            # `method` is "GET" or "POST"
            return await getattr(utils.http, method.lower())(
                *args,
                user_agent=True,
                cache=False,
                cookies=self.cookies_filepath,
                **kwargs,
            )
        except errors.RequestError as e:
            if error_prefix:
                raise errors.RequestError(f'{error_prefix}: {e}') from e
            else:
                raise e

    def _failed_to_find_error(self, doc, msg_prefix):
        filepath = f'{msg_prefix}.{self.name}.html'
        utils.html.dump(doc, filepath)
        raise RuntimeError(f'{msg_prefix}: No error message found (dumped HTML response to {filepath})')

    async def _login(self, *, tfa_otp=None):
        if not self.options.get('username'):
            raise errors.RequestError('Login failed: No username configured')
        elif not self.options.get('password'):
            raise errors.RequestError('Login failed: No password configured')

        post_data = {
            'username': self.options['username'],
            'password': self.options['password'],
            'keeplogged': '1' if self.cookies_filepath else None,
            'two_step': tfa_otp or '',  # 2FA
            'login': 'Log in',
        }
        error_prefix = 'Login failed'
        response = await self._request(
            method='POST',
            url=self._login_url,
            data=post_data,
            error_prefix=error_prefix,
        )
        doc = utils.html.parse(response)
        self._find_error(doc, error_prefix=error_prefix)

    def _find_error(self, doc, *, error_prefix):
        msg = None

        # Find: "Your username or password was incorrect."
        if tag := doc.find('form', action='login.php'):
            # Remove actual <form> to leave us with only the error message.
            tag.table.extract()
            msg = utils.html.as_text(tag)

        # Find: "Wrong 2FA Pin!"
        # Find: "You have 2FA enabled on your account. Fill in the code from your device!"
        elif tag := doc.find('h2', string=re.compile('error', flags=re.IGNORECASE)):
            msg = utils.html.as_text(tag.parent.parent.find('p'))
            if '2FA' in msg:
                # Request OTP from user and call _login(tfa_otp=...) again.
                raise errors.TfaRequired('2FA OTP required')

        if msg:
            raise errors.RequestError(f'{error_prefix}: {msg}')

    async def confirm_logged_in(self):
        response = await self._request('GET', self._base_url)
        doc = utils.html.parse(response)
        auth_regex = re.compile(r'logout\.php\?.*\bauth=([0-9a-zA-Z]+)')
        logout_link_tag = doc.find('a', href=auth_regex)
        if logout_link_tag:
            logout_link_href = logout_link_tag['href']
            match = auth_regex.search(logout_link_href)
            self._auth = match.group(1)
        else:
            raise errors.RequestError('Login failed for unknown reason')

    async def _logout(self):
        try:
            await self._request(
                method='GET',
                url=self._logout_url,
                params={'auth': self._auth},
                error_prefix='Logout failed',
            )
        finally:
            delattr(self, '_auth')

    async def get_announce_url(self):
        if self.options.get('announce_url'):
            return self.options['announce_url'].get_secret_value()
        elif not self.is_logged_in:
            raise RuntimeError('Cannot get announce URL from website if not logged in')
        else:
            response = await self._request(
                method='GET',
                url=self._upload_url,
            )
            doc = utils.html.parse(response)
            announce_url_tag = doc.find('input', value=re.compile(r'^https?://.*/announce\b'))
            if announce_url_tag:
                return announce_url_tag['value']
            else:
                cmd = f'{__project_name__} set trackers.{self.name}.announce_url YOUR_URL'
                raise errors.RequestError(f'Failed to find announce URL - set it manually: {cmd}')

    @utils.blocking_memoize
    async def get_uhd_info(self, imdb_id):
        """
        Get IMDb information from tracker

        :param imdb_id: IMDb ID

        The return value is a dictionary returned by ajax.php. It may contain
        arbitrary keys or be empty.
        """
        assert imdb_id, 'IMDb ID is not available yet'

        try:
            # If ajax.php doesn't have the info cached, it responds with
            # {"error": "1"}, in which case, we wait a decreasing number of
            # seconds before trying again. This is more or less what the website
            # JS is doing.

            # Example responses:
            # {"error":1,"message":" Submited to fetcher..."}
            # {"error":1,"message":" Fetching..."}
            # {'status': 'failure', 'error': 'rate limit exceeded'}

            # Wait 6 seconds after the first try, then 3 seconds for up to 4
            # minutes combined.
            for sleep in (6,) + (3,) * 20 * 4:
                uhd_info = await self._get_uhd_info(imdb_id)
                if str(uhd_info.get('error', '1')) == '0':
                    _log.debug('UHD info: %r', uhd_info)
                    return uhd_info
                if str(uhd_info.get('error')) not in ('1', '0'):
                    _log.debug('Failed to get UHD info for %s: %r', imdb_id, uhd_info['error'])
                    break
                else:
                    _log.debug('Still waiting for UHD info: %r', uhd_info)
                    await asyncio.sleep(sleep)

        except errors.RequestError as e:
            _log.debug('Failed to get UHD info for %s: %r', imdb_id, e)
            pass

        return {}

    async def _get_uhd_info(self, imdb_id):
        params = {
            'action': 'imdb_fetch',
            'imdbid': imdb_id,
        }
        _log.debug(
            'UHD info URL for %s: %s?%s',
            imdb_id,
            self._ajax_url,
            '&'.join(
                f'{key}={urllib.parse.quote_plus(value)}'
                for key, value in params.items()
            ),
        )
        response = await self._request(
            method='GET',
            url=self._ajax_url,
            params=params,
            # Requesting information about unknown IDs can take a long time.
            timeout=10 * 60,
        )
        return response.json()

    async def upload(self, tracker_jobs):
        assert self.is_logged_in

        post_data = tracker_jobs.post_data
        post_data['auth'] = self._auth

        _log.debug('POSTing data:')
        for k, v in post_data.items():
            _log.debug(' * %s = %s', k, v)

        post_files = tracker_jobs.post_files
        _log.debug('POSTing files: %r', post_files)

        response = await self._request(
            method='POST',
            url=self._upload_url,
            data=post_data,
            files=post_files,
            follow_redirects=False,
        )
        return self._handle_upload_response(response)

    def _handle_upload_response(self, response):
        _log.debug('############################### HANDLING UPLOAD RESPONSE ##########################')
        # "Location" header should contain the uploaded torrent's URL
        _log.debug('Upload response headers: %r', response.headers)
        location = response.headers.get('Location')
        _log.debug('Upload response location: %r', location)

        if location:
            torrent_page_url = urllib.parse.urljoin(self.options['base_url'], location)
            # Redirect URL should start with "https://.../torrents.php"
            if torrent_page_url.startswith(self._torrents_url):
                return torrent_page_url

        # Find error message in HTML
        msg_prefix = 'Upload failed'
        doc = utils.html.parse(response)
        error_tags = doc.select('#scontent .thin > p + p')
        if error_tags:
            msg = utils.html.as_text(error_tags[0])
            raise errors.RequestError(f'{msg_prefix}: {msg}')

        # Failed to find error message
        self._failed_to_find_error(doc, msg_prefix)
