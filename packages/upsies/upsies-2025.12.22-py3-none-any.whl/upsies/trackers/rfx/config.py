"""
Concrete :class:`~.TrackerConfigBase` subclass for RFX
"""

import base64

from ... import utils
from .. import base

RfxImagehost = utils.types.Imagehost(
    disallowed=(
        ()
        if utils.is_running_in_development_environment() else
        ('dummy',)
    ),
)


class RfxTrackerConfig(base.TrackerConfigBase):
    upload_url: base.config.upload_url(
        default=base64.b64decode('aHR0cHM6Ly9yZWVsZmxpeC5jYy9hcGkvdG9ycmVudHMvdXBsb2Fk').decode('ascii'),
    )

    announce_url: utils.config.fields.string(
        default=base64.b64decode('aHR0cHM6Ly9yZWVsZmxpeC5jYy9hbm5vdW5jZQ==').decode('ascii'),
        description='Announce URL without the private key.',
    )

    announce_passkey: utils.config.fields.string(
        default='',
        description=(
            'The private part of the announce URL.\n'
            'Get it from the website: Settings -> Passkey'
        ),
        secret=True,
    )

    apikey: base.config.apikey('')

    anonymous: base.config.anonymous('no')

    image_host: base.config.image_host(RfxImagehost, default=('imgbox', 'freeimage'))

    screenshots_count: base.config.screenshots_count(3, min=3, max=10)

    exclude: base.config.exclude(
        base.exclude_regexes.garbage,
    )


cli_arguments = {
    'submit': {
        ('--imdb', '--im'): {
            'help': 'IMDb ID or URL',
            'type': utils.argtypes.webdb_id('imdb'),
        },
        ('--tmdb', '--tm'): {
            'help': 'TMDb ID or URL',
            'type': utils.argtypes.webdb_id('tmdb'),
        },
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
        ('--screenshots-count', '--ssc'): {
            'help': ('How many screenshots to make '
                     f'(min={RfxTrackerConfig.defaults["screenshots_count"].min}, '
                     f'max={RfxTrackerConfig.defaults["screenshots_count"].max})'),
            'type': utils.argtypes.make_integer(
                min=RfxTrackerConfig.defaults['screenshots_count'].min,
                max=RfxTrackerConfig.defaults['screenshots_count'].max,
            ),
        },
        ('--screenshots', '--ss'): {
            'help': (
                'Path(s) to existing screenshot file(s)\n'
                'Directories are searched recursively.\n'
                'More screenshots are created if necessary.'
            ),
            'nargs': '+',
            'action': 'extend',
            'type': utils.argtypes.files_with_extension('png'),
            'metavar': 'SCREENSHOT',
        },
        ('--personal-release', '--pr'): {
            'help': 'Tag submission as your own release',
            'action': 'store_true',
        },
        ('--only-description', '--od'): {
            'help': 'Only generate description (do not submit)',
            'action': 'store_true',
            'group': 'generate-metadata',
        },
        ('--only-title', '--ot'): {
            'help': 'Only generate title (do not submit)',
            'action': 'store_true',
            'group': 'generate-metadata',
        },
    },
}
