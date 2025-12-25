"""
Image uploader for imgbox.com
"""

from .. import errors, utils
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)

pyimgbox = utils.LazyModule(module='pyimgbox', namespace=globals())


class ImgboxImagehostConfig(base.ImagehostConfigBase):
    """User configuration for :class:`ImgboxImagehost`"""


class ImgboxImagehost(base.ImagehostBase):
    """Upload images to a gallery on imgbox.com"""

    name = 'imgbox'

    Config = ImgboxImagehostConfig

    async def _upload_image(self, image_path):
        gallery = pyimgbox.Gallery(
            thumb_width=0,
            square_thumbs=False,
            comments_enabled=False,
        )
        try:
            submission = await gallery.upload(image_path)
            _log.debug('%s: Response: %r', self.name, submission)
            if not submission.success:
                raise errors.RequestError(submission.error)
            else:
                return submission.image_url
        finally:
            await gallery.close()
