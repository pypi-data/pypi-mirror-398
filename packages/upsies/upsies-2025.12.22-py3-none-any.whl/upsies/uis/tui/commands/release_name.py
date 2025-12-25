"""
Generate properly formatted release name
"""

import functools

from .... import errors, jobs, utils
from .base import CommandBase


class release_name(CommandBase):
    """
    Generate properly formatted release name

    IMDb is searched to get the correct title, year and alternative title if
    applicable.

    Audio and video information is detected with mediainfo.

    Missing required information is highlighted with placeholders,
    e.g. "UNKNOWN_RESOLUTION".
    """

    names = ('release-name', 'rn')

    cli_arguments = {
        'RELEASE': {
            'type': utils.argtypes.release,
            'help': 'Release name or path to release content',
        },
        ('--separator', '-s'): {
            'default': ' ',
            'help': 'Separator between parts (default: " ")',
        },
    }

    @functools.cached_property
    def jobs(self):
        return (self.imdb_job, self.release_name_job)

    @functools.cached_property
    def release_name(self):
        return utils.release.ReleaseName(
            self.args.RELEASE,
            separator=self.args.separator,
        )

    @functools.cached_property
    def release_name_job(self):
        return jobs.dialog.TextFieldJob(
            name='release-name',
            label='Release Name',
            home_directory=self.home_directory,
            cache_directory=self.cache_directory,
            cache_id=f'separator={self.args.separator}',
            ignore_cache=self.args.ignore_cache,
            prejobs=(
                self.imdb_job,
            ),
            text=self.get_release_name,
        )

    async def get_release_name(self):
        imdb_id = self.imdb_job.output[0]
        await self.release_name_job.fetch_text(
            coro=self.release_name.fetch_info(webdb=self.imdb, webdb_id=imdb_id),
            warn_exceptions=(
                errors.RequestError,
            ),
            default=self.release_name,
        )

    @functools.cached_property
    def imdb_job(self):
        # To be able to fetch the original title, year, etc, we need to ask for
        # an ID first. IMDb seems to be best.
        return jobs.webdb.WebDbSearchJob(
            home_directory=self.home_directory,
            cache_directory=self.cache_directory,
            ignore_cache=self.args.ignore_cache,
            query=utils.webdbs.Query.from_path(self.args.RELEASE),
            db=self.imdb,
            show_poster=self.config['config']['id']['show_poster'],
        )

    @functools.cached_property
    def imdb(self):
        return utils.webdbs.webdb('imdb')
