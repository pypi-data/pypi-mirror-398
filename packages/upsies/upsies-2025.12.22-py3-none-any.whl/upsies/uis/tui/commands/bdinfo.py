"""
Print ``bdinfo`` output
"""

import functools

from .... import jobs, utils
from .base import CommandBase


class bdinfo(CommandBase):
    """
    Print the BDInfo report(s)

    This needs a ``bdinfo`` executable in your $PATH. It is called like this:

        bdinfo --mpls=PLAYLIST_FILE_NAME PATH_TO_BLURAY REPORT_DIRECTORY

    Here is a wrapper script that runs BDInfoCLI-ng in a docker container:
    https://codeberg.org/plotski/upsies/src/branch/master/goodies/bdinfo
    """

    names = ('bdinfo', 'bi')

    cli_arguments = {
        'CONTENT': {
            'type': utils.argtypes.content,
            'help': 'Path to release content',
        },
        ('--summary', '-s'): {
            'choices': ('none', 'full', 'quick'),
            'default': 'none',
            'help': 'Which parts of the BDInfo output to print',
            'group': 'playlist_or_summary',
        },
        ('--multiple', '-m'): {
            'help': 'Allow selection of multiple playlists and generate multiple BDInfo reports',
            'action': 'store_true',
        },
        ('--format', '-f'): {
            'help': ('Text that contains the placeholder "{BDINFO}", which is replaced '
                     'by the BDInfo report\n'
                     'Example: "[bdinfo]{BDINFO}[/bdinfo]"'),
            'default': '{BDINFO}',
        },
    }

    @functools.cached_property
    def playlists_job(self):
        return jobs.playlists.PlaylistsJob(
            home_directory=self.home_directory,
            cache_directory=self.cache_directory,
            ignore_cache=self.args.ignore_cache,
            content_path=self.args.CONTENT,
            select_multiple=self.args.multiple,
        )

    @functools.cached_property
    def bdinfo_job(self):
        return jobs.bdinfo.BdinfoJob(
            home_directory=self.home_directory,
            cache_directory=self.cache_directory,
            ignore_cache=self.args.ignore_cache,
            summary=(
                None
                if self.args.summary == 'none' else
                self.args.summary
            ),
            format=self.args.format,
        )

    @functools.cached_property
    def jobs(self):
        return (
            self.playlists_job,
            self.bdinfo_job,
        )
