"""
Concrete :class:`~.TrackerConfigBase` subclass for BHD
"""

import base64

from ... import utils
from .. import base

BhdImagehost = utils.types.Imagehost(
    allowed=(
        ('imgbox', 'ptpimg', 'imgbb', 'dummy')
        if utils.is_running_in_development_environment() else
        ('imgbox', 'ptpimg', 'imgbb')
    ),
)


class BhdTrackerConfig(base.TrackerConfigBase):
    upload_url: base.config.upload_url(
        base64.b64decode('aHR0cHM6Ly9iZXlvbmQtaGQubWUvYXBpL3VwbG9hZA==').decode('ascii')
    )

    announce_url: utils.config.fields.string(
        default=base64.b64decode('aHR0cHM6Ly90cmFja2VyLmJleW9uZC1oZC5tZToyMDUzL2Fubm91bmNl').decode('ascii'),
        description='Announce URL without the private passkey.',
    )

    announce_passkey: utils.config.fields.string(
        default='',
        description=(
            'The private part of the announce URL.\n'
            'Get it from the website: My Security -> Passkey'
        ),
        secret=True,
    )

    apikey: base.config.apikey('')

    anonymous: base.config.anonymous('no')

    draft: utils.config.fields.boolean(
        default='no',
        description=(
            'Whether your uploads are stashed under Torrents -> Drafts '
            'after the upload instead of going live immediately.'
        ),
    )

    image_host: base.config.image_host(BhdImagehost, default=('imgbox',))

    screenshots_count: base.config.screenshots_count(4, min=3, max=10)

    exclude: base.config.exclude(
        base.exclude_regexes.checksums,
        base.exclude_regexes.extras,
        base.exclude_regexes.garbage,
        base.exclude_regexes.images,
        base.exclude_regexes.nfo,
        base.exclude_regexes.samples,
        base.exclude_regexes.subtitles,
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
        ('--custom-edition', '--ce'): {
            'help': 'Non-standard edition, e.g. "Final Cut"',
            'default': '',
        },
        ('--draft', '--dr'): {
            'help': 'Upload as draft',
            'action': 'store_true',
            # The default value must be None so CommandBase.get_options()
            # doesn't always overwrite the value with the config file value.
            'default': None,
        },
        ('--nfo',): {
            'help': 'Path to NFO file (supersedes any *.nfo file found in the release directory)',
        },
        ('--personal-rip', '--pr'): {
            'help': 'Tag submission as your own encode',
            'action': 'store_true',
        },
        ('--screenshots-count', '--ssc'): {
            'help': ('How many screenshots to make '
                     f'(min={BhdTrackerConfig.defaults["screenshots_count"].min}, '
                     f'max={BhdTrackerConfig.defaults["screenshots_count"].max})'),
            'type': utils.argtypes.make_integer(
                min=BhdTrackerConfig.defaults['screenshots_count'].min,
                max=BhdTrackerConfig.defaults['screenshots_count'].max,
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
        ('--special', '--sp'): {
            'help': 'Tag as special episode, e.g. Christmas special (ignored for movie uploads)',
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
