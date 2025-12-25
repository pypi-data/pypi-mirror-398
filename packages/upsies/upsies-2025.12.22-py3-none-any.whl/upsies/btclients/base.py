import abc
import collections
import typing

import aiobtclientapi
import pydantic

from .. import errors, utils
from . import fields

import logging  # isort:skip
_log = logging.getLogger(__name__)


class _GetConfigAttribute:
    """Get ``name`` and ``label`` from :attr:`~.Btclient.Config`"""

    def __init__(self, attribute_name):
        self.attribute_name = attribute_name

    def __get__(self, obj, objtype):
        return getattr(objtype.Config, self.attribute_name)


class Btclient:
    """
    Base class for BitTorrent client APIs

    This is a wrapper around a :class:`aiobtclientapi.APIBase` subclass.

    :param config: :class:`~.BtclientConfig` instance
    """

    @abc.abstractmethod
    def Config(self):
        """:class:`~.BtclientConfig` subclass that must be set by subclasses"""

    @classmethod
    def from_config(cls, config):
        """
        Return subclass instance where :attr:`name` matches ``config["client"]``

        :raise ConfigError: if no match is found
        """
        # Find subclass by matching "client" against each subclass' "name" attribute.
        config_client = config['client']
        for subcls in Btclient.__subclasses__():
            if config_client == subcls.name:
                return subcls(config)

        raise errors.ConfigError('No client specified')

    name = _GetConfigAttribute('name')
    """
    Name of the client (in configuration files and internal use)

    See :attr:`~.BtclientConfig.client`.
    """

    label = _GetConfigAttribute('label')
    """
    Official name of the client (e.g. in documentation)

    See :attr:`~.BtclientConfig.label`.
    """

    @classmethod
    def client_names(cls):
        """Sequence of :attr:`name` values of subclasses"""
        return fields.KNOWN_CLIENT_NAMES

    def __init__(self, config):
        assert isinstance(config, self.Config), f'Not a {self.Config.__name__}: {config!r}'
        self._config = config
        self._api = aiobtclientapi.api(
            name=config['client'],
            url=config['url'],
            username=config['username'],
            password=config['password'].get_secret_value(),
        )

    def __repr__(self):
        return f'{type(self).__name__}({self._config!r})'

    async def add_torrent(self, torrent, *, download_path=None):
        """
        Add `torrent` to client

        :param torrent: ``.torrent`` file/URL, magnet link or infohash
        :param download_path: Where the files in `torrent` can be found or should be downloaded to
        """
        _log.debug('Adding %s to %s at %r with config=%s', torrent, self.name, download_path, self._config)
        response = await self._api.add(
            torrent,
            location=download_path,
            # Note that "check_after_add" option is not supported by all clients.
            verify=self._config.get('check_after_add', False),
        )

        # Raise first error.
        for error in response.errors:
            raise errors.TorrentAddError(error)

        # Return first infohash of first added (or already added) torrent.
        added = (response.added + response.already_added)
        if added:
            return added[0]

        raise RuntimeError(f'Failed to add torrent: {torrent}')


