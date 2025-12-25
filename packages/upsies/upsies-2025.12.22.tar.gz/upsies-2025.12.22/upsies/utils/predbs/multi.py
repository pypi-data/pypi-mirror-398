import asyncio
import collections
import difflib
import functools
import os
import re

import async_lru

from ... import constants, errors, utils
from . import SceneCheckResult

import logging  # isort:skip
_log = logging.getLogger(__name__)


class MultiPredbApi:
    """
    Wrapper around multiple :class:`~.PredbApiBase` instances

    Each method loops over every provided predb and calls the same method on
    it. The first call that does not raise :class:`~.RequestError` or
    :class:`NotImplementedError` is returned.

    If no call succeeds and any exceptions were raised, they are combined into a
    single :class:`~.RequestError`, which is raised. If every call raised
    :class:`NotImplementedError`, a combined :class:`NotImplementedError` is
    raised.

    :param predbs: Sequence of :class:`~.PredbApiBase` instances
    """

    DEFAULT_PREDB_NAMES = (
        'srrdb',
        'corruptnet',
        # 'predbovh',
        # 'predbclub',
        'predbnet',
    )

    def __init__(self, predbs=None):
        if predbs:
            self._predbs = predbs
        else:
            self._predbs = [
                utils.predbs.predb(name)
                for name in type(self).DEFAULT_PREDB_NAMES
            ]

    @functools.cached_property
    def predbs(self):
        """Sequence of :class:`~.PredbApiBase` that are used"""
        return tuple(self._predbs)

    async def _call(self, predb, method_name, *args, **kwargs):
        method = getattr(predb, method_name)
        return await method(*args, **kwargs)

    def _raise(self, exceptions, method_name):
        if not exceptions:
            raise NotImplementedError(
                '|'.join(predb.name for predb in self._predbs)
                + f'.{method_name}'
            )
        elif len(exceptions) == 1:
            raise exceptions[0]
        else:
            raise errors.RequestError(
                'All queries failed: ' + ', '.join(str(e) for e in exceptions)
            )

    async def _for_each_predb(self, predbs, method_name, *args, **kwargs):
        # Try calling `method_name` on each predb sequentially and return the
        # first successful response.
        exceptions = []
        for predb in predbs:
            _log.debug('Trying %s.%s', predb.name, method_name)
            try:
                return await self._call(predb, method_name, *args, **kwargs)
            except (NotImplementedError, errors.RequestError) as e:
                _log.debug('Collecting exception: %r', e)
                exceptions.append(e)

        # All predbs are unreachable or don't have `method_name` implemented.
        self._raise(exceptions, method_name)

    async def _for_all_predbs(self, predbs, method_name, *args, **kwargs):
        # Call `method_name` on all predbs concurrently and yield the return
        # value or RequestError/NotImplementedError as they occur.
        method_calls = [
            asyncio.create_task(
                self._call(predb, method_name, *args, **kwargs)
            )
            for predb in predbs
        ]

        try:
            for coro in asyncio.as_completed(method_calls):
                try:
                    result = await coro
                except (NotImplementedError, errors.RequestError) as e:
                    yield e
                else:
                    yield result
        finally:
            # If our caller stops iterating over our yielded `result`s, we may
            # still have unfinished tasks that will continue to run in the
            # background. We cancel them here because
            #   1. nobody cares about their return values anymore
            #
            #   2. if one of the tasks raises an exception, asyncio will
            #      eventually complain about an unhandled exception. Cancelling
            #      the tasks seems to prevents that.
            #
            # NOTE: This is untested functionality because I couldn't reproduce
            #       this issue in a test case.
            for task in method_calls:
                task.cancel()

    @async_lru.alru_cache
    async def search(self, *args, **kwargs):
        """
        Search multiple predbs concurrently and return first non-empty results

        See :meth:`~.PredbApiBase.search`.
        """
        # Because srrdb always blocks search requests for a long time (~50 seconds), we don't use it
        # if we have alternatives. This is less accurate because some releases are only listed on
        # srrdb (see the commented-out tests in the same commit as this comment), but the long wait
        # times are too annoying.
        predbs = self._predbs
        if len(predbs) >= 2:
            predbs = tuple(
                predb for predb in predbs
                if predb.name != 'srrdb'
            )
        _log.debug('Searching predbs: %r', tuple(p.name for p in predbs))

        exceptions = []
        async for results in self._for_all_predbs(predbs, 'search', *args, **kwargs):
            if isinstance(results, Exception):
                exceptions.append(results)
            # Return non-empty search results or wait for next response
            elif results:
                return results

        if exceptions:
            # All predbs are unreachable or don't have `method_name` implemented.
            # Raise combined RequestErrors.
            self._raise(exceptions, method_name='search')
        else:
            # No search results
            return []

    @async_lru.alru_cache
    async def release_files(self, *args, **kwargs):
        """See :meth:`~.PredbApiBase.release_files`"""
        return await self._for_each_predb(self._predbs, 'release_files', *args, **kwargs)

    _nogroup_regexs = (
        re.compile(r'^$'),
        re.compile(r'^(?i:nogroup)$'),
        re.compile(r'^(?i:nogrp)$'),
    )

    @async_lru.alru_cache
    async def is_scene_release(self, release):
        """
        Return whether `release` is a scene release or not

        .. note:: A renamed or otherwise altered scene release is still
            considered a scene release.

        :param release: Release name, path to release

        :return: :class:`~.types.SceneCheckResult`
        """
        if isinstance(release, str):
            release_info = utils.release.ReleaseInfo(release)
        else:
            release_info = release

        # Empty group or names like "NOGROUP" are non-scene
        if (
            # Any NOGROUP-equivalent means it's not scene
            any(regex.search(release_info['group']) for regex in self._nogroup_regexs)

            # Abbreviated file names also have an empty group, but ReleaseInfo()
            # can pick up information from the parent directory and we can do a
            # successful search for that.
            and not utils.predbs.is_abbreviated_filename(release_info.path)
        ):
            return SceneCheckResult.false

        # We know at least `title` and `group`. If there are any search results,
        # it should be a scene release.
        results = await self.search(release)
        if results:
            return SceneCheckResult.true
        else:
            return SceneCheckResult.false

    async def verify_release_name(self, content_path, release_name):
        """
        Raise if release was renamed

        :param content_path: Path to release file or directory
        :param release_name: Known exact release name, e.g. from :meth:`search`
            results

        :raise SceneRenamedError: if release was renamed
        :raise SceneError: if `release_name` is not a scene release
        :raise NotImplementedError: if :meth:`release_files` raises it
        """
        content_path = content_path.strip(os.sep)
        _log.debug('Verifying release name: %r =? %r', content_path, release_name)

        # TODO: Rewrite this comment: We MUST first check if release_files() is implemented. If we check
        # is_scene_release() first and an incomplete predb wrongly reports "not
        # a scene release", MultiPredbApi can move on the next predb.
        files = await self.release_files(release_name)

        # TODO: Rewrite this comment: We check is_scene_release() a) because we can fail early before we do
        # all the work below and b) because we don't want to raise
        # SceneRenamedError below if this is not a scene release.
        if not await self.is_scene_release(release_name):
            raise errors.SceneError(f'Not a scene release: {release_name}')

        # Figure out which file is the actual payload. Note that the release may not
        # contain any files, e.g. Wrecked.2011.DiRFiX.LIMITED.FRENCH.720p.BluRay.X264-LOST.
        main_release_file = None
        if files:
            content_file_extension = utils.fs.file_extension(content_path)
            if content_file_extension:
                # `content_path` points to a file, not a directory
                content_file = utils.fs.basename(content_path)
                # Find the closest match in the released files
                # (`content_file` may have been renamed)
                filename_matches = difflib.get_close_matches(content_file, files)
                if filename_matches:
                    main_release_file = filename_matches[0]

            if not main_release_file and files:
                # Default to the largest file
                main_release_file = sorted(
                    (info for info in files.values()),
                    key=lambda info: info['size'],
                )[0]['file_name']

        # No files in this release, default to `release_name`
        if not main_release_file:
            main_release_file = release_name
        _log.debug('Main release file: %r', main_release_file)

        # Generate set of paths that are valid for this release
        acceptable_paths = {release_name}

        # Properly named directory that contains the released file. This covers
        # abbreviated files and all other files.
        for file in files:
            acceptable_paths.add(os.path.join(release_name, file))

        # Any non-abbreviated files may exist outside of a properly named parent
        # directory
        for file in files:
            if not utils.predbs.is_abbreviated_filename(file):
                acceptable_paths.add(file)

        # If `release_name` is an episode, it may be inside a season pack parent
        # directory. This only matters if we're dealing with an abbreviated file
        # name; normal file names are independent of their parent directory name.
        if utils.predbs.is_abbreviated_filename(content_path):
            season_pack_name = utils.predbs.common.get_season_pack_name(release_name)
            for file in files:
                acceptable_paths.add(f'{season_pack_name}/{file}')

        # Standalone file is also ok if it is named `release_name` with the same
        # file extension as the main file
        main_release_file_extension = utils.fs.file_extension(main_release_file)
        acceptable_paths.add(f'{release_name}.{main_release_file_extension}')

        # Release is correctly named if `content_path` ends with any acceptable path
        for path in (p.strip(os.sep) for p in acceptable_paths):
            if re.search(rf'(?:^|{re.escape(os.sep)}){re.escape(path)}$', content_path):
                return

        # All attempts to match `content_path` against `release_name` have failed.
        # Produce a useful error message.
        if utils.predbs.is_abbreviated_filename(content_path):
            # Abbreviated files should never be handled without a parent
            original_name = os.path.join(release_name, main_release_file)
        elif utils.fs.file_extension(content_path):
            # Assume `content_path` refers to a file, not a directory
            # NOTE: We can't use os.path.isdir(), `content_path` may not exist.
            original_name = main_release_file
        else:
            # Assume `content_path` refers to directory
            original_name = release_name

        # Use the same number of parent directories for original/existing path. If
        # original_name contains the parent directory, we also want the parent
        # directory in existing_name.
        original_name_parts_count = original_name.count(os.sep)
        content_path_parts = content_path.split(os.sep)
        existing_name = os.sep.join(content_path_parts[-original_name_parts_count - 1:])

        raise errors.SceneRenamedError(
            original_name=original_name,
            existing_name=existing_name,
        )

    async def verify_release_files(self, content_path, release_name):
        """
        Check if existing files have the correct size

        :param content_path: Path to release file or directory
        :param release_name: Known exact release name, e.g. from :meth:`search`
            results

        The return value is a sequence of :class:`~.errors.SceneError` exceptions:

            * :class:`~.errors.SceneFileSizeError` if a file has the wrong size
            * :class:`~.errors.SceneMissingInfoError` if the correct file size
              of file cannot be found
            * :class:`~.errors.SceneError` if `release_name` is not a scene release
        """
        exceptions = []

        # TODO: Rewrite this comment: We MUST first check if release_files() is implemented. If we check
        # is_scene_release() first and an incomplete predb wrongly reports "not
        # a scene release", MultiPredbApi can move on the next predb.
        fileinfos = await self.release_files(release_name)

        # TODO: Rewrite this comment: We check is_scene_release() a) because we can fail early before we do
        # all the work below and b) because we don't want to raise
        # SceneRenamedError below if this is not a scene release.
        if not await self.is_scene_release(release_name):
            exceptions.append(errors.SceneError(f'Not a scene release: {release_name}'))
        if exceptions:
            return tuple(exceptions)

        def get_release_filesize(filename):
            return fileinfos.get(filename, {}).get('size', None)

        # Map file paths to expected file sizes
        if os.path.isdir(content_path):
            # Map each file in content_path to its correct size
            exp_filesizes = {
                filepath: get_release_filesize(utils.fs.basename(filepath))
                for filepath in utils.fs.file_list(content_path)
            }

        # `content_path` is file
        elif len(fileinfos) == 1:
            # Original release is also a single file, but it may be in a directory
            filename = tuple(fileinfos)[0]
            exp_filesize = get_release_filesize(filename)
            exp_filesizes = {
                # Title.2015.720p.BluRay.x264-FOO.mkv
                content_path: exp_filesize,
                # Title.2015.720p.BluRay.x264-FOO/foo-title.mkv
                os.path.join(utils.fs.strip_extension(content_path), filename): exp_filesize,
            }
        else:
            # Original release is multiple files (e.g. Extras or Bonus)
            filename = utils.fs.basename(content_path)
            exp_filesizes = {content_path: get_release_filesize(filename)}

        # Compare expected file sizes to actual file sizes
        for filepath, exp_size in exp_filesizes.items():
            filename = utils.fs.basename(filepath)
            actual_size = utils.fs.file_size(filepath)
            _log.debug('Checking file size: %s: %r ?= %r', filename, actual_size, exp_size)
            if exp_size is None:
                _log.debug('No info: %s', filename)
                exceptions.append(errors.SceneMissingInfoError(filename))
            elif actual_size is not None:
                if actual_size != exp_size:
                    _log.debug('Wrong size: %s', filename)
                    exceptions.append(
                        errors.SceneFileSizeError(
                            filename=filename,
                            original_size=exp_size,
                            existing_size=actual_size,
                        )
                    )
                else:
                    _log.debug('Correct size: %s', filepath)
            else:
                _log.debug('No such file: %s', filepath)

        return tuple(e for e in exceptions if e)

    async def verify_release(self, content_path, release_name=None):
        """
        Find matching scene releases and apply :meth:`verify_release_name`
        and :meth:`verify_release_files`

        :param content_path: Path to release file or directory
        :param release_name: Known exact release name or `None` to
            :meth:`search` for `content_path`

        :return: :class:`~.types.SceneCheckResult` enum from
            :meth:`is_scene_release` and sequence of
            :class:`~.errors.SceneError` exceptions from
            :meth:`verify_release_name` and :meth:`verify_release_files`
        """
        # If we know the exact release name, this is easy.
        if release_name:
            return await self._verify_release(content_path, release_name)

        # Find possible `release_name` values. For season packs that were released
        # as single episodes, this will get us a sequence of episode release names.
        existing_release_names = await self.search(content_path)
        if not existing_release_names:
            return SceneCheckResult.false, ()

        # Maybe `content_path` was released by scene as it is (as file or directory)
        for existing_release_name in existing_release_names:
            is_scene_release, exceptions = await self._verify_release(content_path, existing_release_name)
            if is_scene_release and not exceptions:
                return SceneCheckResult.true, ()

        # Maybe `content_path` is a directory (season pack) and scene released
        # single files (episodes).
        return await self._verify_release_per_file(content_path)

    async def _verify_release(self, content_path, release_name):
        _log.debug('Verifying %r against release: %r', content_path, release_name)

        # Stop other checks if this is not a scene release
        is_scene = await self.is_scene_release(release_name)
        if is_scene in (SceneCheckResult.false, SceneCheckResult.unknown):
            return is_scene, ()

        # Combined exceptions from verify_release_name() and verify_release_files()
        exceptions = []

        # verify_release_name() can only produce one exception, so it is raised
        try:
            await self.verify_release_name(content_path, release_name)
        except errors.SceneError as e:
            exceptions.append(e)

        # verify_release_files() can produce multiple exceptions, so it returns them
        exceptions.extend(await self.verify_release_files(content_path, release_name))
        return is_scene, tuple(exceptions)

    async def _verify_release_per_file(self, content_path):
        _log.debug('Verifying each file beneath %r', content_path)
        is_scene_releases = []
        combined_exceptions = collections.defaultdict(list)
        filepaths = utils.fs.file_list(content_path, extensions=constants.VIDEO_FILE_EXTENSIONS)
        for filepath in filepaths:
            existing_release_names = await self.search(filepath)
            _log.debug('Search results for %r: %r', filepath, existing_release_names)

            # If there are no search results, default to "not a scene release"
            is_scene_release = SceneCheckResult.false

            # Match each existing_release_name against filepath
            for existing_release_name in existing_release_names:
                is_scene_release, exceptions = await self._verify_release(filepath, existing_release_name)
                _log.debug('Verified %r against %r: %r, %r',
                           filepath, existing_release_name, is_scene_release, exceptions)
                if is_scene_release and not exceptions:
                    # Match found, don't check other existing_release_names
                    break
                elif is_scene_release:
                    # Remember exceptions per file (makes debugging easier)
                    combined_exceptions[filepath].extend(exceptions)

            # Remember the SceneCheckResult when the for loop ended. True if we
            # found a scene release at any point, other it's the value of the last
            # existing_release_name.
            is_scene_releases.append(is_scene_release)

        # Collapse `is_scene_releases` into a single value
        if is_scene_releases and all(isr is SceneCheckResult.true for isr in is_scene_releases):
            _log.debug('All files are scene releases')
            is_scene_release = SceneCheckResult.true
        elif is_scene_releases and all(isr is SceneCheckResult.false for isr in is_scene_releases):
            _log.debug('All files are non-scene releases')
            is_scene_release = SceneCheckResult.false
        else:
            _log.debug('Uncertain scene status: %r', is_scene_releases)
            is_scene_release = SceneCheckResult.unknown

        return is_scene_release, tuple(
            exception
            for exceptions in combined_exceptions.values()
            for exception in exceptions
        )
