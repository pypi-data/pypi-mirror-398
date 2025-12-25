"""
Dummy image uploader for testing and debugging
"""

import asyncio
import os

from .. import errors, utils
from . import base

if utils.is_running_in_development_environment():

    class DummyImagehostConfig(base.ImagehostConfigBase):
        hostname: utils.config.fields.string(
            default='localhost',
            description='Host name in dummy image URLs.',
        )

    class DummyImagehost(base.ImagehostBase):
        """Dummy service for testing and debugging"""

        name = 'dummy'

        Config = DummyImagehostConfig

        description = (
            'This is a fake image hosting service '
            'that is used for testing and debugging.'
        )

        cli_arguments = {
            ('--hostname', '-n'): {
                'help': 'Host name in the dummy URL',
            },
        }

        async def _upload_image(self, image_path):
            try:
                utils.fs.assert_file_readable(image_path)
            except errors.ContentError as e:
                raise errors.RequestError(e) from e
            else:
                await asyncio.sleep(0.6)
                url = f'http://{self.config["hostname"]}/{os.path.basename(image_path)}'
                return url
