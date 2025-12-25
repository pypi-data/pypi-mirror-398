"""
Image uploader for freeimage.host
"""

import json

from .. import errors, utils
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)


class FreeimageImagehostConfig(base.ImagehostConfigBase):
    """User configuration for :class:`FreeimageImagehost`"""

    base_url: utils.config.fields.string(
        default='https://freeimage.host',
        description='Base URL of the API.',
    )
    apikey: utils.config.fields.string(
        secret=True,
        default='6d207e02198a847aa98d0a2a901485a5',
        description=(
            'API access key. '
            'The default value is the public API key from https://freeimage.host/page/api.'
        ),
    )


class FreeimageImagehost(base.ImagehostBase):
    """Upload images to freeimage.host"""

    name = 'freeimage'

    Config = FreeimageImagehostConfig

    async def _upload_image(self, image_path):
        try:
            response = await utils.http.post(
                url=self.config['base_url'] + '/api/1/upload',
                cache=False,
                data={
                    'key': self.config['apikey'],
                    'action': 'upload',
                    'format': 'json',
                },
                files={
                    'source': image_path,
                },
            )
        except errors.RequestError as e:
            # Error response is undocumented. I looks like this:
            # {
            #   "status_code": 400,
            #   "error": {
            #     "message": "Can't get target upload source info",
            #     "code": 310,
            #     "context": "CHV\\UploadException"
            #   },
            #   "status_txt": "Bad Request"
            # }
            try:
                info = json.loads(e.text)
                raise errors.RequestError(f'{info["status_txt"]}: {info["error"]["message"]}')
            except (TypeError, ValueError, KeyError):
                if e.text:
                    raise errors.RequestError(f'Upload failed: {e.text}') from e
                else:
                    raise errors.RequestError(f'Upload failed: {e}') from e

        _log.debug('%s: Response: %r', self.name, response)
        info = response.json()
        try:
            return info['image']['image']['url']
        except KeyError as e:
            raise RuntimeError(f'Unexpected response: {response}') from e
