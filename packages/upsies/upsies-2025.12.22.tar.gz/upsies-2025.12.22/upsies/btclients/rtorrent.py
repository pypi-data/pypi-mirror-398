import aiobtclientapi

from . import base, fields


class RtorrentBtclientConfig(base.BtclientConfig):
    name: fields.name = aiobtclientapi.RtorrentAPI.name
    label: fields.label = aiobtclientapi.RtorrentAPI.label
    client: fields.client = aiobtclientapi.RtorrentAPI.name

    url: fields.url(aiobtclientapi.RtorrentAPI)
    username: fields.username
    password: fields.password
    translate_path: fields.translate_path
    check_after_add: fields.check_after_add


class RtorrentBtclient(base.Btclient):
    Config = RtorrentBtclientConfig
