"""
Concrete :class:`~.TrackerConfigBase` subclass for NBL
"""

import base64

from ... import utils
from .. import base

import logging  # isort:skip
_log = logging.getLogger(__name__)


class NblTrackerConfig(base.TrackerConfigBase):
    upload_url: base.config.upload_url(
        base64.b64decode('aHR0cHM6Ly9uZWJ1bGFuY2UuaW8vdXBsb2FkLnBocA==').decode('ascii'),
    )

    apikey: base.config.apikey(
        default='',
        instructions='Create one on the website: <USERNAME> -> Settings -> API keys (check "Upload")',
    )

    announce_url: base.config.announce_url(
        default='',
        instructions='Get it from the website: Shows -> Upload -> Your personal announce URL',
    )

    exclude: base.config.exclude(
        base.exclude_regexes.garbage,
    )

    anonymous: base.config.anonymous('no')


cli_arguments = {
    'submit': {
        ('--anonymous', '--an'): {
            'help': (
                'Hide your username for this submission\n'
                'Valid BOOL values: ' + ', '.join(
                    f'{t}/{f}'
                    for t, f in zip(utils.types.Bool.truthy, utils.types.Bool.falsy)
                )
            ),
            'type': utils.argtypes.bool_or_none,
            'metavar': 'BOOL',
        },
        ('--tvmaze', '--tv'): {
            'help': 'TVmaze ID or URL',
            'type': utils.argtypes.webdb_id('tvmaze'),
        },
    },
}
