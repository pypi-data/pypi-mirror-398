"""
Create screenshots from video file and optionally upload them
"""

import functools

from .... import imagehosts, jobs, utils
from .base import CommandBase


class screenshots(CommandBase):
    """Create screenshots from video file and optionally upload them"""

    names = ('screenshots', 'ss')

    cli_arguments = {
        'CONTENT': {
            'type': utils.argtypes.content,
            'help': 'Path to release content',
        },
        ('--exclude-files', '--ef'): {
            'action': 'extend',
            'nargs': '+',
            'metavar': 'PATTERN',
            'help': ('Glob pattern to exclude from CONTENT '
                     '(matched case-insensitively against path relative to CONTENT)'),
            'default': [],
        },
        ('--exclude-files-regex', '--efr'): {
            'action': 'extend',
            'nargs': '+',
            'metavar': 'PATTERN',
            'help': ('Regular expression to exclude from CONTENT '
                     '(matched case-sensitively against path relative to CONTENT)'),
            'type': utils.argtypes.regex,
            'default': [],
        },
        ('--timestamps', '-t'): {
            'nargs': '+',
            'action': 'extend',
            'default': [],
            'type': utils.argtypes.timestamp,
            'metavar': 'TIMESTAMP',
            'help': 'Space-separated list of [[HH:]MM:]SS strings',
        },
        ('--precreated', '-p'): {
            'nargs': '+',
            'action': 'extend',
            'default': [],
            'metavar': 'SCREENSHOT',
            'help': 'Existing screenshot file path',
        },
        ('--number', '-n'): {
            'type': utils.argtypes.integer,
            'help': 'How many screenshots to make in total',
            'default': 0,
        },
        ('--from-all-videos', '-a'): {
            'action': 'store_true',
            'help': 'Make NUMBER screenshots from each video file beneath CONTENT',
        },
        ('--optimize', '--opt'): {
            'type': utils.argtypes.one_of(utils.image.optimization_levels),
            'default': None,
            'metavar': 'LEVEL',
            'help': f'File size optimization level: {", ".join(utils.image.optimization_levels)}',
        },
        ('--tonemap'): {
            'type': utils.argtypes.bool_or_none,
            'default': None,
            'metavar': 'BOOL',
            'help': 'Apply tonemap filter to HDR screenshots',
        },
        ('--upload-to', '-u'): {
            'type': utils.argtypes.imagehosts,
            'metavar': 'IMAGE_HOSTS',
            'help': (
                'Comma-separated list of case-insensitive image hosting service names\n'
                'Supported services: ' + ', '.join(imagehosts.imagehost_names())
            ),
        },
        ('--output-directory', '-o'): {
            'default': '',  # Current working directory
            'metavar': 'PATH',
            'help': 'Directory where screenshots are put (created on demand)',
        },
    }

    @functools.cached_property
    def jobs(self):
        return (
            self.playlists_job,
            self.screenshots_job,
            self.upload_screenshots_job,
        )

    @functools.cached_property
    def playlists_job(self):
        if utils.disc.is_disc(self.args.CONTENT, multidisc=True):
            return jobs.playlists.PlaylistsJob(
                home_directory=self.home_directory,
                cache_directory=self.cache_directory,
                ignore_cache=self.args.ignore_cache,
                content_path=self.args.CONTENT,
                # In case of multidisc release, only ask user to select playlists from first
                # selected disk.
                select_multiple=self.args.from_all_videos,
            )

    @functools.cached_property
    def screenshots_job(self):
        return jobs.screenshots.ScreenshotsJob(
            home_directory=self.args.output_directory,
            cache_directory=self.cache_directory,
            ignore_cache=self.args.ignore_cache,
            content_path=self.args.CONTENT,
            exclude_files=(
                tuple(self.args.exclude_files)
                + tuple(self.args.exclude_files_regex)
            ),
            timestamps=self.args.timestamps,
            precreated=self.args.precreated,
            count=self.args.number,
            from_all_videos=self.args.from_all_videos,
            optimize=(
                self.args.optimize
                if self.args.optimize is not None else
                self.config['config']['screenshots']['optimize']
            ),
            tonemap=(
                self.args.tonemap
                if self.args.tonemap is not None else
                self.config['config']['screenshots']['tonemap']
            )
        )

    @functools.cached_property
    def upload_screenshots_job(self):
        if self.args.upload_to:
            return jobs.imagehost.ImagehostJob(
                home_directory=self.home_directory,
                cache_directory=self.cache_directory,
                ignore_cache=self.args.ignore_cache,
                imagehosts=self.imagehosts,
            )

    @functools.cached_property
    def imagehosts(self):
        return tuple(
            imagehosts.imagehost(
                name=name,
                config=self.config['imghosts'][name],
                cache_directory=self.cache_directory,
            )
            for name in self.args.upload_to
        )
