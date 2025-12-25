"""
Base class for image uploaders
"""

import abc
import glob
import hashlib
import os

from .. import __project_name__, constants, errors, utils
from . import common

import logging  # isort:skip
_log = logging.getLogger(__name__)


class ImagehostConfigBase(utils.config.SubsectionBase):
    """
    Base class for image host configurations

    User configuration for an image host, for example for API keys.
    """

    thumb_width: utils.config.fields.integer(
        default=0,
        min=0,
        description=(
            'Thumbnail width in pixels or 0 for no thumbnail.\n'
            'Trackers may ignore this option and use a hardcoded thumbnail width.'
        ),
    )


class ImagehostBase(abc.ABC):
    """
    Base class for image uploaders

    :param config: Instance of :attr:`~.Config` or dictionary with keyword argument for that class
    :param str cache_directory: Where to cache URLs; defaults to
        :attr:`~upsies.constants.DEFAULT_CACHE_DIRECTORY`
    """

    supported_mime_types = ('image/png', 'image/jpeg')
    """Sequence of MIME types that are supported by the hosting service"""

    @property
    @abc.abstractmethod
    def name(self):
        """Name of the image hosting service"""

    @property
    @abc.abstractmethod
    def Config(self):
        """Subclass of :class:`~.ImagehostConfigBase`"""

    def __init__(self, config, cache_directory=None):
        if isinstance(config, self.Config):
            self._config = config
        else:
            self._config = self.Config(**config)
        self._cache_directory = cache_directory if cache_directory else constants.DEFAULT_CACHE_DIRECTORY

    @property
    def cache_directory(self):
        """Path to directory where upload info is cached"""
        return self._cache_directory

    @cache_directory.setter
    def cache_directory(self, directory):
        self._cache_directory = directory

    @property
    def config(self):
        """:class:`~.ImagehostConfigBase` instance provided during instantiation"""
        return self._config

    cli_arguments = {}
    """CLI argument definitions (see :attr:`.CommandBase.cli_arguments`)"""

    description = ''
    """Any documentation, for example how to get an API key"""

    async def upload(self, image_path, *, thumb_width=None, cache=True):
        """
        Upload image file

        :param image_path: Path to image file
        :param int thumb_width: Override ``thumb_width`` in :attr:`config`

            If set to 0, no thumbnail is uploaded.
        :param bool cache: Whether to attempt to get the image URL from cache

        :raise RequestError: if the upload fails

        :return: :class:`~.imagehost.common.UploadedImage`
        """
        if 'apikey' in self.config and not self.config['apikey']:
            raise errors.RequestError(
                'You must configure an API key first. Run '
                f'"{__project_name__} upload-images {self.name} --help" '
                'for more information.'
            )

        # Upload fullsize image.
        info = {
            'url': await self._get_image_url(image_path, cache=cache),
        }

        # Get thumbnail via argument, if specified, or from config file.
        if thumb_width is None:
            thumb_width = self.config['thumb_width']
        if thumb_width:
            # Create thumbnail.
            try:
                thumbnail_path = utils.image.resize(
                    image_path,
                    width=thumb_width,
                    target_directory=self.cache_directory,
                    overwrite=not cache,
                )
            except errors.ImageResizeError as e:
                raise errors.RequestError(e) from e
            else:
                # Upload thumbnail.
                info['thumbnail_url'] = await self._get_image_url(thumbnail_path, cache=cache)

        return common.UploadedImage(**info)

    async def _get_image_url(self, image_path, *, cache=True):
        url = self._get_url_from_cache(image_path) if cache else None
        if not url:
            try:
                converted_image_path = self._get_proper_image(image_path)
            except errors.ImageConvertError as e:
                raise errors.RequestError(e) from e
            else:
                _log.debug('Uploading image: %r', converted_image_path)
                url = await self._upload_image(converted_image_path)
                _log.debug('Uploaded image: %r: %r', converted_image_path, url)
                self._store_url_to_cache(image_path, url)
        return url

    def _get_proper_image(self, image_path):
        # Convert `image_path` to png if it is in an unsupported format.
        # Raise exception if format cannot be determined.
        mime_type = utils.image.get_mime_type(image_path)
        _log.debug('MIME type of %r: %r', image_path, mime_type)
        if not mime_type:
            raise errors.ImageConvertError(f'Unknown file type: {image_path}')
        elif mime_type not in self.supported_mime_types:
            filename_suffix = f'.{self._get_cache_file_id(image_path)}.png'
            max_filename_length = 250 - len(filename_suffix)
            filename = utils.fs.basename(image_path)[-max_filename_length:] + filename_suffix
            mime_type = 'image/png'
            output_file = os.path.join(self.cache_directory, filename)
            _log.debug('Converted to %r: %r', mime_type, output_file)
            return utils.image.convert(image_path, mime_type=mime_type, output_file=output_file)
        else:
            return image_path

    @abc.abstractmethod
    async def _upload_image(self, image_path):
        """Upload `image_path` and return URL to the image file"""

    def _get_url_from_cache(self, image_path):
        cache_file_suffix = self._get_cache_file_suffix(image_path)
        cache_file_glob = os.path.join(
            glob.escape(self.cache_directory),
            f'*.{cache_file_suffix}',
        )
        matching_cache_files = glob.glob(cache_file_glob)

        if matching_cache_files:
            cache_file = matching_cache_files[0]
            try:
                with open(cache_file, 'r') as f:
                    url = f.read().strip()
            except OSError as e:
                # Unreadable cache file. We'll try to overwrite it later.
                _log.debug('Failed to read %r: %r', cache_file, e)
            else:
                _log.debug('Got URL for %r from cache: %s: %s', image_path, cache_file, url)
                return url

    def _store_url_to_cache(self, image_path, url):
        # Prepend file name to unique ID for easier debugging. Max file name length is usually 255
        # bytes.
        cache_file_suffix = self._get_cache_file_suffix(image_path)
        max_filename_length = 250 - len(cache_file_suffix)
        filename = f'{utils.fs.basename(image_path)}.{cache_file_suffix}'
        cache_file = os.path.join(self.cache_directory, filename[-max_filename_length:])

        try:
            utils.fs.mkdir(utils.fs.dirname(cache_file))
            with open(cache_file, 'w') as f:
                f.write(url)
        except (OSError, errors.ContentError) as e:
            msg = e.strerror if getattr(e, 'strerror', None) else e
            raise RuntimeError(f'Unable to write cache {cache_file}: {msg}') from e

    def _get_cache_file_suffix(self, image_path):
        unique_id = self._get_cache_file_id(image_path)
        return f'{unique_id}.{self.name}.url'

    def _get_cache_file_id(self, image_path):
        try:
            # Generate unique ID from the first 10 KiB of image data.
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read(10 * 1024)).hexdigest()
        except OSError:
            # If `image_path` is not readable, get unique ID from file path.
            return hashlib.md5(image_path.encode('utf8')).hexdigest()
