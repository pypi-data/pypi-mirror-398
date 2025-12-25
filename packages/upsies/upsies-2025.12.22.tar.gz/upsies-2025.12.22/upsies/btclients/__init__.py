from .base import Btclient, BtclientConfig, BtclientsConfig, GenericBtclientConfig
from .deluge import DelugeBtclient
from .qbittorrent import QbittorrentBtclient
from .rtorrent import RtorrentBtclient
from .transmission import TransmissionBtclient


def client_names():
    r"""Return sequence of valid :class:`~.Btclient.name`\ s"""
    return tuple(
        cls.name
        for cls in Btclient.__subclasses__()
    )
