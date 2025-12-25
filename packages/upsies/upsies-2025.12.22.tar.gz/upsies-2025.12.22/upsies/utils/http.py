"""
HTTP methods with caching
"""

import asyncio
import builtins
import collections
import http
import io
import json
import os
import pathlib
import random
import re
import time

import httpx

from .. import __project_name__, __version__, constants, errors, utils

import logging  # isort:skip
_log = logging.getLogger(__name__)

_default_timeout = 180
_default_headers = {
    'Accept-Language': 'en-US,en;q=0.5',
    'User-Agent': f'{__project_name__}/{__version__}',
}

# Use one Lock per requested url + parameters so we can make multiple identical
# requests concurrently without bugging the server.
_request_locks = collections.defaultdict(lambda: asyncio.Lock())

# Map domain names to dictionaries of session cookies
_session_cookies = collections.defaultdict(dict)


cache_directory = None
"""
Where to store cached responses

If this is set to a falsy value, default to
:attr:`~.constants.DEFAULT_CACHE_DIRECTORY`.
"""

def _get_cache_directory():
    return cache_directory or constants.DEFAULT_CACHE_DIRECTORY


async def get(
        url,
        *,
        headers={},
        params={},
        auth=None,
        cache=False,
        max_cache_age=float('inf'),
        user_agent=False,
        follow_redirects=True,
        raise_on_error_status=True,
        verify=True,
        timeout=_default_timeout,
        cookies=None,
        debug_file=None,
    ):
    """
    Perform HTTP GET request

    :param str url: URL to request
    :param dict headers: Custom headers (added to default headers)
    :param dict params: Key value pairs passed in the URL,
        e.g. ``{"k": "v"}`` → ``http://host/get?k=v``
    :param auth: Basic access authentication; sequence of <username> and
        <password> or `None`
    :param bool cache: Whether to use cached response if available
    :param int,float max_cache_age: Maximum age of cache in seconds
    :param user_agent: Custom User-Agent header (:class:`str`), ``True`` to send our User-Agent
        ("upsies/<VERSION>"), the literal string ``BROWSER`` to send a browser User-Agent, or
        ``False`` to not send any User-Agent
    :param bool follow_redirects: Whether to follow redirects
    :param bool raise_on_error_status: Whether to raise :class:`RequestError` if the HTTP status
        code indicates an error (e.g. 404)
    :param bool verify: Whether to verify TLS connection or ignore any errors
        like expired certificate
    :param int,float timeout: Maximum number of seconds the request may take
    :param cookies: Cookies to include in the request (merged with
        existing cookies in the global client session)

        * If `cookies` is a :class:`dict`, forget them after the request.

        * If `cookies` is a :class:`str`, load cookies from that path (if it
          exists), perform the request, and save the new set of cookies to the
          same path. If this is a relative path, `cache_directory` is prepended.

        .. note:: Session cookies are handled separately and automatically.

    :return: Response text
    :rtype: Response
    :raise RequestError: if the request fails for any expected reason
    """
    return await _request(
        method='GET',
        url=url,
        headers=headers,
        params=params,
        auth=auth,
        cache=cache,
        max_cache_age=max_cache_age,
        user_agent=user_agent,
        follow_redirects=follow_redirects,
        raise_on_error_status=raise_on_error_status,
        verify=verify,
        timeout=timeout,
        cookies=cookies,
        debug_file=debug_file,
    )

