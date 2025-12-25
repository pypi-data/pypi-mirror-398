"""
Find, download and re-upload poster for movie, series or season
"""

import collections
import hashlib
import os
import re
import urllib.parse

import async_lru

from .. import errors, uis, utils
from . import JobBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class PosterJob(JobBase):
    """
    Get poster and optionally resize and reupload it

    This job adds the following signals to :attr:`~.JobBase.signal`:

        ``obtaining``
            Emitted when getting a poster is attempted. Registered callbacks get no arguments.

        ``obtained``
            Emitted when a poster was successfully obtained. Registered callbacks get the poster
            file path or URL as a positional argument.

        ``downloading``
            Emitted when downloading a poster is attempted. Registered callbacks get the poster URL
            as a positional argument.

        ``downloaded``
            Emitted when a poster was successfully downloaded. Registered callbacks get the poster
            URL as a positional argument.

        ``resizing``
            Emitted when resizing a poster is attempted. Registered callbacks get the original
            poster file path as a positional argument.

        ``resized``
            Emitted when a poster was successfully resized. Registered callbacks get the resized
            poster file path as a positional argument.

        ``uploading``
            Emitted when uploading a poster to an image hosting service is attempted. Registered
            callbacks get the relevant :class:`~.ImagehostBase` subclass as a positional argument.

        ``uploaded``
            Emitted when a poster was successfully uploaded to an image hosting service. Registered
            callbacks get the URL of the uploaded poster as a positional argument.
    """

    name = 'poster'
    label = 'Poster'

    # Caching is done by utilities.
    cache_id = None

    def initialize(self, *, getter, width=None, height=None, write_to=None, imagehosts=()):
        """
        Set internal state

        :param getter: Coroutine function that returns a poster file or poster URL
            (e.g. :meth:`.WebDbApiBase.poster_url`). May raise :class:`~.RequestError`, which is
            passed to :meth:`~.JobBase.error`.

        :param width: Resize poster to this many pixels wide (aspect ratio is maintained)

        :param height: Resize poster to this many pixels high (aspect ratio is maintained)

        :param imagehosts: Sequence of :class:`~.ImagehostBase` subclass instances

            Upload poster to the first, try the next one if it fails and so on.
            :class:`~.RequestError` from uploading is passed to :meth:`~.JobBase.warn`. If all
            uploads fail, :meth:`error` is called. Any failed image host is considered broken and
            will not be used for subsequent images.

        :param write_to: Write poster to this file path (may be `None` or empty string)
        """
        self._getter = getter
        self._width = width
        self._height = height
        self._write_to = write_to
        self._imagehosts = imagehosts

        self.signal.add('obtaining')
        self.signal.add('obtained')
        self.signal.add('downloading')
        self.signal.add('downloaded')
        self.signal.add('resizing')
        self.signal.add('resized')
        self.signal.add('uploading')
        self.signal.add('uploaded')

    _url_regex = re.compile(r'^https?://.+', flags=re.IGNORECASE)

    class _ProcessingError(errors.UpsiesError):
        pass

    async def run(self):
        try:
            params = await self._obtain()
            poster = params['poster']
            width = params.get('width', self._width)
            height = params.get('height', self._height)
            write_to = params.get('write_to', self._write_to)
            imagehosts = params.get('imagehosts', self._imagehosts)

            poster = await self._resize(poster, width, height)
            await self._write(poster, write_to)
            await self._upload(poster, imagehosts)

            if not write_to and not imagehosts:
                if width or height:
                    await self._write(poster, self._get_poster_filename(poster))
                else:
                    self.add_output(poster)

        except self._ProcessingError as e:
            self.error(e)

    async def _obtain(self):
        _log.debug('Obtaining poster: %r', self._getter)
        self.signal.emit('obtaining')
        try:
            params_or_poster = await self._getter()
        except errors.RequestError as e:
            self.warn(f'Failed to get poster: {e}')
            params_or_poster = None

        _log.debug('Obtained poster: %r', params_or_poster)
        if not params_or_poster:
            params = await self._obtain_via_prompt()

        elif isinstance(params_or_poster, collections.abc.Mapping):
            params = params_or_poster

        else:
            params = {'poster': params_or_poster}

        self.signal.emit('obtained', params['poster'])
        return params

    async def _obtain_via_prompt(self):
        self.info = 'Please enter a poster file or URL.'
        try:
            poster = ''
            while True:
                poster = os.path.expanduser(await self.add_prompt(
                    uis.prompts.TextPrompt(text=poster)
                ))
                if not poster:
                    self.warn('Poster file or URL is required.')

                elif self._url_regex.search(poster):
                    # Download poster just to get an error if it fails. Later
                    # downloads should grab it from cache without pestering the
                    # server.
                    try:
                        await utils.http.get(poster, cache=True)
                    except errors.RequestError as e:
                        self.warn(f'Failed to download poster: {e}')
                    else:
                        return {'poster': poster}

                elif not os.path.exists(poster):
                    self.warn(f'Poster file does not exist: {poster}')

                elif not os.path.isfile(poster):
                    self.warn(f'Poster is not a file: {poster}')

                else:
                    return {'poster': poster}
        finally:
            self.clear_warnings()

    async def _resize(self, poster, width, height):
        if width or height:
            _log.debug('Resizing poster to %s x %s: %r', width, height, poster)

            # Download the poster so we can resize it.
            filepath = await self._get_poster_filepath(poster)
            filename_resized = '.'.join((
                utils.fs.basename(utils.fs.strip_extension(filepath)),
                f'{width}x{height}',
                utils.fs.file_extension(filepath),
            ))

            self.signal.emit('resizing', filepath)
            try:
                filepath_resized = utils.image.resize(
                    filepath,
                    target_directory=self.cache_directory,
                    target_filename=filename_resized,
                    width=width,
                    height=height,
                )
            except errors.ImageResizeError as e:
                raise self._ProcessingError(f'Failed to resize poster: {e}') from e
            else:
                self.signal.emit('resized', filepath_resized)
                return filepath_resized
        else:
            # Return original poster file or URL.
            return poster

    async def _write(self, poster, filepath):
        if filepath:
            # Write poster file or URL to user-provided path.
            _log.debug('Writing poster: %r', (poster, filepath))
            data = await self._read_file_or_url(poster)
            filepath = await self._write_file(data, filepath)
            self.add_output(filepath)

    async def _upload(self, poster, imagehosts):
        if imagehosts:
            # If poster is a URL, we must download it first.
            filepath = await self._get_poster_filepath(poster)

            # Upload `filepath` to any `imagehost` and return the URL of the first successful
            # upload.
            for imagehost in imagehosts:
                _log.debug('Uploading poster: %r', (filepath, imagehost.name))
                self.signal.emit('uploading', imagehost)
                try:
                    url = await imagehost.upload(filepath, thumb_width=0)
                except errors.RequestError as e:
                    self.warn(f'Failed to upload poster: {e}')
                else:
                    self.signal.emit('uploaded', url)
                    self.add_output(url)
                    return

            # If all upload() calls failed, add an error to all the warnings.
            raise self._ProcessingError('All uploads failed')

    @async_lru.alru_cache
    async def _get_poster_filepath(self, poster):
        if self._url_regex.search(poster):
            # Download poster URL to temporary file and return its path.
            data = await self._read_file_or_url(poster)
            filepath = os.path.join(
                self.cache_directory,
                self._get_poster_filename(poster),
            )
            return await self._write_file(data, filepath)

        else:
            # Return original poster file path.
            return poster

    def _get_poster_filename(self, poster):
        if self._url_regex.search(poster):
            # Turn poster URL into unique file name.
            url = urllib.parse.urlparse(poster)
            unique_id = hashlib.md5(
                '.'.join((url.path, url.query))
                .encode('utf8')
            ).hexdigest()
            filename = 'poster:' + '.'.join((
                url.hostname,
                unique_id,
            ))
            extension = utils.fs.file_extension(url.path)
            if extension:
                filename += f'.{extension}'
            return filename
        else:
            # Get poster file name from poster file path.
            return utils.fs.basename(poster)

    async def _read_file_or_url(self, poster):
        if self._url_regex.search(poster):
            # Return downloaded data from URL.
            _log.debug('Downloading poster: %r', poster)
            try:
                self.signal.emit('downloading', poster)
                response = await utils.http.get(poster, cache=True)
            except errors.RequestError as e:
                raise self._ProcessingError(f'Failed to download poster: {e}') from e
            else:
                self.signal.emit('downloaded', poster)
                return response.bytes

        else:
            # Return poster file content.
            _log.debug('Reading poster: %r', poster)
            try:
                with open(poster, 'rb') as f:
                    return f.read()
            except OSError as e:
                msg = e.strerror if e.strerror else str(e)
                raise self._ProcessingError(f'Failed to read poster: {msg}') from e

    async def _write_file(self, data, filepath):
        # Write `data` to sanitized `filepath` and return sanitized `filepath`.
        filepath = utils.fs.sanitize_path(filepath)
        try:
            with open(filepath, 'wb') as f:
                f.write(data)
        except OSError as e:
            msg = e.strerror if e.strerror else str(e)
            raise self._ProcessingError(f'Failed to write {filepath}: {msg}') from e
        else:
            return filepath
