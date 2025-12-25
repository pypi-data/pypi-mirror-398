"""
Upload images to image hosting services
"""

from .. import errors, utils
from .. import imagehosts as imagehosts_module
from . import JobBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class ImagehostJob(JobBase):
    """Upload images to an image hosting service"""

    name = 'imghost'
    label = 'Image URLs'

    # Don't cache output and rely on caching in ImagehostBase. Otherwise, a
    # single failed/cancelled upload would throw away all the gathered URLs
    # because nothing is cached if a job fails.
    cache_id = None

    def initialize(self, *, imagehosts, image_paths=()):
        """
        Validate arguments and set internal state

        :param imagehosts: Sequence of :class:`ImagehostBase` subclass instances (see
            :func:`.imagehosts.imagehost`)

        :param image_paths: Sequence of image paths to upload

        First, `image_paths` are uploaded. If a Job named "screenshots" exists in
        :attr:`~.JobBase.siblings`, screenshots from that job are uploaded as well.
        """
        for imagehost in imagehosts:
            assert isinstance(imagehost, imagehosts_module.ImagehostBase), f'Not an ImagehostBase: {imagehost!r}'
            # Force image hosts to cache image URLs in our cache directory
            imagehost.cache_directory = self.cache_directory

        self._image_paths = tuple(image_paths)
        self._imagehosts = list(imagehosts)
        self._uploaded_images = []
        self._urls_by_file = {}
        self.images_total = len(self._image_paths)

    async def run(self):
        for image_path in self._image_paths:
            await self._upload_to_one_or_any(image_path)

        if 'screenshots' in self.siblings:
            screenshots_total, = await self.receive_one('screenshots', 'screenshots_total', only_posargs=True)
            self.set_images_total(screenshots_total)
            async for screenshot_path, in self.receive_all('screenshots', 'output', only_posargs=True):
                await self._upload_to_one_or_any(screenshot_path)

    async def _upload_to_one_or_any(self, image_path):
        if len(self._imagehosts) <= 1:
            await self._upload_to_one(image_path)
        else:
            await self._upload_to_any(image_path)

    async def _upload_to_one(self, image_path):
        # Upload to 1 or 0 image hosts and error out immediately if that fails.
        for imagehost in self._imagehosts:
            try:
                await self._upload(image_path, imagehost)
            except errors.RequestError as e:
                self.error(f'{imagehost.name}: Upload failed: {utils.fs.basename(image_path)}: {e}')

    async def _upload_to_any(self, image_path):
        # Try each image host and stop on first successful upload.
        # Only warn about upload failures.
        fail = False
        for imagehost in tuple(self._imagehosts):
            try:
                await self._upload(image_path, imagehost)
            except errors.RequestError as e:
                _log.debug('Failed to upload %s to %s: %r', image_path, imagehost.name, e)
                self.warn(f'{imagehost.name}: Upload failed: {utils.fs.basename(image_path)}: {e}')
                fail = True
                # Do not attempt to upload to this service again.
                self._imagehosts.remove(imagehost)
            else:
                fail = False
                break
        if fail:
            self.error('All upload attempts failed.')

    async def _upload(self, image_path, imagehost):
        info = await imagehost.upload(image_path, cache=not self.ignore_cache)
        _log.debug('Uploaded image: %r', info)
        self._uploaded_images.append(info)
        self._urls_by_file[image_path] = info
        image_url = str(info)
        self.add_output(image_url)

    @property
    def exit_code(self):
        """`0` if all images were uploaded, `1` otherwise, `None` if unfinished"""
        if self.is_finished:
            if self.images_uploaded > 0 and self.images_uploaded == self.images_total:
                return 0
            else:
                return 1

    @property
    def uploaded_images(self):
        """
        Sequence of :class:`~.imagehosts.common.UploadedImage` objects

        Use this property to get additional information like thumbnail URLs that
        are not part of this job's :attr:`~.base.JobBase.output`.
        """
        return tuple(self._uploaded_images)

    @property
    def urls_by_file(self):
        """Map of image file paths to :class:`~.imagehost.common.UploadedImage` instances"""
        return self._urls_by_file.copy()

    @property
    def images_uploaded(self):
        """Number of uploaded images"""
        return len(self._uploaded_images)

    @property
    def images_total(self):
        """Expected number of images to upload"""
        return self._images_total

    @images_total.setter
    def images_total(self, value):
        self._images_total = int(value)

    def set_images_total(self, value):
        """:attr:`images_total` setter as a method"""
        self.images_total = value