async def post(
        url,
        *,
        headers={},
        params={},
        data={},
        files={},
        auth=None,
        cache=False,
        max_cache_age=float('inf'),
        user_agent=False,
        follow_redirects=True,
        raise_on_error_status=True,
        verify=True,
        timeout=_default_timeout,
        cookies=None,
        debug_file=None,
    ):
    """
    Perform HTTP POST request

    :param str url: URL to request
    :param dict headers: Custom headers (added to default headers)
    :param dict params: Key value pairs passed in the URL,
        e.g. ``{"k": "v"}`` → ``http://host/get?k=v``
    :param dict data: Data to send as application/x-www-form-urlencoded

        .. note:: `None` values are not included in the POST request.

    :param dict files: Files to send as multipart/form-data as a dictionary that
        maps field names to file paths or dictionaries. For dictionaries, these
        keys are used:

             ``file``
                 File path or file-like object, e.g. return value of
                 :func:`open` or :class:`~.io.BytesIO`.

             ``filename`` (optional)
                 Name of the file that is reported to the server. Defaults to
                 :func:`~.os.path.basename` of ``file`` if ``file`` is a string,
                 `None` otherwise.

             ``mimetype`` (optional)
                 MIME type of the file content. If not provided and `file` is a
                 string, guess based on extension of ``file``. If `None`, do not
                 send any MIME type.

        Examples:

        >>> files = {
        >>>     "image": "path/to/foo.jpg",
        >>>     "document": {
        >>>         "file": "path/to/bar",
        >>>         "filename": "something.txt",
        >>>         "mimetype": "text/plain",
        >>>     },
        >>>     "data": {
        >>>         "file": io.BytesIO(b"binary data"),
        >>>         "mimetype": "application/octet-stream",
        >>>      },
        >>>     "more_data": io.BytesIO(b"more binary data"),
        >>> }
    :param auth: Basic access authentication; sequence of <username> and
        <password> or `None`
    :param bool cache: Whether to use cached response if available
    :param int,float max_cache_age: Maximum age of cache in seconds
    :param user_agent: Custom User-Agent header (:class:`str`), ``True`` to send our User-Agent
        ("upsies/<VERSION>"), the literal string ``BROWSER`` to send a browser User-Agent, or
        ``False`` to not send any User-Agent
    :param bool follow_redirects: Whether to follow redirects
    :param bool raise_on_error_status: Whether to raise :class:`RequestError` if the HTTP status
        code indicates an error (e.g. 404)
    :param bool verify: Whether to verify TLS connection or ignore any errors
        like expired certificate
    :param int,float timeout: Maximum number of seconds the request may take
    :param cookies: Cookies to include in the request (merged with existing
        cookies in the global client session); see :func:`get`

    :return: Response text
    :rtype: Response
    :raise RequestError: if the request fails for any expected reason
    """
    return await _request(
        method='POST',
        url=url,
        headers=headers,
        params=params,
        data=data,
        files=files,
        auth=auth,
        cache=cache,
        max_cache_age=max_cache_age,
        user_agent=user_agent,
        follow_redirects=follow_redirects,
        raise_on_error_status=raise_on_error_status,
        verify=verify,
        timeout=timeout,
        cookies=cookies,
        debug_file=debug_file,
    )

async def download(url, filepath, *args, cache=False, **kwargs):
    """
    Write downloaded data to file

    :param url: Where to download the data from
    :param filepath: Where to save the downloaded data

    Any other arguments are passed to :func:`get`.

    If `filepath` exists, no request is made.

    :raise RequestError: if anything goes wrong
    :return: `filepath`
    """
    if not os.path.exists(filepath) or not cache:
        _log.debug('Downloading %r to %r', url, filepath)
        response = await get(url, *args, cache=False, **kwargs)
        try:
            with open(filepath, 'wb') as f:
                f.write(response.bytes)
        except OSError as e:
            msg = e.strerror if e.strerror else str(e)
            raise errors.RequestError(f'Unable to write {filepath}: {msg}') from e
    else:
        _log.debug('Already downloaded %r to %r', url, filepath)
    return filepath


class Response(str):
    """
    Response to an HTTP request

    This is a subclass of :class:`str` with additional attributes and methods.
    """

    def __new__(cls, text, bytes, url=None, headers=None, status_code=None):
        obj = super().__new__(cls, text)
        obj._bytes = bytes
        obj._url = url
        obj._headers = headers if headers is not None else {}
        obj._status_code = status_code
        return obj

    @property
    def url(self):
        """URL the response came from"""
        return self._url

    @property
    def headers(self):
        """HTTP headers"""
        return self._headers

    @property
    def status_code(self):
        """HTTP status code"""
        return self._status_code

    @property
    def bytes(self):
        """Response data as :class:`bytes`"""
        return self._bytes

    def json(self):
        """
        Parse the response text as JSON

        :raise RequestError: if parsing fails
        """
        try:
            return json.loads(self)
        except ValueError as e:
            if self:
                raise errors.RequestError(f'Malformed JSON: {str(self)!r}: {e}') from e
            else:
                raise errors.RequestError('Malformed JSON: Empty string') from e

    def __repr__(self):
        kwargs = [
            f'text={str(self)!r}',
            f'bytes={self.bytes!r}',
        ]
        if self.headers != {}:
            kwargs.append(f'headers={self.headers!r}')
        if self.status_code is not None:
            kwargs.append(f'status_code={self.status_code!r}')
        return f'{type(self).__name__}({", ".join(kwargs)})'


