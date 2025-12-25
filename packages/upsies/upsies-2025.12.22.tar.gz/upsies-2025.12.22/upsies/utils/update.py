"""
Find most recent version
"""

import re

from packaging.version import parse as parse_version

from .. import __changelog__, __project_name__, __version__, utils
from . import http

import logging  # isort:skip
_log = logging.getLogger(__name__)

natsort = utils.LazyModule(module='natsort', namespace=globals())


_PYPI_URL = f'https://pypi.org/pypi/{__project_name__}/json'
_REPO_URL = (
    'https://codeberg.org/plotski/'
    f'{__project_name__}/raw/branch/master/{__project_name__}/__init__.py'
)
_MAX_CACHE_AGE = 24 * 3600  # 24 hours
_REQUEST_TIMEOUT = 30


def current_is_prerelease():
    """Whether the currently running release is a prerelease"""
    current = parse_version(__version__)
    return current.is_prerelease


async def get_newer_release():
    """
    Return version of newer release than :attr:`upsies.__version__`

    If there is no newer release, return an empty :class:`str`.

    :raise RequestError: if getting the latest version fails
    """
    current = __version__
    release = await _get_latest_release()
    if parse_version(release) > parse_version(current):
        return release


async def get_newer_prerelease():
    current = __version__
    release = await _get_latest_prerelease()
    if parse_version(release) > parse_version(current):
        return release

    # If there is no newer prerelease, a proper release could've been made after the prerelease we
    # are currently running. We must do a normal release check as well to detect that.
    return await get_newer_release()


async def _get_latest_release():
    response = await http.get(
        url=_PYPI_URL,
        timeout=_REQUEST_TIMEOUT,
        cache=True,
        max_cache_age=_MAX_CACHE_AGE,
    )
    all_versions = natsort.natsorted(response.json()['releases'])
    # PyPI should return the releases sorted by release date (latest last)
    if all_versions:
        return _fix_version(all_versions[-1])


async def _get_latest_prerelease():
    response = await http.get(
        url=_REPO_URL,
        timeout=_REQUEST_TIMEOUT,
        cache=True,
        max_cache_age=_MAX_CACHE_AGE,
    )
    match = re.search(r'^__version__\s*=\s*[\'"]([\w\.]+)[\'"]', response, flags=re.MULTILINE)
    if match:
        return match.group(1)


def _fix_version(version):
    # Python's version parser removes leading zeros from our non-standard date version.
    # We re-add it here for prettification.
    match = re.search(r'^(\d{4})\.(\d+)\.(\d+)(.*)$', version)
    if match:
        year, month, day, pre = match.groups()
        version = f'{year}.{month:0>2}.{day:0>2}{pre}'
    return version


async def get_latest_release_changelog():
    """
    Return changes of the most recent proper release as multiline :class:`str`

    If no proper release can be found, return an empty :class:`str`.

    :raise RequestError: if getting the changelog fails
    """
    changelogs = await _get_recent_changelogs()
    # Find most recent changelog with proper version.
    for version, changelog in changelogs:
        if re.search(r'^\d{4}\.\d+\.\d+$', version):
            return changelog
    return ''


async def get_latest_changelog():
    """Same as :func:`get_latest_release_changelog`, but do not ignore prerelease"""
    changelogs = await _get_recent_changelogs()
    # Always return the first entry if it exists.
    if changelogs:
        return changelogs[0][1]
    else:
        return ''


async def _get_recent_changelogs():
    response = await http.get(
        url=__changelog__,
        timeout=_REQUEST_TIMEOUT,
        cache=True,
        max_cache_age=_MAX_CACHE_AGE,
    )

    version_regex = r'^(\d{4}\..{1,2}\..{1,2})'
    changelogs = []
    for i, changelog in enumerate(re.split(r'\n{2,}', response)):
        # We don't care about old changes.
        if i >= 2:
            break

        if match := re.search(version_regex, changelog, flags=re.MULTILINE):
            version = match.group(1)
            changes = re.sub(version_regex + '.*?\n', r'', changelog, flags=re.MULTILINE).rstrip()
            changelogs.append((version, changes))

    return tuple(changelogs)
