"""
Concrete :class:`~.TrackerConfigBase` subclass for MTV
"""

import base64

from ... import utils
from .. import base

MtvImagehost = utils.types.Imagehost(
    allowed=(
        ('imgbb', 'imgbox', 'ptpimg', 'dummy')
        if utils.is_running_in_development_environment() else
        ('imgbb', 'imgbox', 'ptpimg')
    ),
)


class MtvTrackerConfig(base.TrackerConfigBase):
    base_url: base.config.base_url(
        base64.b64decode('aHR0cHM6Ly93d3cubW9yZXRoYW50di5tZQ==').decode('ascii'),
    )

    username: base.config.username('')

    password: base.config.password('')

    cookies_filepath: base.config.cookies_filepath('')

    announce_url: base.config.announce_url('', autofetched=True)

    image_host: base.config.image_host(
        MtvImagehost,
        default=('imgbox',),
    )

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
        ('--screenshots-count', '--ssc'): {
            'help': ('How many screenshots to make '
                     f'(min={MtvTrackerConfig.defaults["screenshots_count"].min}, '
                     f'max={MtvTrackerConfig.defaults["screenshots_count"].max})'),
            'type': utils.argtypes.make_integer(
                min=MtvTrackerConfig.defaults['screenshots_count'].min,
                max=MtvTrackerConfig.defaults['screenshots_count'].max,
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
        ('--ignore-dupes', '--id'): {
            'help': 'Force submission even if the tracker reports duplicates',
            'action': 'store_true',
        },
    },
}