class BtclientConfig(utils.config.SubsectionBase):
    """
    Bittorrent client configuration base class
    """

    # Immutable class attribute that identifies the BitTorrent client (e.g. "qbittorrent", "deluge",
    # etc). Must be specified by subclass.
    name: fields.name

    # Same as `name`, but mutable and stored on the instance. This is used to derive a subclass.
    client: fields.client

    # Proper name of the BitTorrent client (e.g. "qBittorrent", "Deluge", etc).
    # Must be specified by subclass.
    label: fields.label

    def __new__(cls, **kwargs):
        # Get the actual class we want to instantiate.
        guessed_cls = cls.guess_subclass(kwargs)
        self = super().__new__(guessed_cls)

        if not issubclass(guessed_cls, cls):
            # __init__() is only called automatically if we return an instance of `cls`, which is
            # not the case if, for example, we guessed `QbittorrentBtclientConfig` from
            # `GenericBtclientConfig`.
            self.__init__(**kwargs)

        return self

    @classmethod
    def guess_subclass(cls, kwargs):
        """Return correct subclass based on "client" option in `kwargs` or :attr:`name`"""
        # Do not guess the correct subclass if this is a `*Defaults` class (see
        # `ConfigDictBase.defaults`).
        if cls.__name__.endswith('Defaults'):
            return cls

        def get_client_name(subcls, kws=None):
            # Get client name from keyword arguments. Keyword arguments always take precedence over
            # the class attribute so we can do `DelugeBtclientConfig(client="transmission")` to get
            # a `TransmissionBtclientConfig` instance. This is ugly, but it's necessary to allow the
            # user to change the "client" option without editing the config file.
            client_name = None
            if kws:
                client_name = kws.get('client', None)

            if not client_name:
                # Get client name from class attribute.
                client_name = getattr(subcls, 'name', None)

            return client_name

        wanted_client_name = get_client_name(cls, kwargs)
        subclses = BtclientConfig.__subclasses__()
        for subcls in subclses:
            subcls_client_name = get_client_name(subcls)
            if wanted_client_name == subcls_client_name:
                return subcls

        return GenericBtclientConfig

    def convert(self):
        """
        Return different :class:`BtclientConfig` instance based on "client" field

        Return `None` if not proper subclass can be determined (i.e. the determined subclass is
        :class:`GenericBtclientConfig`) or if the "client" field has its default value.

        For example:

        >>> c1 = DelugeBtclientConfig()
        >>> isinstance(c1, DelugeBtclientConfig)
        True
        >>> c1["client"] = 'transmission'
        >>> c2 = c1.convert()
        >>> isinstance(c2, TransmissionBtclientConfig)
        True
        >>> c1["client"] = 'deluge'
        >>> c1.convert() is None
        True
        """
        subclass = self.guess_subclass(dict(self))
        if (
                subclass is not GenericBtclientConfig
                and self['client'] != self.defaults['client']
        ):
            known_fields = set(subclass.__pydantic_fields__)
            kwargs = {
                key: value
                for key, value in self.items()
                if (
                        # Subclass knows what to do with `key`, e.g. "category" is only implemented
                        # for QbittorrentBtclientConfig, so we ignore it when converting to another
                        # client.
                        key in known_fields
                        # Do not pass our default values to the new subclass. It may have its own
                        # default for `key`.
                        and value != self.defaults[key]
                )
            }
            try:
                return subclass(**kwargs)
            except pydantic.ValidationError as e:
                raise self._value_error(e) from e

    def as_ini(self, *, client_id, include_defaults=False, comment_defaults=True):
        return '\n'.join(self._as_ini(
            client_id=client_id,
            include_defaults=include_defaults,
            comment_defaults=comment_defaults,
        ))

    def _as_ini(self, *, client_id, include_defaults=False, comment_defaults=True):
        # Always specify "client" option in case user wants to customize the client ID (i.e. section
        # name). Comment out the "client" option if the client ID is already customized.
        yield from self._as_ini_option_lines(
            'client',
            include_default=True,
            comment_default=client_id == type(self).name,
        )
        for option in self:
            if option != 'client':
                yield from self._as_ini_option_lines(
                    option,
                    include_default=include_defaults,
                    comment_default=comment_defaults,
                )


class GenericBtclientConfig(BtclientConfig):
    """
    Dummy :class:`BtclientConfig` that can be converted to a proper implementation

    Converting to a propery implementation is done by setting the "client" field and calling
    :meth:`~.BtclientConfig.convert`.
    """

    name: fields.name = ''
    client: fields.client = ''
    label: fields.label = ''


def _validate_client_config(cfg):
    if isinstance(cfg, BtclientConfig):
        return cfg
    elif isinstance(cfg, collections.abc.Mapping):
        # This will get us a `DelugeBtclientConfig` if `cfg["client"] == "deluge"` and default to
        # `GenericBtclientConfig`.
        return BtclientConfig(**cfg)
    else:
        raise TypeError(f'Not a {BtclientConfig.__name__} or Mapping: {type(cfg).__name__}: {cfg!r}')


