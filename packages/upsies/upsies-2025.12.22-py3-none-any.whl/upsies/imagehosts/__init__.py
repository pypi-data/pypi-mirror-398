"""
API for image hosting services
"""

import pydantic

from .. import utils
from .base import ImagehostBase, ImagehostConfigBase
from .common import UploadedImage


def imagehost_classes():
    """Return list of :class:`.ImagehostBase` subclasses"""
    return utils.subclasses(ImagehostBase, utils.submodules(__package__))


def imagehost(name, config=None, cache_directory=None):
    """
    Create :class:`.ImagehostBase` instance

    :param str name: Name of the image hosting service. A subclass of
        :class:`.ImagehostBase` with the same :attr:`~.ImagehostBase.name` must
        exist in one of this package's submodules.
    :param config: User configuration passed to the subclass specified by `name`
    :param cache_directory: Where to cache URLs of uploaded images or `None` to
        use :attr:`~upsies.constants.DEFAULT_CACHE_DIRECTORY`.

    :raise ValueError: if no matching subclass can be found

    :return: :class:`.ImagehostBase` instance
    """
    for cls in imagehost_classes():
        if cls.name == name:
            return cls(
                config=config or {},
                cache_directory=cache_directory,
            )
    raise ValueError(f'Unsupported image hosting service: {name}')


def imagehost_names():
    """Return sequence of valid `name` arguments for :func:`imagehost`"""
    return sorted(utils.string.CaseInsensitiveString(cls.name) for cls in imagehost_classes())


def _imagehost_config_fields():
    """
    Return :class:`dict` that maps field names (:attr:`.ImagehostBase.name`) to
    `(<ImagehostConfigBase subclass>, <ImagehostConfigBase instance>)` tuples
    """
    clses = sorted(
        imagehost_classes(),
        key=lambda cls: cls.name,
    )
    return {
        cls.name: (cls.Config, cls.Config())
        for cls in clses
    }

ImagehostsConfig = pydantic.create_model(
    'ImagehostsConfig',
    **_imagehost_config_fields(),
    __base__=utils.config.SectionBase,
)
