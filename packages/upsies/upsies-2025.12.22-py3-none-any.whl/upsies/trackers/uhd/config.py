"""
Concrete :class:`~.TrackerConfigBase` subclass for UHD
"""

import base64

from ... import utils
from .. import base

UhdImagehost = utils.types.Imagehost(
    disallowed=(
        ()
        if utils.is_running_in_development_environment() else
        ('dummy',)
    ),
)


class UhdTrackerConfig(base.TrackerConfigBase):
    base_url: base.config.base_url(
        base64.b64decode('aHR0cHM6Ly91aGRiaXRzLm9yZw==').decode('ascii'),
    )

    username: base.config.username('')

    password: base.config.password('')

    cookies_filepath: base.config.cookies_filepath('')

    announce_url: base.config.announce_url('', autofetched=True)

    image_host: base.config.image_host(
        UhdImagehost,
        default=('ptpimg', 'freeimage', 'imgbox'),
    )

    screenshots_count: base.config.screenshots_count(4, min=2, max=10)

    exclude: base.config.exclude(
        base.exclude_regexes.checksums,
        base.exclude_regexes.garbage,
        base.exclude_regexes.images,
        base.exclude_regexes.nfo,
        base.exclude_regexes.samples,
        base.exclude_regexes.subtitles,
    )

    anonymous: base.config.anonymous('no')


cli_arguments = {
    'submit': {
        ('--imdb', '--im'): {
            'help': 'IMDb ID or URL',
            'type': utils.argtypes.webdb_id('imdb'),
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
        ('--internal', '--in'): {
            'help': 'Internal encode (use only if you were told to)',
            'action': 'store_true',
        },
        ('--3d',): {
            'help': 'Mark this as a 3D release',
            'action': 'store_true',
        },
        ('--vie', '--vi'): {
            'help': 'Release contains Vietnamese audio dub',
            'action': 'store_true',
        },
        ('--screenshots-count', '--ssc'): {
            'help': ('How many screenshots to make '
                     f'(min={UhdTrackerConfig.defaults["screenshots_count"].min}, '
                     f'max={UhdTrackerConfig.defaults["screenshots_count"].max})'),
            'type': utils.argtypes.make_integer(
                min=UhdTrackerConfig.defaults['screenshots_count'].min,
                max=UhdTrackerConfig.defaults['screenshots_count'].max,
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
        ('--nfo',): {
            'help': 'Path to NFO file (supersedes any *.nfo file found in the release directory)',
        },
        ('--poster', '--po'): {
            'help': 'Path or URL to poster image (autodetected by default)',
        },
        ('--trailer', '--tr'): {
            'help': 'Trailer YouTube ID or URL (autodetected by default)',
        },
        ('--only-description', '--od'): {
            'help': 'Only generate description (do not submit)',
            'action': 'store_true',
            'group': 'generate-metadata',
        },
    },
}
