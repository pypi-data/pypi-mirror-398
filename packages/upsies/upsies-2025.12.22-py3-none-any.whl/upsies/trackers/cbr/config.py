"""
Concrete :class:`~.TrackerConfigBase` subclass for CBR
"""

import base64

from ... import utils
from .. import base

CbrImagehost = utils.types.Imagehost(
    allowed=(
        ('imgbox', 'ptpimg', 'imgbb', 'freeimage', 'dummy')
        if utils.is_running_in_development_environment() else
        ('imgbox', 'ptpimg', 'imgbb', 'freeimage')
    ),
)


class CbrTrackerConfig(base.TrackerConfigBase):
    base_url: base.config.base_url(
        base64.b64decode('aHR0cHM6Ly9jYXB5YmFyYWJyLmNvbQ==').decode('ascii')
    )

    announce_url: base.config.announce_url(
        default='',
        autofetched=False,
        instructions='Get it from the website: Torrents > Upload > URL de Anúncio',
    )

    apikey: base.config.apikey(
        default='',
        instructions='Get it from the website: Your profile > Settings > API key',
    )

    anonymous: base.config.anonymous('no')

    image_host: base.config.image_host(
        CbrImagehost,
        default=('imgbox', 'freeimage')
    )

    screenshots_count: base.config.screenshots_count(4, min=3, max=10)

    exclude: base.config.exclude(
        base.exclude_regexes.checksums,
        base.exclude_regexes.extras,
        base.exclude_regexes.garbage,
        base.exclude_regexes.images,
        base.exclude_regexes.nfo,
        base.exclude_regexes.samples,
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
        ('--nfo',): {
            'help': 'Path to NFO file (supersedes any *.nfo file found in the release directory)',
        },
        ('--personal-rip', '--pr'): {
            'help': 'Tag submission as your own encode',
            'action': 'store_true',
        },
        ('--queue', '--qe'): {
            'help': 'Send to moderation queue',
            'action': 'store_true',
        },
        ('--screenshots-count', '--ssc'): {
            'help': ('How many screenshots to make '
                     f'(min={CbrTrackerConfig.defaults["screenshots_count"].min}, '
                     f'max={CbrTrackerConfig.defaults["screenshots_count"].max})'),
            'type': utils.argtypes.make_integer(
                min=CbrTrackerConfig.defaults['screenshots_count'].min,
                max=CbrTrackerConfig.defaults['screenshots_count'].max,
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
