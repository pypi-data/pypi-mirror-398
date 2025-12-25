"""
Concrete :class:`~.TrackerBase` subclass for MTV
"""

import re
import urllib

from ... import __project_name__, errors, utils
from ..base import TrackerBase
from . import config, rules
from .jobs import MtvTrackerJobs

import logging  # isort:skip
_log = logging.getLogger(__name__)


class MtvTracker(TrackerBase):
    name = 'mtv'
    label = 'MTV'
    torrent_source_field = 'MTV'

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

    TrackerJobs = MtvTrackerJobs
    TrackerConfig = config.MtvTrackerConfig
    cli_arguments = config.cli_arguments
    rules = rules

    @property
    def _base_url(self):
        return self.options['base_url']

    @property
    def _login_url(self):
        return urllib.parse.urljoin(self._base_url, '/login')

    @property
    def _login_tfa_url(self):
        return urllib.parse.urljoin(self._base_url, '/twofactor/login')

    @property
    def _logout_url(self):
        return urllib.parse.urljoin(self._base_url, '/logout')

    @property
    def _upload_url(self):
        return urllib.parse.urljoin(self._base_url, '/upload.php')

    @property
    def _torrents_url(self):
        return urllib.parse.urljoin(self._base_url, '/torrents.php')

    async def _request(self, method, *args, **kwargs):
        return await getattr(utils.http, method.lower())(
            *args,
            user_agent=True,
            cookies=self.cookies_filepath,
            follow_redirects=False,
            **kwargs,
        )

    async def _login(self, *, tfa_otp=None):
        if not self.options.get('username'):
            raise errors.RequestError('Login failed: No username configured')
        elif not self.options.get('password'):
            raise errors.RequestError('Login failed: No password configured')

        if not tfa_otp:
            # First request sends username and password.
            request_kwargs = {
                'url': self._login_url,
                'data': {
                    'token': await self._get_token(self._login_url),
                    'username': self.options['username'],
                    'password': self.options['password'],
                    # Tell the server to remember our user session if the user wants to store it.
                    'keeploggedin': '1' if self.cookies_filepath else None,
                    # Lock session to our IP address unless we have a long-running user session
                    # during which our IP address may change.
                    'iplocked': None if self.cookies_filepath else '1',
                    'cinfo': '1280|720|24|0',
                    'submit': 'login',
                },
            }
        else:
            # Second request sends 2FA OTP.
            request_kwargs = {
                'url': self._login_tfa_url,
                'data': {
                    'token': await self._get_token(self._login_tfa_url),
                    'code': tfa_otp,
                    'submit': 'login'
                },
            }

        response = await self._request('POST', **request_kwargs)
        if response.headers.get('location', '').endswith('twofactor/login'):
            raise errors.TfaRequired('2FA OTP required')

    async def confirm_logged_in(self):
        response = await self._request('GET', self._base_url)
        doc = utils.html.parse(response)
        user_page_link_regex = re.compile(r'/user.php(?:\?|.*?&)id=(\d+)')
        user_page_link_tag = doc.find('a', href=user_page_link_regex)
        if not user_page_link_tag:
            raise errors.RequestError('Login failed')

    async def _logout(self):
        token = await self._get_token(self._base_url)
        await self._request(
            'POST',
            url=self._logout_url,
            data={'token': token},
        )

    async def get_announce_url(self):
        if self.options.get('announce_url'):
            return self.options['announce_url'].get_secret_value()
        elif not self.is_logged_in:
            raise RuntimeError('Cannot get announce URL from website if not logged in')
        else:
            response = await self._request('GET', self._upload_url)
            doc = utils.html.parse(response)
            announce_url_tag = doc.find('input', value=re.compile(r'^https?://.*/announce\b'))
            if announce_url_tag:
                return announce_url_tag['value']
            else:
                cmd = f'{__project_name__} set trackers.{self.name}.announce_url YOUR_URL'
                raise errors.RequestError(f'Failed to find announce URL - set it manually: {cmd}')

    @staticmethod
    def calculate_piece_size_min_max(_bytes):
        """Anything from 32 KiB to 8 MiB is fine, regardless of content size"""
        return (
            32 * 1024,        # 32 KiB
            8 * (1024 ** 2),  # 8 MiB
        )

    async def upload(self, tracker_jobs):
        _log.debug('Initial POST data:\n')
        for k, v in tracker_jobs.post_data_upload.items():
            _log.debug(' * %s = %s', k, v)

        autofill_post_data = await self._make_autofill_request(tracker_jobs)
        _log.debug('Autofill data: %r', autofill_post_data)

        torrent_page_url = await self._make_upload_request(tracker_jobs, autofill_post_data)
        _log.debug('Torrent page URL: %r', torrent_page_url)
        return torrent_page_url

    async def _make_autofill_request(self, tracker_jobs):
        # First request uploads the torrent file. We extract "tempfileid" and
        # "tempfilename" from the returned HTML form that must be returned in
        # the second request. We can also extract the autogenerated "taglist".
        post_data = await self._prepare_post_data(tracker_jobs.post_data_autofill)
        _log.debug('Autofill POST data: %r', post_data)
        post_files = {
            'file_input': {
                'file': tracker_jobs.torrent_filepath,
                'mimetype': 'application/x-bittorrent',
            },
        }

        response = await self._request(
            'POST',
            url=self._upload_url,
            cache=False,
            data=post_data,
            files=post_files,
        )

        doc = utils.html.parse(response)
        try:
            return {
                'tempfileid': self._get_form_value(doc, 'input', attrs={'name': 'tempfileid'}),
                'tempfilename': self._get_form_value(doc, 'input', attrs={'name': 'tempfilename'}),
                'taglist': self._get_form_value(doc, 'textarea', attrs={'name': 'taglist'}),
            }
        except ValueError as e:
            # If we can't find required values, look for error message
            _log.debug('Failed to extract values from autofill response: %s', e)
            self._raise_error(doc, msg_prefix='Upload failed', tracker_jobs=tracker_jobs)

    async def _make_upload_request(self, tracker_jobs, autofill_post_data):
        # Second request combines our metadata with server-generated data from
        # _make_autofill_request().
        post_data = await self._prepare_post_data(tracker_jobs.post_data_upload)
        post_data.update(autofill_post_data)

        _log.debug('Final POST data:\n')
        for k, v in post_data.items():
            _log.debug(' * %s = %s', k, v)

        response = await self._request(
            'POST',
            url=self._upload_url,
            cache=False,
            data=post_data,
        )

        # Get URL to uploaded torrent from HTTP 302 redirect location
        redirect_path = response.headers.get('location', '')
        _log.debug('HTTP 302 redirect location: %r', redirect_path)
        if 'torrents.php' in redirect_path:
            torrent_page_url = urllib.parse.urljoin(self._base_url, redirect_path)
            return torrent_page_url

        # Find error message in HTML
        doc = utils.html.parse(response)
        self._raise_error_dupes(doc)
        try:
            self._raise_error(doc, msg_prefix='Upload failed', tracker_jobs=tracker_jobs)
        except RuntimeError:
            # _raise_error() can't find an error message.
            # Dump response headers for debugging.
            # HTML was already dumped by _raise_error()
            headers_filepath = f'{utils.fs.basename(tracker_jobs.content_path)}.headers'
            with open(headers_filepath, 'w') as f:
                for k, v in response.headers.items():
                    f.write(f'{k}: {v}\n')
            raise

    async def _prepare_post_data(self, post_data):
        post_data['auth'] = await self._get_auth()
        return post_data

    async def _get_token(self, url):
        # Return hidden <input name="token"> tag's value.
        response = await self._request('GET', url)
        doc = utils.html.parse(response)
        return self._get_form_value(doc, 'input', attrs={'name': 'token'})

    async def _get_auth(self):
        # "auth" seems to be a random string that never changes, and it must be
        # returned in upload requests.
        if not hasattr(self, '_auth'):
            assert self.is_logged_in
            response = await self._request('GET', self._upload_url)
            doc = utils.html.parse(response)

            # There is a limit for unchecked torrents. Of course, it is not presented like any other
            # error message and there is no straightforward way to find in the HTML soup.
            tags = doc.select('#upload #content > div > div > h2')
            if tags:
                text = utils.html.as_text(tags[0])
                if re.search(r'\d+ torrents awaiting staff approval', text):
                    raise errors.RequestError(text)

            self._auth = self._get_form_value(doc, 'input', attrs={'name': 'auth'})

        return self._auth

    def _get_form_value(self, doc, tag_name, **kwargs):
        try:
            tag = doc.find(tag_name, **kwargs)

            # <input value="...">
            value = tag.get('value')
            if value:
                return value

            # <textarea>value</textarea>
            value = utils.html.as_text(tag)
            if value:
                return value

            raise ValueError(f'Tag has no value: {tag}')

        except AttributeError:
            pass

        raise ValueError(f'Could not find tag: {tag_name}')

    def _raise_error(self, doc, msg_prefix, tracker_jobs=None):
        error_tag = doc.find('div', attrs={'class': 'error'})
        if error_tag:
            msg = utils.html.as_text(error_tag)
            raise errors.RequestError(f'{msg_prefix}: {msg}')

        # Example error: "The exact same torrent file already exists on the site!"
        alert_tag = doc.find('div', attrs={'class': 'alert'})
        if alert_tag:
            msg = utils.html.as_text(alert_tag)
            raise errors.RequestError(f'{msg_prefix}: {msg}')

        # TODO: Remove this if the "zero bytes response / GroupID cannot be null" bug is fixed.
        #       Also remember to remove the then unnecessary `tracker_jobs` argument.
        if not doc.string and tracker_jobs:
            _log.debug('Empty server response: %r', doc.prettify())
            bug_report = ' '.join((
                tracker_jobs.release_name.title_with_aka_and_year,
                f'https://imdb.com/title/{tracker_jobs.imdb_id}',
            ))
            forum_link = f'{self._base_url}/forum/thread/3338'
            raise errors.RequestError(
                f'{msg_prefix}: "GroupID cannot be null" bug encountered.\n'
                '\n'
                f'Please post the following information here: {forum_link}\n'
                '\n'
                f'    {bug_report}\n'
                '\n'
                f'You will get a reply from staff when the issue is fixed and you can try again.\n'
                '\n'
                'Here is an owl for your inconvenience:\n'
                '\n'
                '   ^ ^\n'
                '  (O,O)\n'
                '\\ (   )   _,~´\n'
                ' `~"-"~~~´\n'
            )

        filepath = f'{msg_prefix}.{self.name}.html'
        utils.html.dump(doc, filepath)
        raise RuntimeError(f'{msg_prefix}: No error message found (dumped HTML response to {filepath})')

    def _raise_error_dupes(self, doc):
        dupes_warning = doc.find('div', id="messagebar", string=re.compile(r'(?i:dupes?|duplicates?)'))
        if dupes_warning:
            _log.debug('Found dupes warning: %s', dupes_warning)
            table = doc.find('table', id='torrent_table')
            if table:
                dupe_files = tuple(
                    utils.html.as_text(cell)
                    for row in table.find_all('tr', attrs={'class': 'torrent'})
                    for cell in row.find('td', attrs={'class': 'torrent'})
                )
                if dupe_files:
                    raise errors.FoundDupeError(dupe_files)