async def _request(
        method,
        url,
        *,
        headers={},
        params={},
        data={},
        files={},
        auth=None,
        cache=False,
        max_cache_age=float('inf'),
        user_agent=False,
        follow_redirects=True,
        raise_on_error_status=True,
        verify=True,
        timeout=_default_timeout,
        cookies=None,
        debug_file=None,
    ):
    if method.upper() not in ('GET', 'POST'):
        raise ValueError(f'Invalid method: {method}')

    client = httpx.AsyncClient(
        headers={**_default_headers, **headers},
        cookies=_load_permanent_cookies(cookies),
        verify=bool(verify),
    )
    async with client:
        # Create request object
        if isinstance(data, (bytes, str)):
            build_request_args = {'content': data}
        else:
            # Remove fields with a value of `None`
            build_request_args = {'data': _sanitize_request_data_dict(data)}

        request = client.build_request(
            method=str(method),
            url=str(url),
            cookies=_load_session_cookies(httpx.URL(url).host),
            params=params,
            files=_open_files(files),
            timeout=timeout,
            **build_request_args,
        )

        # Block when requesting the same URL multiple times simultaneously so the
        # first response can be loaded from cache by the other requests
        request_lock_key = (request.url, await request.aread())
        # _log.debug('Request lock key: %r', request_lock_key)
        request_lock = _request_locks[request_lock_key]
        async with request_lock:
            # Adjust User-Agent
            if user_agent == 'BROWSER':
                request.headers['User-Agent'] = await get_popular_user_agent()
            elif isinstance(user_agent, str):
                request.headers['User-Agent'] = user_agent
            elif not user_agent:
                del request.headers['User-Agent']

            if cache:
                cache_file = _cache_file(method, url, params, data)
                result = _from_cache(cache_file, max_age=max_cache_age)
                if result is not None:
                    return result

            if debug_file:
                await _dump_req_res(request, f'{debug_file}.request')

            try:
                response = await client.send(
                    request=request,
                    auth=auth,
                    follow_redirects=follow_redirects,
                )
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    if raise_on_error_status and response.status_code not in (301, 302, 303, 307, 308):
                        msg = f'{response.status_code} {response.reason_phrase}'
                        custom_text = utils.html.as_text(response.text)
                        if custom_text:
                            msg = f'{msg}: {custom_text}'
                        raise errors.RequestError(
                            f'{url}: {msg}',
                            url=url,
                            text=response.text,
                            headers=response.headers,
                            status_code=response.status_code,
                        ) from e

            except httpx.TimeoutException as e:
                raise errors.TimeoutError(timeout, resource=url) from e

            except httpx.HTTPError as e:
                msg = str(e)

                # Remove cryptic error number from message.
                msg = re.sub(r'^\[Errno -?\d+\]\s*', r'', msg)

                # For SSL error messages, remove "(_ssl.c:1000)" at the end.
                # Relevant issue:
                # Introduce httpx.SSLError exception: https://github.com/encode/httpx/issues/3350
                msg = re.sub(r'\s*\([a-z0-9_]+\.c:\d+\)$', r'', msg)

                raise errors.RequestError(f'{url}: {msg}') from e

            else:
                _save_session_cookies(cookies=client.cookies, domain=response.url.host)
                if cookies and isinstance(cookies, (str, pathlib.Path)):
                    _save_permanent_cookies(client=client, filepath=cookies, domain=response.url.host)

                if cache:
                    cache_file = _cache_file(method, url, params, data)
                    _to_cache(cache_file, response.content)

                if debug_file:
                    await _dump_req_res(response, f'{debug_file}.response')

                return Response(
                    url=response.url,
                    text=response.text,
                    bytes=response.content,
                    headers=response.headers,
                    status_code=response.status_code,
                )


