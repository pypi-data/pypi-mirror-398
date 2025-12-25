import aiobtclientapi
import aiobtclientrpc

from .. import errors, utils
from . import base, fields


class QbittorrentBtclientConfig(base.BtclientConfig):
    name: fields.name = aiobtclientapi.QbittorrentAPI.name
    label: fields.label = aiobtclientapi.QbittorrentAPI.label
    client: fields.client = aiobtclientapi.QbittorrentAPI.name

    url: fields.url(aiobtclientapi.QbittorrentAPI)
    username: fields.username
    password: fields.password
    translate_path: fields.translate_path
    check_after_add: fields.check_after_add
    category: utils.config.fields.string(
        default='',
        description='qBittorrent category to add torrents to',
    )


class QbittorrentBtclient(base.Btclient):
    Config = QbittorrentBtclientConfig

    async def add_torrent(self, *args, **kwargs):
        infohash = await super().add_torrent(*args, **kwargs)

        if 'category' in self._config:
            await self._set_category(infohash, self._config['category'])

        return infohash

    async def _set_category(self, infohash, category):
        try:
            await self._api.call(
                'torrents/setCategory',
                hashes=infohash,
                category=category,
            )
        except aiobtclientrpc.RPCError as e:
            if 'incorrect category name' in str(e).lower():
                raise errors.TorrentAddError(f'Unknown category: {category}') from e
            else:
                raise e
