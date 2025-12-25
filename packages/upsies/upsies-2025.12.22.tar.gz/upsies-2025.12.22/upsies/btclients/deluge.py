import aiobtclientapi

from . import base, fields


class DelugeBtclientConfig(base.BtclientConfig):
    name: fields.name = aiobtclientapi.DelugeAPI.name
    label: fields.label = aiobtclientapi.DelugeAPI.label
    client: fields.client = aiobtclientapi.DelugeAPI.name

    url: fields.url(aiobtclientapi.DelugeAPI)
    username: fields.username
    password: fields.password
    translate_path: fields.translate_path
    check_after_add: fields.check_after_add


class DelugeBtclient(base.Btclient):
    Config = DelugeBtclientConfig
