"""
Print ``mediainfo`` output
"""

import functools

from .... import jobs, utils
from .base import CommandBase


class mediainfo(CommandBase):
    """
    Print ``mediainfo`` output

    Directories are recursively searched for the first video file in natural
    order, e.g. "File1.mp4" comes before "File10.mp4".

    Any irrelevant leading parts in the file path are removed from the output.
    """

    names = ('mediainfo', 'mi')

    cli_arguments = {
        'CONTENT': {
            'type': utils.argtypes.content,
            'help': 'Path to release content',
        },
        ('--from-all-videos', '-a'): {
            'action': 'store_true',
            'help': 'Get mediainfo from each video file beneath CONTENT',
        },
        ('--exclude-files', '--ef'): {
            'nargs': '+',
            'metavar': 'PATTERN',
            'help': ('Glob pattern to exclude from CONTENT '
                     '(matched case-insensitively against path relative to CONTENT)'),
            'default': (),
        },
        ('--exclude-files-regex', '--efr'): {
            'nargs': '+',
            'metavar': 'PATTERN',
            'help': ('Regular expression to exclude from CONTENT '
                     '(matched case-sensitively against path relative to CONTENT)'),
            'type': utils.argtypes.regex,
            'default': (),
        },
        ('--format', '-f'): {
            'help': ('Text that contains the placeholder "{MEDIAINFO}", which is replaced '
                     'by the `mediainfo` output\n'
                     'Example: "[mediainfo]{MEDIAINFO}[/mediainfo]"'),
            'default': '{MEDIAINFO}',
        },
    }

    @functools.cached_property
    def jobs(self):
        return (
            self.playlists_job,
            self.mediainfo_job,
        )

    @functools.cached_property
    def playlists_job(self):
        if utils.disc.is_disc(self.args.CONTENT, multidisc=True):
            return jobs.playlists.PlaylistsJob(
                home_directory=self.home_directory,
                cache_directory=self.cache_directory,
                ignore_cache=self.args.ignore_cache,
                content_path=self.args.CONTENT,
                select_multiple=self.args.from_all_videos,
            )

    @functools.cached_property
    def mediainfo_job(self):
        return jobs.mediainfo.MediainfoJob(
            home_directory=self.home_directory,
            cache_directory=self.cache_directory,
            ignore_cache=self.args.ignore_cache,
            content_path=self.args.CONTENT,
            from_all_videos=self.args.from_all_videos,
            exclude_files=(
                tuple(self.args.exclude_files)
                + tuple(self.args.exclude_files_regex)
            ),
            format=self.args.format,
        )