def _sanitize_request_data_dict(data):
    sanitized = {}
    for key, value in data.items():
        if value is not None:
            if callable(getattr(value, 'get_secret_value', None)):
                # Something like `pydantic.SecretStr` that keeps secrets like API keys and passwords
                # out of log files.
                sanitized[key] = value.get_secret_value()
            else:
                sanitized[key] = value
    return sanitized


async def _dump_req_res(r, filepath):
    content = await r.aread()

    if isinstance(r, httpx.Request):
        _log.debug('Sending request: %r', r)
        _log.debug('Request headers: %r', r.headers)
        _log.debug('Request data: %r', content)
    else:
        _log.debug('Received response: %r', r)
        _log.debug('Response headers: %r', r.headers)
        _log.debug('Response data: %r', content)

    utils.fs.mkdir(os.path.dirname(filepath))
    if isinstance(content, str):
        utils.html.dump(content, f'{filepath}.html')
    elif isinstance(content, bytes):
        with open(f'{filepath}.content', 'wb') as f:
            f.write(content)
    elif isinstance(content, str):
        with open(f'{filepath}.content', 'w') as f:
            f.write(content)
    else:
        raise RuntimeError(f'How should I dump {type(content).__name__}?: {content!r}')

    with open(f'{filepath}.headers', 'w') as f:
        f.write(json.dumps(dict(r.headers), indent=4))


def _load_session_cookies(domain):
    # _log.debug('Loading session cookies for %r: %r', domain, _session_cookies[domain])
    return _session_cookies[domain]


def _save_session_cookies(cookies, domain):
    # `cookies` is dict-like, but it raises `httpx.CookieConflict` if mulitple cookies have the same
    # name. So we iterate over `cookies.jar` (`http.cookiejar.CookieJar` instance), which doesn't
    # have this issue. We assume (1) the more recently set cookie is relevant, and (2) the more
    # recent cookie comes after the old cookie when iterating over `cookies.jar`. This may be wrong
    # but seems to work for now.
    #
    # At the time of writing, this issue was reproducible like this:
    #
    #     $ upsies id tmdb Whatever
    #     [...]
    #     httpx.CookieConflict: Multiple cookies exist with name=AWSALBAPP-0
    #
    _session_cookies[domain].update(
        (cookie.name, cookie.value)
        for cookie in cookies.jar
    )
    _log.debug('Saved session cookies for %r: %r: %r', domain, cookies, _session_cookies[domain])


def clear_session_cookies(domain=None):
    """
    Delete all session cookies for `domain`

    If `domain` is `None`, delete all session cookies.
    """
    if domain:
        _session_cookies[domain].clear()
    else:
        for domain in _session_cookies:
            _session_cookies[domain].clear()


def _load_permanent_cookies(cookies):
    if isinstance(cookies, (collections.abc.Mapping, http.cookiejar.CookieJar)):
        _log.debug('Loading permanent cookies from mapping: %r', cookies)
        return cookies
    elif cookies and isinstance(cookies, (str, pathlib.Path)):
        filepath_abs = os.path.join(_get_cache_directory(), cookies)
        _log.debug('Loading permanent cookies from file: %r', filepath_abs)
        cookie_jar = http.cookiejar.LWPCookieJar(filepath_abs)
        try:
            cookie_jar.load()
        except FileNotFoundError:
            _log.debug('No such file: %r', filepath_abs)
            pass
        except OSError as e:
            msg = e.strerror if e.strerror else str(e)
            raise errors.RequestError(f'Failed to read {cookie_jar.filename}: {msg}') from e
        return cookie_jar
    elif cookies is not None:
        raise RuntimeError(f'Unsupported cookies type: {cookies!r}')


