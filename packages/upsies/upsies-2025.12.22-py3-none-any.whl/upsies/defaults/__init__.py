from .. import btclients, imagehosts, utils
from .. import trackers as trackers_module
from .config import ConfigConfig


class Config(utils.config.ConfigBase):
    config: ConfigConfig = ConfigConfig()
    clients: btclients.BtclientsConfig = btclients.BtclientsConfig()
    imghosts: imagehosts.ImagehostsConfig = imagehosts.ImagehostsConfig()
    trackers: trackers_module.TrackersConfig = trackers_module.TrackersConfig()
