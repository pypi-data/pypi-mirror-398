"""
Concrete :class:`~.TrackerBase` subclass for PTP
"""

import asyncio
import math
import re
import urllib

from ... import errors, utils
from ..base import TrackerBase
from . import config, rules
from .jobs import PtpTrackerJobs

import logging  # isort:skip
_log = logging.getLogger(__name__)


class PtpTracker(TrackerBase):
    name = 'ptp'
    label = 'PTP'
    torrent_source_field = 'PTP'

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
        '{howto.next_section}. Announce URL\n'
        '\n'
        '   The announce URL is required because the passkey is used as another authentication factor.\n'
        '   $ upsies set trackers.{tracker.name}.announce_url ANNOUNCE_URL\n'
        '\n'
        '{howto.next_section}. Screenshots\n'
        '\n'
        '   {howto.current_section}.1 Configure ptpimg.me API key.\n'
        '       $ upsies upload-images ptpimg --help\n'
        '\n'
        '   {howto.current_section}.2 Specify how many screenshots to make. (optional)\n'
        '       $ upsies set trackers.{tracker.name}.screenshots_from_movie NUMBER_OF_MOVIE_SCREENSHOTS\n'
        '       $ upsies set trackers.{tracker.name}.screenshots_from_episode NUMBER_OF_EPISODE_SCREENSHOTS\n'
        '\n'
        '{howto.autoseed}\n'
        '\n'
        '{howto.reuse_torrents}\n'
        '\n'
        '{howto.upload}\n'
    )

    TrackerJobs = PtpTrackerJobs
    TrackerConfig = config.PtpTrackerConfig
    cli_arguments = config.cli_arguments
    rules = rules

    @property
    def _base_url(self):
        return self.options['base_url']

    @property
    def _ajax_url(self):
        return urllib.parse.urljoin(self._base_url, '/ajax.php')

    @property
    def _artist_url(self):
        return urllib.parse.urljoin(self._base_url, '/artist.php')

    @property
    def _logout_url(self):
        return urllib.parse.urljoin(self._base_url, '/logout.php')

    @property
    def _upload_url(self):
        return urllib.parse.urljoin(self._base_url, '/upload.php')

    @property
    def _torrents_url(self):
        return urllib.parse.urljoin(self._base_url, '/torrents.php')

    @property
    def _announce_url(self):
        announce_url = self.options['announce_url']
        if not announce_url:
            raise errors.AnnounceUrlNotSetError(tracker=self)
        else:
            return announce_url.get_secret_value()

    @property
    def _passkey(self):
        # Needed for logging in with ajax.php
        match = re.search(r'.*/([a-zA-Z0-9]+)/announce', self._announce_url)
        if match:
            return match.group(1)
        else:
            raise RuntimeError(f'Failed to find passkey in announce URL: {self._announce_url}')

    async def _request(self, method, *args, error_prefix='', **kwargs):
        # Because HTTP errors (e.g. 404) are raised, we treat RequestErrrors as
        # normal response so we can get the message from the HTML.
        try:
            # `method` is "GET" or "POST"
            response = await getattr(utils.http, method.lower())(
                *args,
                user_agent=True,
                follow_redirects=False,
                cookies=self.cookies_filepath,
                **kwargs,
            )
        except errors.RequestError as e:
            response = e

        # Get error from regular exception (e.g. "Connection refused") or the
        # HTML in response.
        try:
            self._maybe_raise_error(response)
        except errors.RequestError as e:
            # Prepend error_prefix to explain the general nature of the error.
            if error_prefix:
                raise errors.RequestError(f'{error_prefix}: {e}') from e
            else:
                raise e
        else:
            return response

    def _maybe_raise_error(self, response_or_request_error):
        # utils.http.get()/post() raise RequestError on HTTP status codes, but
        # we want to get the error message from the response text.
        # _maybe_raise_error_from_*() handle Response and RequestError.
        self._maybe_raise_error_from_json(response_or_request_error)
        self._maybe_raise_error_from_html(response_or_request_error)

        # If we got a RequestError and we didn't find an error message in the
        # text, we raise it. This handles any real RequestErrors, like
        # "Connection refused". We also raise any other exception so _request()
        # doesn't return it as a regular response.
        if isinstance(response_or_request_error, BaseException):
            raise response_or_request_error

    def _maybe_raise_error_from_json(self, response_or_request_error):
        # Get error message from ajax.php JSON Response or RequestError
        try:
            json = response_or_request_error.json()
        except errors.RequestError:
            # Response or RequestError is not JSON
            pass
        else:
            if (
                isinstance(json, dict)
                and json.get('Result') == 'Error'
                and json.get('Message')
            ):
                raise errors.RequestError(utils.html.as_text(json['Message']))

    def _maybe_raise_error_from_html(self, response_or_request_error):
        # Only attempt to find an error message if this looks like HTML. This
        # prevents a warning from bs4 about parsing non-HTML.
        text = str(response_or_request_error)
        if all(c in text for c in '<>\n'):
            doc = utils.html.parse(text)
            try:
                error_header_tag = doc.select('#content .page__title', string=re.compile(r'(?i:error)'))
                error_container_tag = error_header_tag[0].parent
                error_msg_tag = error_container_tag.find('div', attrs={'class': 'panel__body'})
                error_msg = error_msg_tag.get_text().strip()
                if error_msg:
                    raise errors.RequestError(error_msg)
            except (AttributeError, IndexError):
                # No error message found
                pass

    async def _login(self, *, tfa_otp=None):
        if not self.options.get('username'):
            raise errors.RequestError('Login failed: No username configured')
        elif not self.options.get('password'):
            raise errors.RequestError('Login failed: No password configured')

        post_data = {
            'username': self.options['username'],
            'password': self.options['password'],
            'passkey': self._passkey,
            # Do not send Tfa* on the first request. (`None` values are exluded from the POST data.)
            'TfaType': 'normal' if tfa_otp else None,
            'TfaCode': tfa_otp,
            # Tell the server to remember our user session if the user wants to store it.
            'keeplogged': '1' if self.cookies_filepath else None,
        }

        response = await self._request(
            method='POST',
            url=self._ajax_url,
            params={'action': 'login'},
            data=post_data,
            error_prefix='Login failed',
        )
        json = response.json()

        if json.get('Result') == 'TfaRequired':
            # Raise exception to get called again with `tfa_otp`.
            raise errors.TfaRequired(f'2FA OTP required: {response.json()!r}')

        elif json.get('Result') == 'Error':
            if msg := json.get('Message'):
                raise errors.RequestError(f'Login failed: {utils.html.as_text(msg)}')
            else:
                raise errors.RequestError('Login failed')

    async def confirm_logged_in(self):
        response = await self._request('GET', self._base_url, cache=False)
        doc = utils.html.parse(response)
        self._session = {
            'auth': self._find_auth(doc),
            'anti_csrf_token': self._find_anti_csrf_token(doc),
        }

    def _find_auth(self, doc):
        auth_regex = re.compile(r'logout\.php\?.*\bauth=([0-9a-zA-Z]+)')
        logout_link_tag = doc.find('a', href=auth_regex)
        if logout_link_tag:
            logout_link_href = logout_link_tag['href']
            match = auth_regex.search(logout_link_href)
            return match.group(1)
        raise errors.RequestError('Could not find auth')

    def _find_anti_csrf_token(self, doc):
        body_tag = doc.find('body')
        if body_tag:
            anti_csrf_token = body_tag.get('data-anticsrftoken', None)
            if anti_csrf_token:
                return anti_csrf_token
        raise errors.RequestError('Could not find anti_csrf_token')

    async def _logout(self):
        try:
            auth = self._session['auth']
        except (AttributeError, KeyError) as e:
            raise RuntimeError('Session information not found') from e
        delattr(self, '_session')

        response = await self._request(
            method='GET',
            url=self._logout_url,
            params={'auth': auth},
            error_prefix='Logout failed',
        )
        _log.debug('Logout response: %r', response)

    async def get_announce_url(self):
        return self._announce_url

    async def upload(self, tracker_jobs):
        post_data = tracker_jobs.post_data
        post_data['AntiCsrfToken'] = self._session['anti_csrf_token']

        _log.debug('POSTing data:')
        for k, v in post_data.items():
            _log.debug(' * %s = %s', k, v)

        post_files = {
            'file_input': {
                'file': tracker_jobs.torrent_filepath,
                'mimetype': 'application/x-bittorrent',
            },
        }
        _log.debug('POSTing files: %r', post_files)

        response = await utils.http.post(
            url=self._upload_url,
            cache=False,
            user_agent=True,
            data=post_data,
            files=post_files,
            # Ignore the HTTP redirect (should be 302 Found) so we can get the
            # torrent URL from the "Location" response header
            follow_redirects=False,
        )

        # The server needs some time to process the uploaded metadata before the
        # torrent is registered by the tracker and we can seed it. If we don't
        # sleep() here, the torrent may be announced before the tracker knows it
        # exists.
        await asyncio.sleep(3)

        return self._handle_upload_response(response)

    def _handle_upload_response(self, response):
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
        doc = utils.html.parse(response)

        # Find and raise error message
        alert_tag = doc.find(class_='alert')
        if alert_tag:
            msg = utils.html.as_text(alert_tag)
            raise errors.RequestError(f'Upload failed: {msg}')

        # Failed to find error message
        dump_filepath = 'ptp_upload_failed.html'
        utils.html.dump(response, dump_filepath)
        raise errors.RequestError(f'Failed to interpret response (see {dump_filepath})')

    def normalize_imdb_id(self, imdb_id):
        """
        Format IMDb ID for PTP

        PTP expects 7-characters, right-padded with "0" and without the leading
        "tt".

        If `imdb_id` is falsy (e.g. `None`, empty string, etc), or if it isn't
        an IMDb ID, return "0".
        """
        imdb_id = str(imdb_id)
        match = re.search(r'^(?:tt|)(\d+)$', imdb_id)
        if match:
            imdb_id_digits = match.group(1)
            if set(imdb_id_digits) != {'0'}:
                return match.group(1).rjust(7, '0')
        return '0'

    async def get_ptp_group_id_by_imdb_id(self, imdb_id):
        """
        Convert IMDb ID to PTP group ID

        Any :class:`~.RequestError` is caught and passed to
        :meth:`.TrackerBase.error`.

        :return: PTP group ID or `None` if PTP doesn't have a group for
            `imdb_id`
        :raise RequestError: if the request fails.
        """
        if imdb_id:
            _log.debug('%s: Fetching PTP group ID', imdb_id)
            # We must be logged in first.
            await self.signal.wait_for('logged_in')

            response = await self._request(
                method='GET',
                url=self._torrents_url,
                params={
                    'imdb': self.normalize_imdb_id(imdb_id),
                    'json': '1',
                },
                cache=True,
            )

            match = re.search(r'id=(\d+)', response.headers.get('location', ''))
            if match:
                _log.debug('%s: PTP group ID: %s', imdb_id, match.group(1))
                return match.group(1)
            else:
                _log.debug('%s: No PTP group ID', imdb_id)

    async def get_movie_metadata(self, imdb_id):
        """
        Get metadata about movie as :class:`dict` from PTP website

        :param imdb_id: IMDb ID (e.g. ``tt123456``)

        The returned :class:`dict` always has the following keys:

            - ``countries`` (:class:`tuple` of :class:`str`)
            - ``languages`` (:class:`tuple` of :class:`str`)
            - ``plot`` (:class:`str`)
            - ``poster`` (:class:`str`, image URL)
            - ``tags`` (:class:`tuple` of :class:`str`)
            - ``title`` (:class:`str`)
            - ``year`` (:class:`str`)

        :raise RequestedNotFoundError: if no metadata is found.
        :raise RequestError: if the request fails.
        """
        _log.debug('%s: Fetching metadata from PTP', imdb_id)
        metadata = {}
        if imdb_id:
            # We must be logged in first.
            await self.signal.wait_for('logged_in')
            response = await self._request(
                method='GET',
                url=self._ajax_url,
                params={
                    'action': 'torrent_info',
                    'imdb': self.normalize_imdb_id(imdb_id),
                },
                cache=True,
            )

            # We expect a list of JSON objects that contains exactly one JSON object.
            results = response.json()
            _log.debug('%s: Raw movie metadata: %r', imdb_id, response)

            # Response should be a JSON list containing exactly one search result, but we don't rely
            # on that because this is not documented anywhere.
            if isinstance(results, list) and len(results) == 1:
                metadata = results[0]
                # If `imdb_id` is invalid/unknown, "title" is `null` (None) in the JSON response.
                if not isinstance(metadata, dict) or not metadata.get('title'):
                    raise errors.RequestedNotFoundError(imdb_id)
            else:
                raise errors.RequestedNotFoundError(imdb_id)

        def comma_split(string):
            lst = []
            for val in string.split(','):
                val = val.strip()
                if val:
                    lst.append(val)
            return lst

        return {
            'title': metadata.get('title') or '',
            'plot': metadata.get('plot') or '',
            'poster': metadata.get('art') or '',
            'year': metadata.get('year') or '',
            'tags': comma_split(metadata.get('tags', '')),
            'countries': comma_split(metadata.get('Countries', '')),
            'languages': comma_split(metadata.get('Languages', '')),
        }

    async def get_artist_metadata(self, artist):
        """
        Get metadata about artist as :class:`dict` from PTP website

        :param artist: Name, IMDb URL/ID (e.g. ``nm123456``) or PTP URL/ID

        :raise RequestedNotFoundError: if `artist` is unknown on both PTP and
            IMDb.
        :raise RequestError: if the metadata request fails.
        """
        _log.debug('%s: Fetching artist metadata from PTP', artist)
        # We must be logged in first.
        await self.signal.wait_for('logged_in')
        try:
            response = await self._request(
                method='POST',
                url=self._artist_url,
                data={
                    'action': 'find',
                    'name': (
                        # PTP accepts PTP artist URLs, but not a naked ID.
                        self._get_artist_url(artist)
                        if re.search(r'^\d+$', artist) else
                        artist
                    ),
                    'AntiCsrfToken': self._session['anti_csrf_token'],
                },
                cache=True,
            )
        except errors.RequestError as e:
            if 'not found' in str(e):
                raise errors.RequestedNotFoundError(artist) from e
            else:
                raise e
        else:
            return self._get_artist_dict(response)

    async def create_artist(self, name):
        """
        Create artist on PTP

        .. warning:: This must only be called if the artist doesn't exist on
            IMDb or PTP.

        :param name: Complete canonical name of the artist

        :return: :class:`dict` with the keys: ``name``, ``id``, ``url``

        :raise RequestError: if the metadata request fails.
        """
        _log.debug('Creating artist: %r', name)
        # We must be logged in first.
        await self.signal.wait_for('logged_in')
        response = await self._request(
            method='POST',
            url=self._artist_url,
            data={
              'action': 'create',
              'name': name,
              'AntiCsrfToken': self._session['anti_csrf_token'],
            },
            cache=False,
        )
        return self._get_artist_dict(response)

    def _get_artist_dict(self, response):
        _log.debug('Raw artist metadata: %r', response)
        # Raise RequestError if response is not valid JSON.
        artist = response.json()
        try:
            return {
                'name': artist['ArtistName'],
                'id': artist['ArtistId'],
                'url': self._get_artist_url(artist['ArtistId'])
            }
        except KeyError as e:
            if artist.get('Message'):
                raise errors.RequestError(artist['Message']) from e
            else:
                raise errors.RequestError(f'Unexpected response: {artist}') from e

    def _get_artist_url(self, artist_id):
        return self._artist_url + '?id=' + str(artist_id)

    @staticmethod
    def calculate_piece_size(bytes):
        """
        Return the recommended piece size for a given content size

        :param bytes: Torrent's content size without any excluded files
        """
        exponent = math.ceil(math.log2(bytes / 1050))
        # Allowed piece size range: 32 KiB ... 16 MiB
        exponent = max(15, min(24, exponent))
        return int(math.pow(2, exponent))

    @staticmethod
    def calculate_piece_size_min_max(bytes):
        """
        Return the allowed minimum and maximum piece size for a given
        content size

        :param bytes: torrent's content size without any excluded files

        :raise ValueError: if `bytes` is negative or otherwise unexpected
        """
        if bytes <= 0:
            raise ValueError(f'Unexpected size: {bytes!r}')

        # NOTE: The algorithm below is from the website's javascript.

        max_exponent = math.ceil(math.log2(bytes / 500))
        min_exponent = math.floor(math.log2(bytes / 2000))

        # 2^24 or 16MiB is the max for uTorrent 2.x
        min_exponent = min(24, min_exponent)
        max_exponent = min(24, max_exponent)

        # Compatibility for uTorrent 2.x creator which only supports up to 4 MiB piece sizes
        if min_exponent > 22 and bytes <= 128 * 1024 * 1024 * 1024:
            min_exponent = 22
        if min_exponent > 22 and bytes <= 256 * 1024 * 1024 * 1024:
            min_exponent = 23

        # Tiny torrents < ~40MiB need a sane lower bound
        min_exponent = max(15, min_exponent)
        max_exponent = max(18, max_exponent)

        return (
            math.pow(2, min_exponent),
            math.pow(2, max_exponent),
        )