def _save_permanent_cookies(client, filepath, domain):
    filepath_abs = os.path.join(_get_cache_directory(), filepath)
    _log.debug('Saving permanent cookies for %r to %r', domain, filepath_abs)
    file_cookie_jar = http.cookiejar.LWPCookieJar(filepath_abs)
    for cookie in client.cookies.jar:
        if domain.endswith(cookie.domain):
            file_cookie_jar.set_cookie(cookie)

    if file_cookie_jar:
        try:
            utils.fs.mkdir(utils.fs.dirname(filepath_abs))
            file_cookie_jar.save()
        except OSError as e:
            msg = e.strerror if e.strerror else str(e)
            raise errors.RequestError(f'Failed to write {filepath_abs}: {msg}') from e


def _open_files(files):
    """
    Open files for upload

    See :func:`post` and
    https://www.python-httpx.org/advanced/#multipart-file-encoding.

    :raise RequestError: if a file cannot be opened
    """
    opened = {}
    for fieldname, fileinfo in files.items():
        # Field name is mapped to file path
        if isinstance(fileinfo, str):
            filename = os.path.basename(fileinfo)
            fileobj = _get_file_object(fileinfo)
            opened[fieldname] = (filename, fileobj)

        # Field name is mapped to opened file/file-like object/stream
        elif isinstance(fileinfo, io.BytesIO):
            opened[fieldname] = (None, fileinfo)

        # Field name is mapped to dictionary with the keys "file", "filename"
        # and "mimetype".
        # - "file" can be a path or file-like object (like above)
        # - "filename" is the name of the file that is passed to the server or
        #   `None`.
        # - "mimetype" is the MIME type, which is autodetected unless "filename"
        #   is `None`.
        elif isinstance(fileinfo, collections.abc.Mapping):
            if isinstance(fileinfo['file'], str):
                filename = fileinfo.get('filename', os.path.basename(fileinfo['file']))
                fileobj = _get_file_object(fileinfo['file'])
            elif isinstance(fileinfo['file'], io.BytesIO):
                filename = fileinfo.get('filename', None)
                fileobj = fileinfo['file']
            else:
                raise RuntimeError(f'Invalid "file" value in fileinfo: {fileinfo["file"]!r}')
            mimetype = fileinfo.get('mimetype', False)
            if mimetype is False:
                opened[fieldname] = (filename, fileobj)
            else:
                opened[fieldname] = (filename, fileobj, mimetype)

        else:
            raise RuntimeError(f'Invalid fileinfo: {fileinfo}')

    return opened

def _get_file_object(filepath):
    """
    Open `filepath` and return the file object

    :raise RequestError: if OSError is raised by `open`
    """
    try:
        return open(filepath, 'rb')
    except OSError as e:
        msg = e.strerror if e.strerror else 'Failed to open'
        raise errors.RequestError(f'{filepath}: {msg}') from e


def _to_cache(cache_file, bytes):
    if not isinstance(bytes, builtins.bytes):
        raise TypeError(f'Not a bytes object: {bytes!r}')

    # Try to remove <script> tags
    if b'<script' in bytes:
        try:
            string = str(bytes, encoding='utf-8', errors='strict')
        except UnicodeDecodeError:
            pass
        else:
            # This is disabled for now because ImdbApi uses a JSON object that
            # is are stored inside a <script></script> tag.
            string = utils.html.purge_tags(string)
            bytes = string.encode('utf-8')

    try:
        utils.fs.mkdir(utils.fs.dirname(cache_file))
        with open(cache_file, 'wb') as f:
            f.write(bytes)
    except OSError as e:
        raise RuntimeError(f'Unable to write cache file {cache_file}: {e}') from e


def _from_cache(cache_file, max_age=float('inf')):
    try:
        cache_mtime = os.stat(cache_file).st_mtime
    except FileNotFoundError:
        return None
    else:
        cache_age = time.time() - cache_mtime
        if cache_age <= max_age:
            bytes = _read_bytes_from_file(cache_file)
            text = _read_string_from_file(cache_file)
            if bytes and text:
                return Response(text=text, bytes=bytes)


def _read_string_from_file(filepath):
    bytes = _read_bytes_from_file(filepath)
    if bytes:
        return str(bytes, encoding='utf-8', errors='replace')


