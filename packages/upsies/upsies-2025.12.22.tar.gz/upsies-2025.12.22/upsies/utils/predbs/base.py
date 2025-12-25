"""
Abstract base class for scene release databases
"""

import abc
import asyncio
import collections
import copy

from ... import constants, errors, utils

import logging  # isort:skip
_log = logging.getLogger(__name__)

natsort = utils.LazyModule(module='natsort', namespace=globals())


class PredbApiBase(abc.ABC):
    """Base class for scene release database APIs"""

    def __init__(self, config=None):
        self._config = copy.deepcopy(self.default_config)
        if config is not None:
            self._config.update(config.items())

    @property
    @abc.abstractmethod
    def name(self):
        """Unique name of the scene release database"""

    @property
    @abc.abstractmethod
    def label(self):
        """User-facing name of the scene release database"""

    @property
    def config(self):
        """
        User configuration

        This is a deep copy of :attr:`default_config` that is updated with the
        `config` argument from initialization.
        """
        return self._config

    @property
    @abc.abstractmethod
    def default_config(self):
        """Default user configuration as a dictionary"""

    @abc.abstractmethod
    async def _search(self, query):
        """
        Perform search

        :param SceneQuery query: Search keywords
        """

    async def search(self, query, *, only_existing_releases=True):
        """
        Search for scene release

        If there are no results and `query` is a directory path that looks like
        a season pack, perform one search per video file in that directory or
        any subdirectory. This is necessary to find mixed season packs.

        :param query: :class:`~.SceneQuery` object or :class:`str` to pass to
            :meth:`~.SceneQuery.from_string` or :class:`collections.abc.Mapping`
            to pass to :meth:`~.SceneQuery.from_release`
        :param bool only_existing_releases: If this is truthy, imaginary season
            pack releases are created and added to the search results.

        :return: :class:`list` of release names as :class:`str`

        :raise RequestError: if the search request fails
        """
        path = None
        if isinstance(query, str):
            path = query
            query = utils.predbs.SceneQuery.from_string(query)
        elif isinstance(query, collections.abc.Mapping):
            query = utils.predbs.SceneQuery.from_release(query)

        try:
            results = list(await self._search(query))
        except NotImplementedError as e:
            raise errors.RequestError(f'{self.name} does not support searching') from e

        if not results and path:
            # Maybe `path` points to season pack?
            # Find episodes and search for them individually.
            return await self._search_for_episodes(path, only_existing_releases)
        else:
            return self._postprocess_search_results(results, query, only_existing_releases)

    async def _search_for_episodes(self, path, only_existing_releases):
        combined_results = []
        for episode_query in self._generate_episode_queries(path):
            results = await self.search(episode_query, only_existing_releases=only_existing_releases)
            combined_results.extend(results)
        return combined_results

    def _generate_episode_queries(self, path):
        info = utils.release.ReleaseInfo(path)
        if info['type'] is utils.release.ReleaseType.season:
            # Create SceneQuery from each episode path
            episode_paths = utils.fs.file_list(path, extensions=constants.VIDEO_FILE_EXTENSIONS)
            for episode_path in episode_paths:
                if not utils.predbs.is_abbreviated_filename(episode_path):
                    _log.debug('Generating query for episode: %r', episode_path)
                    # guessit prefers getting the group name from the parent
                    # directory, but the group in the parent directory is likely
                    # "MiXED", so we definitely want the group from the file.
                    filename = utils.fs.basename(episode_path)
                    yield utils.predbs.SceneQuery.from_string(filename)

    def _postprocess_search_results(self, results, query, only_existing_releases):
        def sorted_and_deduped(results):
            return natsort.natsorted(set(results), key=str.casefold)

        if not query.episodes:
            # _log.debug('No episodes queried: %r', query.episodes)
            return sorted_and_deduped(results)
        else:
            # _log.debug('Episodes queried: %r', query.episodes)

            def get_wanted_episodes(season):
                # Combine episodes from any season with episodes from given
                # season (season being empty string means "any season")
                eps = None
                if '' in query.episodes:
                    eps = query.episodes['']
                if season in query.episodes:
                    eps = (eps or []) + query.episodes[season]
                return eps

            # Translate single episodes into season packs.
            matches = []
            for result in results:
                for result_season, result_eps in utils.release.Episodes.from_string(result).items():
                    wanted_episodes = get_wanted_episodes(result_season)

                    # [] means season pack
                    if wanted_episodes == []:
                        if only_existing_releases:
                            # Add episode from wanted season pack
                            _log.debug('Adding episode from season pack: %r', result)
                            matches.append(result)
                        else:
                            season_pack = utils.predbs.common.get_season_pack_name(result)
                            if season_pack not in matches:
                                _log.debug('Adding season pack: %r', season_pack)
                                matches.append(season_pack)

                    elif wanted_episodes is not None:
                        for ep in result_eps:
                            if ep in wanted_episodes:
                                matches.append(result)
                                break

            return sorted_and_deduped(matches)

    @abc.abstractmethod
    async def _release_files(self, release_name):
        pass

    async def release_files(self, release_name):
        """
        Map release file names to file information

        If this is not implemented by the subclass, :class:`NotImplementedError`
        is raised.

        Each file information is a dictionary that contains at least the keys
        ``release_name``, ``file_name`` and ``size``. More keys may be available
        depending on the subclass implementation.

        If `release_name` is a season pack, information the relevant episode
        releases is returned.

        :param str release_name: Exact name of the release

        :raise RequestError: if request fails or `release_name` is not found
        """
        try:
            files = await self._release_files(release_name)
        except NotImplementedError as e:
            raise errors.RequestError(f'{self.name} does not provide file information') from e

        if files:
            return files
        else:
            _log.debug('No such release: %r', release_name)
            files = {}

        # If scene released "Foo.S01E0{1,2,3,...}.720p.BluRay-BAR" and we're
        # searching for "Foo.S01.720p.BluRay-BAR", we most likely don't get any
        # results. But we can get release names of individual episodes by
        # searching for the season pack, and then we can call release_files()
        # for each episode.
        release_info = utils.release.ReleaseInfo(release_name)
        if release_info['type'] is utils.release.ReleaseType.season:
            results = await self.search(release_info, only_existing_releases=True)
            if results:
                files = await asyncio.gather(
                    *(self._release_files(result) for result in results)
                )

                # Flatten sequence of dictionaries into single dictionary
                files = {
                    file_name: file_info
                    for files_ in files
                    for file_name, file_info in files_.items()
                }
                _log.debug('Season pack from multiple episode releases: %r', files)

        # If scene released season pack (e.g. Extras or Bonus content) and we're
        # searching for a single episode, we most likely don't get any results.
        # Search for the season pack to get all files.
        elif release_info['type'] is utils.release.ReleaseType.episode:
            # Remove single episodes from seasons
            release_info['episodes'].remove_specific_episodes()
            results = await self.search(release_info)
            if len(results) == 1:
                _log.debug('Getting files from single result: %r', results[0])
                files = await self._release_files(results[0])

        # Go through all files and find the exact release name we're looking for.
        # Don't do this exclusively for episodes because not all multi-file releases
        # are a list of episodes (e.g. extras may not contain any "Exx").
        for file_name, file_info in files.items():
            if utils.fs.strip_extension(release_name) == utils.fs.strip_extension(file_name):
                files = {file_name: file_info}
                _log.debug('Single file from season pack release: %r', files)
                break

        return files
