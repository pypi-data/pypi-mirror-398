"""
Concrete :class:`~.TrackerConfigBase` subclass for PTP
"""

import base64

from ... import utils
from .. import base
from . import metadata

PtpImagehost = utils.types.Imagehost(
    disallowed=(
        ()
        if utils.is_running_in_development_environment() else
        ('dummy',)
    ),
)


class PtpReleaseType(str):
    def __new__(cls, text):
        for type, regex in metadata.types.items():
            if regex.search(text):
                return super().__new__(cls, type)
        raise utils.argtypes.ArgumentTypeError(f'Invalid type: {text}')


class PtpTrackerConfig(base.TrackerConfigBase):
    base_url: base.config.base_url(
        base64.b64decode('aHR0cHM6Ly9wYXNzdGhlcG9wY29ybi5tZQ==').decode('ascii'),
    )

    username: base.config.username('')

    password: base.config.password('')

    cookies_filepath: base.config.cookies_filepath('')

    announce_url: base.config.announce_url('')

    image_host: base.config.image_host(
        PtpImagehost,
        default=('ptpimg', 'freeimage'),
    )

    screenshots_from_movie: base.config.screenshots_count(
        default=3,
        min=3,
        max=10,
        description='How many screenshots to make for single-video uploads.',
    )

    screenshots_from_episode: base.config.screenshots_count(
        default=2,
        min=2,
        max=10,
        description='How many screenshots to make per video for multi-video uploads.',
    )

    exclude: base.config.exclude(
        base.exclude_regexes.checksums,
        base.exclude_regexes.garbage,
        base.exclude_regexes.images,
        base.exclude_regexes.nfo,
        base.exclude_regexes.samples,
    )


cli_arguments = {
    'submit': {
        ('--subtitles', '--su'): {
            'help': (
                'Comma-separated list of subtitle language codes.\n'
                'Use this if subtitles are hardcoded or missing language tags.'
            ),
            'metavar': 'LANGUAGES',
            'type': utils.types.ListOf(
                item_type=utils.argtypes.subtitle,
                separator=',',
            ),
        },
        ('--hardcoded-subtitles', '--hs'): {
            'help': 'Release is trumpable because of hardcoded subtitles',
            'action': 'store_true',
        },
        ('--no-english-subtitles', '--nes'): {
            'help': (
                'Whether release contains no English audio and no English subtitles.\n'
                'This is autodetected reliably if all audio and subtitle tracks have '
                'a correct language tag. If not, you are asked interactively.\n'
                'Subtitle languages are detected in *.idx/sub, VIDEO_TS trees, '
                'BDMV trees and *.srt/ssa/ass/vtt by language code in the file name, e.g. '
                '"Foo.en.srt".'
            ),
            'metavar': 'BOOL',
            'type': utils.argtypes.bool_or_none,
        },
        ('--not-main-movie', '--nmm'): {
            'help': 'Upload ONLY contains extras, Rifftrax, Workprints',
            'action': 'store_true',
        },
        ('--personal-rip', '--pr'): {
            'help': 'Tag submission as your own encode',
            'action': 'store_true',
        },
        ('--poster', '--po'): {
            'help': 'Path or URL to movie poster',
        },
        ('--nfo',): {
            'help': 'Path to NFO file (supersedes any *.nfo file found in the release directory)',
        },
        ('--imdb', '--im'): {
            'help': 'IMDb ID or URL',
            'type': utils.argtypes.webdb_id('imdb'),
        },
        ('--source', '--so'): {
            'help': (
                'Original source of this release\n'
                + 'Should vaguely match: '
                + ', '.join(metadata.sources)
            ),
        },
        ('--type', '--ty'): {
            'help': (
                'General category of this release\n'
                + 'Must vaguely match: '
                + ', '.join(metadata.types)
            ),
            'type': PtpReleaseType,
        },
        ('--screenshots-count', '--ssc'): {
            'help': 'How many screenshots to make per video file',
            'type': utils.argtypes.make_integer(min=1, max=10),
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
        ('--upload-token', '--ut'): {
            'help': 'Upload token from staff',
        },
        ('--only-description', '--od'): {
            'help': 'Only generate description (do not submit)',
            'action': 'store_true',
            'group': 'generate-metadata',
        },
    },
}
