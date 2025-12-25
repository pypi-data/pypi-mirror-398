import typing

import aiobtclientapi
import pydantic

from .. import utils

KNOWN_CLIENT_NAMES = aiobtclientapi.client_names()


_ClientNameChoice = utils.types.Choice(
    options=KNOWN_CLIENT_NAMES,
    case_sensitive=False,
    empty_ok=True,
)


client = utils.config.fields.custom(
    cls=_ClientNameChoice,
    default='',
    description=(
        'BitTorrent client name\n'
        'Supported clients: ' + ', '.join(_ClientNameChoice.options)
    ),
)


name = typing.Annotated[
    typing.ClassVar[str],
    # `frozen=True` seems to have no effect. You can set `MyClass.name = "whatever"` without
    # exception. Not sure if this is a bug in pydantic or my thoughts.
    pydantic.Field(frozen=True),
]
"""Name of BitTorrent client that is used for comparison with :var:`client`"""


label = typing.Annotated[
    typing.ClassVar[str],
    pydantic.Field(frozen=True),
]
"""Official BitTorrent client name used in documentation, error messages, etc"""


def url(api):
    """
    Return :class:`~.typing.Annotated` ``api.url``

    :param api: :class:`aiobtclientapi.APIBase` subclass
    """
    return utils.config.fields.custom(
        cls=api.URL,
        default=api.URL.default,
        description=f'URL of the {api.label} RPC interface',
    )


username = utils.config.fields.string(
    default='',
    description='Username for authentication',
)


password = utils.config.fields.string(
    default='',
    secret=True,
    description='Password for authentication',
)


check_after_add = utils.config.fields.boolean(
    default='no',
    description='Whether added torrents should be hash checked',
)


translate_path = utils.config.fields.custom(
    cls=utils.types.PathTranslations,
    default=(
        # 'foo -> bar',
        # 'this -> that',
    ),
    description=(
        'Translate absolute paths on the computer that is running {__project_name__} (LOCAL) '
        'to paths on the computer that is running {config["label"]} (REMOTE)\n'
        'This is a list where LOCAL and REMOTE are separated by "->". Spaces are trimmed. '
        'When adding a torrent, LOCAL in the content path is replaced with REMOTE to get '
        "the path where the BitTorrent client can find the torrent's files.\n"
        'Paths that start with "X:" (where "X" is any ASCII letter) are Windows '
        'paths. Translated paths always use the REMOTE flavour so that a LOCAL POSIX path can '
        'be translated to a REMOTE Windows path and vice versa.\n'
        'With the examples below, "/mnt/d/things/stuff" translates to "d:\\things\\stuff".'
        'Example:\n'
        'clients.{config["client"]}.translate_path =\n'
        '  /home/me/My Projects -> /storage/seed_forever\n'
        '  /media/me/USB/ -> /storage/seed_temporarily\n'
        '  /mnt/d -> d:\\\n'
    ),
)
