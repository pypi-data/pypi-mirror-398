"""
API for trackers

:class:`~.TrackerBase` provides a uniform interface for all trackers. Its subclasses have two main
purposes:

1. Specify jobs that generate metadata, e.g. torrent creation, ``mediainfo`` output, IMDb ID, etc.

2. Provide coroutine methods, e.g. for uploading the generated metadata.
"""

import pydantic

from .. import errors, trackers, utils
from .base import TrackerBase, TrackerConfigBase, TrackerJobsBase, rules


def tracker_classes():
    """Return list of :class:`.TrackerBase` subclasses"""
    return utils.subclasses(TrackerBase, utils.submodules(__package__))


def tracker(name, **kwargs):
    """
    Create :class:`.TrackerBase` instance

    :param str name: Name of the tracker. A subclass of :class:`.TrackerBase`
        with the same :attr:`~.TrackerBase.name` must exist in one of this
        package's submodules.
    :param kwargs: All keyword arguments are passed to the subclass specified by
        `name`

    :raise ValueError: if no matching subclass can be found

    :return: :class:`.TrackerBase` instance
    """
    for cls in tracker_classes():
        if cls.name == name:
            return cls(**kwargs)
    raise ValueError(f'Unsupported tracker: {name}')


def tracker_names():
    """Return sequence of valid `name` arguments for :func:`.tracker`"""
    return sorted(utils.string.CaseInsensitiveString(cls.name) for cls in tracker_classes())


def _trackers_config_fields():
    """
    Return :class:`dict` that maps field names (:attr:`.TrackerBase.name`) to
    `(<TrackerConfigBase subclass>, <TrackerConfigBase instance>)` tuples
    """
    clses = sorted(
        tracker_classes(),
        key=lambda cls: cls.name,
    )
    return {
        cls.name: (cls.TrackerConfig, cls.TrackerConfig())
        for cls in clses
    }


class _TrackersConfig(utils.config.SectionBase):
    def validate_config(self, config):
        known_clients = set(config['clients'])
        known_clients.update(config['clients'].defaults)
        for tracker_name, tracker_config in self.items():
            add_to = tracker_config['add_to']
            if add_to and add_to not in known_clients:
                raise errors.ConfigValueError(f'No such client: {add_to}', path=('trackers', tracker_name, 'add_to'))


TrackersConfig = pydantic.create_model(
    'TrackersConfig',
    **_trackers_config_fields(),
    __base__=_TrackersConfig,
)