def _read_bytes_from_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            return f.read()
    except OSError:
        pass


def _cache_file(method, url, params, data):

    def make_filename(method, url, params_and_data_str):
        if params_and_data_str:
            filename = f'{method.upper()}.{url}?{params_and_data_str}'
        else:
            filename = f'{method.upper()}.{url}'
        return filename.replace(' ', '+')

    def data_as_string(data):
        if isinstance(data, str):
            return data
        elif isinstance(data, bytes):
            return utils.semantic_hash(data)
        elif isinstance(data, dict):
            return '&'.join(f'{k2}={v2}' for k2, v2 in {
                k1: data_as_string(v1)
                for k1, v1 in data.items()
            }.items())
        else:
            raise TypeError(f'Unsupported data type: {type(data).__name__}: {data!r}')

    params_str = '&'.join((f'{k}={v}' for k,v in params.items()))
    data_str = data_as_string(data)
    params_and_data_str = '.'.join(x for x in (params_str, data_str) if x)

    # If the payload is too long, hash it.
    if len(make_filename(method, url, params_and_data_str)) > 250:
        params_and_data_str = utils.semantic_hash(params_and_data_str)

    # If the file name is still too long, also hash the URL.
    if len(make_filename(method, url, params_and_data_str)) > 250:
        url = utils.semantic_hash(url)

    return os.path.join(
        _get_cache_directory(),
        utils.fs.sanitize_filename(make_filename(method, url, params_and_data_str)),
    )


DEFAULT_USER_AGENT = 'Mozilla/5.0 (X11; Linux) Gecko/20100101 Firefox'
USER_AGENT_CACHE_MAX_AGE = 14 * 24 * 60 * 60
USER_AGENT_SOURCE_URLS = [
    'https://www.whatismybrowser.com/guides/the-latest-user-agent/firefox',
]

async def get_popular_user_agent():
    """
    Return commonly used user agent

    The most recent user agent is cached for `USER_AGENT_CACHE_MAX_AGE` seconds.

    If no user agent can be acquired, return `DEFAULT_USER_AGENT`.
    """
    user_agent = _get_user_agent_from_cache()
    if user_agent:
        return user_agent

    for url in USER_AGENT_SOURCE_URLS:
        user_agent = await _get_user_agent_from_url(url)
        if user_agent:
            _log.debug('Got fresh user agent: %r', user_agent)
            _cache_user_agent(user_agent)
            return user_agent

    _log.debug('Defaulting to hardcoded user agent: %s', DEFAULT_USER_AGENT)
    return DEFAULT_USER_AGENT

def _get_user_agent_from_cache():
    cache_filepath = _get_user_agent_cache_filepath()
    if os.path.exists(cache_filepath):
        cache_created = os.stat(cache_filepath).st_mtime
        cache_age = time.time() - cache_created
        if cache_age < USER_AGENT_CACHE_MAX_AGE:
            try:
                return open(cache_filepath, 'r').read().strip()
            except OSError as e:
                _log.debug('Failed to read user agent from %s: %r', cache_filepath, e)

async def _get_user_agent_from_url(url):
    try:
        response = await get(url, cache=False, user_agent=False)
    except errors.RequestError as e:
        _log.debug('Failed to fetch user agent from %s: %r', url, e)
    else:
        user_agents = re.findall(
            r'>\s*(Mozilla/5\.0\s*.*?Linux.*?\s*Gecko/\d+\s*.*\s*Firefox/[\d\.]+)\s*<',
            response,
        )
        if user_agents:
            _log.debug('Got user agents from %s:', url)
            for ua in user_agents:
                _log.debug(' * %r', ua)
            return random.choice(user_agents)

def _cache_user_agent(user_agent):
    cache_filepath = _get_user_agent_cache_filepath()
    try:
        with open(cache_filepath, 'w') as f:
            f.write(user_agent)
    except OSError as e:
        _log.debug('Failed to write user agent to %s: %r', cache_filepath, e)

def _get_user_agent_cache_filepath():
    return os.path.join(_get_cache_directory(), 'user-agent')
