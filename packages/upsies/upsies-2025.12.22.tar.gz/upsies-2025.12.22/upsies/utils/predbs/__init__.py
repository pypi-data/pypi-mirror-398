"""
Scene release search and verification
"""

from ... import utils
from .. import release
from ..types import SceneCheckResult
from . import corruptnet, predbclub, predbnet, predbovh, srrdb
from .base import PredbApiBase
from .common import assert_not_abbreviated_filename, is_abbreviated_filename, is_mixed_season_pack
from .multi import MultiPredbApi
from .query import SceneQuery


def predbs():
    """Return list of :class:`~.PredbApiBase` subclasses"""
    return utils.subclasses(PredbApiBase, utils.submodules(__package__))


def predb(name, config=None):
    """
    Create :class:`~.PredbApiBase` instance

    :param str name: Name of the scene release database. A subclass of
        :class:`~.PredbApiBase` with the same :attr:`~.PredbApiBase.name`
        must exist in one of this package's submodules.
    :param dict config: User configuration passed to the subclass specified by
        `name`

    :raise ValueError: if no matching subclass can be found

    :return: :class:`~.PredbApiBase` instance
    """
    for predb in predbs():
        if predb.name == name:
            return predb(config=config)
    raise ValueError(f'Unsupported scene release database: {name}')


def predb_names():
    """Return sequence of valid `name` arguments for :func:`.predb`"""
    return sorted(utils.string.CaseInsensitiveString(cls.name) for cls in predbs())
