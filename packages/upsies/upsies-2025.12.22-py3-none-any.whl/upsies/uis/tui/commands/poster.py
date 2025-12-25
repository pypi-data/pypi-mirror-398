"""
Find, download and re-upload poster for movie, series or season
"""

import functools

from .... import imagehosts, jobs, utils
from .base import CommandBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class poster(CommandBase):
    """Download, resize and re-upload poster from IMDb or similar website"""

    names = ('poster',)

    cli_arguments = {
        'RELEASE': {
            'type': utils.argtypes.release,
            'help': 'Release name or path to release content',
        },
        ('--db', '-d'): {
            'type': utils.argtypes.webdb,
            'help': ('Case-insensitive database name (default: imdb)\n'
                     'Supported databases: ' + ', '.join(utils.webdbs.webdb_names())),
            'default': None,
        },
        ('--upload-to', '-u'): {
            'type': utils.types.ListOf(
                item_type=utils.argtypes.imagehost,
                separator=',',
            ),
            'metavar': 'IMAGE_HOST',
            'help': ('Comma-separated list of case-insensitive names of image hosting services\n'
                     'Only the URL from the first successfull upload is used.\n'
                     'Supported services: ' + ', '.join(imagehosts.imagehost_names())),
            'default': (),
        },
        ('--width', '-w'): {
            'help': 'Poster width in pixels (default: 0 (no resizing))',
            'type': utils.argtypes.integer,
            'default': 0,
        },
        ('--height', '-t'): {
            'help': 'Poster height in pixels (default: 0 (no resizing))',
            'type': utils.argtypes.integer,
            'default': 0,
        },
        ('--output', '-o'): {
            'help': 'Write poster to file OUTPUT',
            'default': None,
        },
    }

    @functools.cached_property
    def release_name(self):
        return utils.release.ReleaseName(self.args.RELEASE)

    @functools.cached_property
    def webdb(self):
        if self.args.db:
            return utils.webdbs.webdb(self.args.db)
        elif self.release_name.type in (utils.release.ReleaseType.season,
                                        utils.release.ReleaseType.episode):
            return utils.webdbs.webdb('tvmaze')
        else:
            return utils.webdbs.webdb('imdb')

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

    @functools.cached_property
    def jobs(self):
        return (
            self.webdb_job,
            self.poster_job,
        )

    @functools.cached_property
    def webdb_job(self):
        return jobs.webdb.WebDbSearchJob(
            home_directory=self.cache_directory,
            cache_directory=self.cache_directory,
            ignore_cache=self.args.ignore_cache,
            query=utils.webdbs.Query.from_release(self.release_name),
            db=self.webdb,
            show_poster=self.config['config']['id']['show_poster'],
        )

    @property
    def webdb_id(self):
        if self.webdb_job.is_finished and self.webdb_job.output:
            return self.webdb_job.output[0]

    @functools.cached_property
    def poster_job(self):
        return jobs.poster.PosterJob(
            home_directory=self.home_directory if self.imagehosts else '.',
            cache_directory=self.cache_directory,
            ignore_cache=self.args.ignore_cache,
            prejobs=(
                self.webdb_job,
            ),
            getter=self.get_poster,
            width=self.args.width,
            height=self.args.height,
            write_to=self.args.output,
            imagehosts=self.imagehosts,
        )

    async def get_poster(self):
        return await self.webdb.poster_url(
            self.webdb_id,
            season=self.release_name.only_season,
        )