class BtclientsConfig(utils.config.SectionBase, extra='allow'):
    """
    Map client IDs (:class:`str`) to :class:`~.BtclientConfig` instances

    From a user perspective, a client ID is a section name in "clients.ini", e.g. "[qbittorrent]",
    "[nas]" or "[seedbox]".

    Client IDs are arbitrary strings specified by the user. If a client ID is a valid
    :attr:`.Btclient.name`, it is used to derive the proper subclass from that, e.g. a section named
    "[qbitorrent]" in the INI file will result in a :class:`QbittorrentBtclientConfig` instance
    because :class:`QbittorrentBtclientConfig.name` is "qbittorrent".
    """

    __pydantic_extra__: dict[
        str,
        typing.Annotated[
            BtclientConfig,
            pydantic.BeforeValidator(_validate_client_config),
        ]
    ]

    def __init__(self, **kwargs):
        # If no "client" is specified, use the section name (e.g. "[deluge]" -> client="deluge").
        # The "client" field is used to derive a subclass, e.g. `DelugeBtclientConfig`.
        for section_name, section in kwargs.items():
            if (
                    'client' not in section
                    and section_name in Btclient.client_names()
            ):
                section['client'] = section_name
        super().__init__(**kwargs)

    def __getitem__(self, key):
        try:
            cfg = super().__getitem__(key)

        except errors.UnknownSubsectionConfigError:
            # Client IDs are arbitrary strings, so we can create them on demand.
            if key in Btclient.client_names():
                cfg = BtclientConfig(client=key)
            else:
                cfg = BtclientConfig()
            self[key] = cfg
            return cfg

        else:
            # If "client" is different from its default value, we have to convert, e.g. from
            # DelugeBtclientConfig to TransmissionBtclientConfig.
            if cfg['client'] != cfg.defaults['client']:
                try:
                    cfg_converted = cfg.convert()
                except errors.ConfigValueError as e:
                    # Conversion failed, e.g. because an option that is valid for
                    # TransmissionBtclientConfig is not valid for DelugeBtclientConfig.
                    raise errors.ConfigValueError(e.message, path=(key, *e.path)) from None
                else:
                    # If `cfg_converted` is `None`, conversion is not possible, e.g. because
                    # "client" option is not provided.
                    if cfg_converted is not None:
                        self[key] = cfg = cfg_converted
                    else:
                        # This should never happen because "client" cannot have any value that isn't
                        # a valid `Btname`. But convert() can return `None` in theory, so we raise
                        # RuntimeError for easier debugging if that happens.
                        raise RuntimeError(f'Not enough information to convert: {cfg!r}')

            return cfg

    @classmethod
    def get_defaults(cls):
        """
        Yield 2-tuples of `client_id` (:class:`str`) and :class:`~.BtclientConfig` subclasses

        We want the default instance of this class to be empty (no clients specified), but we also
        want :attr:`~.ConfigDictBase.defaults` to provide all available implementations (e.g. for
        documentation). This method gives us the latter. See also :class:`~._CreateDefaults`.
        """
        for subcls in Btclient.__subclasses__():
            yield subcls.Config.name, subcls.Config

    def as_ini(self, *, include_defaults=False):
        """Return section in INI file format"""
        # Custom client IDs.
        subsections = tuple(self)
        # Default client IDs.
        subsections += tuple(
            subsection
            for subsection in self.defaults
            if subsection not in subsections
        )
        parts = []
        for subsection in subsections:
            parts.extend(self._as_ini(subsection, include_defaults=include_defaults))
        return '\n'.join(parts).strip()

    def _as_ini(self, subsection, *, include_defaults):
        lines = self[subsection].as_ini(client_id=subsection, include_defaults=include_defaults).splitlines()
        if lines:
            if all(line.strip().startswith('#') for line in lines):
                yield f'# [{subsection}]'
            else:
                yield f'[{subsection}]'
            yield from lines
            yield ''

    def get_comment(self):
        return (
            'Section names in this file may be arbitrary strings (except for newlines, null bytes '
            'and other funny business). They are used to identify different client instances upsies '
            'can add torrents to.'
            '\n\n'
            'You may omit setting the `client` option if the section name is one of the supported '
            'clients: ' + ', '.join(name for name in Btclient.client_names())
            + '\n\n'
            'For example, you can set `trackers.*.add_to = foo` if this section exists:\n'
            '\n'
            '    [foo]\n'
            '    client = deluge\n'
            '    url = localhost:1234\n'
            '\n'
            'Or you can set `trackers.*.add_to = deluge` with this section:\n'
            '\n'
            '    [deluge]\n'
            '    url = localhost:1234\n'
            '\n'
        )
