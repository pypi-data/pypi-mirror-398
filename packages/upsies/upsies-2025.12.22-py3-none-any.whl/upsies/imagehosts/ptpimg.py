"""
Image uploader for ptpimg.me
"""

from .. import __project_name__, constants, errors, utils
from . import base

import logging  # isort:skip
_log = logging.getLogger(__name__)


class PtpimgImagehostConfig(base.ImagehostConfigBase):
    """User configuration for :class:`PtpimgImagehost`"""

    base_url: utils.config.fields.string(
        default='https://ptpimg.me',
        description='Base URL of the API.',
    )
    apikey: utils.config.fields.string(
        secret=True,
        default='',
        description=(
            'API access key. '
            'Run ``{__project_name__} ui ptpimg -h`` '
            'for instructions on how to get an API key.'
        ),
    )


class PtpimgImagehost(base.ImagehostBase):
    """Upload images to ptpimg.me"""

    name = 'ptpimg'

    Config = PtpimgImagehostConfig

    description = (
        'You need an API key to upload images.\n'
        '\n'
        '  1. Create an account: https://ptpimg.me/register.php\n'
        f'  2. Store your API key in {utils.fs.tildify_path(constants.IMGHOSTS_FILEPATH)}:\n'
        '\n'
        f'       $ {__project_name__} set --fetch-ptpimg-apikey EMAIL PASSWORD\n'
        '\n'
        '     If you already have your API key, store it like this:\n'
        '\n'
        f'       $ {__project_name__} set imghosts.ptpimg.apikey YOUR_API_KEY'
    )

    async def _upload_image(self, image_path):
        response = await utils.http.post(
            url=f'{self.config["base_url"]}/upload.php',
            cache=False,
            headers={
                'referer': f'{self.config["base_url"]}/index.php',
            },
            data={
                'api_key': self.config['apikey'],
            },
            files={
                'file-upload[0]': image_path,
            },
        )
        _log.debug('%s: Response: %r', self.name, response)
        images = response.json()

        try:
            code = images[0]['code']
            ext = images[0]['ext']
            assert code and ext, (code, ext)
        except (IndexError, KeyError, TypeError, AssertionError) as e:
            raise RuntimeError(f'Unexpected response: {images}') from e
        else:
            image_url = f'{self.config["base_url"]}/{code}.{ext}'
            return image_url

    async def get_apikey(self, email, password):
        """
        Get API key from website

        :param str email: Email address to use for login
        :param str password: Password to use for login

        :raises RequestError: if getting the HTML fails for some reason

        :return: API key
        """
        _log.debug('Getting API key for %r', email)
        response = await utils.http.post(
            url=f'{self.config["base_url"]}/login.php',
            cache=False,
            data={
                'email': email,
                'pass': password,
                'login': '',
            },
        )

        try:
            soup = utils.html.parse(response)
            _log.debug('%s: %s', self.name, soup.prettify())

            # Find API key
            input_tag = soup.find('input', id='api_key')
            if input_tag:
                return input_tag['value']

            # Find error message
            error_tag = soup.find(class_='panel-body')
            if error_tag:
                raise errors.RequestError(''.join(error_tag.strings).strip())

            # Default exception
            raise RuntimeError('Failed to find API key')
        finally:
            await utils.http.get(f'{self.config["base_url"]}/logout.php')
