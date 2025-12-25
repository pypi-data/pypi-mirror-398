"""
Search online database like IMDb to get an ID
"""

import functools

from .... import jobs, utils
from .base import CommandBase


class webdb_search(CommandBase):
    """
    Search online database like IMDb to get an ID

    Pressing ``Enter`` searches for the current query. Pressing ``Enter`` again
    without changing the query selects the focused search result.

    The focused search result can be opened in the default web browser with
    ``Alt-Enter``.

    Search results can be narrowed down with the following parameters:

      - year:YYYY
        Only return results with a specific release year.

      - type:series|movie
        Only return movies or series.

      - id:ID
        Search for a specific, known ID.

    If possible, the ID is also detected in normal text without the "id:ID"
    format. The exact detection is specific to each database, but searching for
    an URL (e.g. https://www.tvmaze.com/shows/1910) should always work.

    If the query starts with "!" and there is only one search result,
    automatically select it. This is useful when searching for an ID,
    e.g. "!id:tt0123456".
    """

    names = ('id',)

    cli_arguments = {
        'DB': {
            'type': utils.argtypes.webdb,
            'help': ('Case-insensitive database name\n'
                     'Supported databases: ' + ', '.join(utils.webdbs.webdb_names())),
        },
        'RELEASE': {
            'type': utils.argtypes.release,
            'help': 'Release name or path to release content',
        },
    }

    @functools.cached_property
    def jobs(self):
        return (
            jobs.webdb.WebDbSearchJob(
                home_directory=self.home_directory,
                cache_directory=self.cache_directory,
                ignore_cache=self.args.ignore_cache,
                query=utils.webdbs.Query.from_path(self.args.RELEASE),
                db=utils.webdbs.webdb(self.args.DB),
                show_poster=self.config['config']['id']['show_poster'],
            ),
        )
