import aiobtclientapi

from . import base, fields


class TransmissionBtclientConfig(base.BtclientConfig):
    name: fields.name = aiobtclientapi.TransmissionAPI.name
    label: fields.label = aiobtclientapi.TransmissionAPI.label
    client: fields.client = aiobtclientapi.TransmissionAPI.name

    url: fields.url(aiobtclientapi.TransmissionAPI)
    username: fields.username
    password: fields.password
    translate_path: fields.translate_path


class TransmissionBtclient(base.Btclient):
    Config = TransmissionBtclientConfig
