"""
Fixed values that do not change during runtime
"""

import os

from xdg.BaseDirectory import xdg_cache_home as XDG_CACHE_HOME
from xdg.BaseDirectory import xdg_config_home as XDG_CONFIG_HOME

from . import __project_name__

DEFAULT_CACHE_DIRECTORY = os.path.join(XDG_CACHE_HOME, __project_name__)
"""Default path cache directory if config option ``cache_directory`` is not set"""

GENERIC_TORRENTS_DIRPATH = os.path.join(DEFAULT_CACHE_DIRECTORY, 'generic_torrents')
"""Path to directory that contains cached torrents for re-using piece hashes"""

CONFIG_DIRECTORYPATH = os.path.join(XDG_CONFIG_HOME, __project_name__)
"""Path to configuration directory"""

CONFIG_FILEPATH = os.path.join(CONFIG_DIRECTORYPATH, 'config.ini')
"""Path to general configuration file"""

TRACKERS_FILEPATH = os.path.join(CONFIG_DIRECTORYPATH, 'trackers.ini')
"""Path to trackers configuration file"""

IMGHOSTS_FILEPATH = os.path.join(CONFIG_DIRECTORYPATH, 'imghosts.ini')
"""Path to image hosting services configuration file"""

CLIENTS_FILEPATH = os.path.join(CONFIG_DIRECTORYPATH, 'clients.ini')
"""Path to BitTorrent clients configuration file"""

VIDEO_FILE_EXTENSIONS = (
    'avi',
    'divx',
    'm2ts',
    'mkv',
    'mp4',
    'mpeg',
    'mpg',
    'mts',
    'ts',
    'vob',
    'wmv',
)
"""Sequence of file extensions to recognize video files"""

GUESSIT_OPTIONS = {
    'expected_title': [
        'The Collector',
        'xXx',
        'TC 2000',
    ],
    'advanced_config': {
    },
}
"""`options` argument for :meth:`.GuessItApi.guessit`"""
