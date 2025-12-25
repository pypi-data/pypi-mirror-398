"""
Base classes for configuration models
"""

import collections
import configparser
import functools
import os
import textwrap
import typing

import pydantic

from ... import __project_name__, errors, utils
from .. import string

import logging  # isort:skip
_log = logging.getLogger(__name__)


class _CreateDefaults:
    """
    Descriptor class that provides a cached instance of the parent class

    The parent class is called without arguments, so it should provide only default values.

    The instance is made immutable by setting :attr:`~.pydantic.BaseModel.model_config` to
    ``{"frozen": True}``.

    If the class has also a method called `get_defaults`, it must provide ``(field_name, cls)``
    tuples. `cls` is called without arguments to create the default instance for the field called
    `field_name`.

    >>> class Foo:
    >>>     defaults: ClassVar = _CreateDefaults()
    >>> Foo.defaults
    <immutable instance of Foo>

    >>> Foo.defaults["foo"] = "bar"
    <Exception: Instance is frozen>
    """

    def __set_name__(self, objtype, name):
        self.attribute_name = name

    def __get__(self, obj, objtype):
        # Create special immutable subclass of `objtype` that provides default values.
        DefaultsSubclass = self._create_defaults_subclass(objtype)

        # Store defaults instance on the same attribute that this _CreateDefaults() instance was
        # stored on. This replaces _CreateDefaults() (which is no longer needed) and makes lookup of
        # `objtype.defaults` as fast as possible.
        setattr(objtype, self.attribute_name, DefaultsSubclass())

        # Do a quick sanity check.
        assert type(objtype.defaults).__name__ == f'{objtype.__name__}Defaults', \
            f'Expected {objtype.__name__}Defaults, not {type(objtype.defaults).__name__}'
        return objtype.defaults

    @classmethod
    def _create_defaults_subclass(cls, objtype):
        clsname = f'{objtype.__name__}Defaults'
        bases = (objtype,)
        attrs = {
            # This makes the subclass immutable. `objtype.model_config` should be automatically
            # copied for our *Defaults subclass, only overloading `frozen=True`.
            'model_config': pydantic.ConfigDict(frozen=True),
            '__annotations__': {},
        }

        try:
            # Get function that provides `(field_name, cls)` pairs from the class this descriptor
            # was created for.
            get_defaults = objtype.get_defaults
        except AttributeError:
            # Default implementation of get_defaults().
            def get_defaults():
                for field_name, field_info in objtype.__pydantic_fields__.items():
                    cls = field_info.annotation
                    yield field_name, cls

        for field_name, typ in get_defaults():
            if isinstance(typ, type) and issubclass(typ, ConfigDictBase):
                # Handle nested key-value map.
                typ_defaults = typ.defaults
                attrs[field_name] = typ_defaults
                attrs['__annotations__'][field_name] = type(typ_defaults)

        return type(clsname, bases, attrs)


class ConfigDictBase(collections.abc.MutableMapping, pydantic.BaseModel):
    """
    :class:`pydantic.BaseModel` that provides dictionary field access
    """

    model_config = pydantic.ConfigDict(
        arbitrary_types_allowed=True,
        extra='forbid',
        validate_assignment=True,
        validate_default=True,
    )

    def __getitem__(self, key):
        # Because attributes can't contain "-", we translate "-" to "_".
        valid_key = key.replace('-', '_')
        try:
            return getattr(self, valid_key)
        except AttributeError as e:
            raise KeyError(key) from e

    def __setitem__(self, key, value):
        # Because attributes can't contain "-", we translate "-" to "_".
        valid_key = key.replace('-', '_')
        try:
            setattr(self, valid_key, value)
        except pydantic.ValidationError as e:
            # NOTE: Pydantic raises ValidationError instead of KeyError if we try to set a
            #       non-existing attribute. We translate that to a KeyError here.
            for error in e.errors():
                if error['type'] == 'no_such_attribute':
                    raise KeyError(key) from e
            raise self._value_error(e) from e

    def __delitem__(self, key):
        raise RuntimeError(f'Keys cannot be removed from {type(self).__name__}: {key!r}: {self!r}')

    def _iter_all_fields(self):
        # `__pydantic_fields__` has fields that are specifically defined in the subclass.
        for field_name in self.__pydantic_fields__:
            yield field_name

        # `__pydantic_extra__` has fields that were not specifically defined.
        if getattr(self, '__pydantic_extra__', None):
            for field_name in sorted(self.__pydantic_extra__):
                yield field_name

    def __iter__(self):
        yield from self._iter_all_fields()

    def __len__(self):
        return len(tuple(self._iter_all_fields()))

    defaults: typing.ClassVar = _CreateDefaults()
    """
    Class property that holds an instance of this class with default values

    See :class:`_CreateDefaults`.
    """

    def _value_error(self, exception, path=()):
        """Translate :class:`pydantic.ValidationError` into :class:`~.ConfigValueError`"""

        def extra_forbidden(error):
            if len(error['loc']) == 1:
                return 'No such section'
            else:
                return 'No such option'

        def value_error(error):
            if error['msg'].startswith('Value error, '):
                return error['msg'][len('Value error, '):]
            else:
                return error['msg']

        custom_msgs = {
            'extra_forbidden': extra_forbidden,
            'value_error': value_error,
        }

        def maybe_add_input(error):
            if str(error['input']) in error['msg']:
                return error['msg']
            else:
                return error['msg'] + ': ' + str(error['input'])

        # TODO: When ExceptionGroup (introduced in Python 3.11) is widely available, we can raise
        #       mulitple exceptions here so that multiple invalid values in a config file are
        #       reported at the same time.
        for error in exception.errors():
            _log.debug('Validation error: %r', error)
            get_msg = custom_msgs.get(error['type'])
            if get_msg:
                msg = get_msg(error)
            else:
                msg = maybe_add_input(error)
            return errors.ConfigValueError(msg, path=(*path, *error['loc']))

        raise RuntimeError(f'No error found: {exception!r}') from exception


class _GetSectionNames:
    def __get__(self, obj, objtype):
        return tuple(objtype.__pydantic_fields__)


class ConfigBase(ConfigDictBase):
    """
    Root-level configuration model

    Instances map section names to :class:`SectionBase` subclass instances.

    From a user perspective, a section is a file name without the file extension, e.g. "clients" for
    "~/.config/upsies/clients.ini".
    """

    section_names: typing.ClassVar = _GetSectionNames()
    """Sequence of valid section names"""

    @pydantic.model_validator(mode='after')
    def validate_config(self):
        """
        Pass this :class:`ConfigBase` instance to :meth:`.SectionBase.validate_config` on all
        sections

        :return: the :class:`ConfigBase` instance (i.e. the first argument `self`)
        """
        for section in self.values():
            section.validate_config(self)
        return self

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            raise errors.UnknownSectionConfigError(key) from None

    def dump(self):
        """Return all values as a human-readable tree structure string"""
        return self._dump(self)

    def dump_defaults(self):
        """Return default values as a human-readable tree structure string"""
        return self._dump(self.defaults)

    @staticmethod
    def _dump(dct):
        lines = []
        for section_name, section in sorted(dct.items()):
            lines.append(f'   {section_name} [{type(section).__name__}]')
            for subsection_name, subsection in sorted(section.items()):
                lines.append(f'      {subsection_name} [{type(subsection).__name__}]')
                for option_name, value in sorted(subsection.items()):
                    lines.append(f'         {option_name} [{type(value).__name__}] = {value!r}')
        return '\n'.join(lines)

    @functools.cached_property
    def files(self):
        """
        :class:`~.collections.abc.Mapping` of section names to file paths

        Section names should be file stems, i.e. file names without extensions.
        """
        return {}

    def read(self, section_name, filepath, *, ignore_missing=False):
        """
        Read `filepath` and make its contents available as `section`

        :raises ConfigError: if reading, parsing or validating `filepath` fails
        """
        _log.debug('Loading %s configuration from %s', section_name, filepath)
        section_kwargs = self._read_ini(filepath, ignore_missing=ignore_missing)
        section_cls = self.__pydantic_fields__[section_name].annotation
        try:
            section = section_cls(**section_kwargs)
            setattr(self, section_name, section)
        except pydantic.ValidationError as e:
            raise errors.ConfigError(f'{filepath}: {self._value_error(e)}') from e
        else:
            # Remember the origin of the config so we can write() it later.
            self.files[section_name] = filepath

    def _read_ini(self, filepath, *, ignore_missing=False):
        # Create INI parser.
        cfgparser = configparser.ConfigParser(
            default_section=None,
            interpolation=None,
        )

        # Read INI file if it exists.
        filecontent = self._read_file(filepath, ignore_missing=ignore_missing)
        if filecontent:
            # Parse raw INI string.
            try:
                cfgparser.read_string(filecontent, source=filepath)
            except configparser.MissingSectionHeaderError as e:
                raise errors.ConfigError(f'{filepath}: Line {e.lineno}: {e.line.strip()}: Option outside of section') from e
            except configparser.ParsingError as e:
                lineno, msg = e.errors[0]
                # TODO: Remove this when Python 3.12 is deprecated.
                import sys
                if sys.version_info >= (3, 13):
                    msg = repr(msg)
                raise errors.ConfigError(f'{filepath}: Line {lineno}: {msg}: Invalid syntax') from e
            except configparser.DuplicateSectionError as e:
                raise errors.ConfigError(f'{filepath}: Line {e.lineno}: {e.section}: Duplicate section') from e
            except configparser.DuplicateOptionError as e:
                raise errors.ConfigError(f'{filepath}: Line {e.lineno}: {e.option}: Duplicate option') from e
            except configparser.Error as e:
                raise errors.ConfigError(f'{filepath}: {e}') from e

        # Convert ConfigParser instance to normal `dict`.
        # https://stackoverflow.com/a/28990982
        cfg = {
            section_name: dict(cfgparser.items(section_name))
            for section_name in cfgparser.sections()
        }

        # Make sure names can be valid object attributes, i.e. rename "foo-bar" to "foo_bar".
        def fix_name(name):
            return name.replace('-', '_')

        for section_name in tuple(cfg):
            # Fix section names.
            section_name_fixed = fix_name(section_name)
            cfg[section_name_fixed] = cfg.pop(section_name)
            # Fix option names in section.
            section = cfg[section_name_fixed]
            for option_name in tuple(section):
                option_name_fixed = fix_name(option_name)
                section[option_name_fixed] = section.pop(option_name)

        # Line breaks are interpreted as list separators
        for section in cfg.values():
            for option in section:
                if '\n' in section[option]:
                    section[option] = tuple(
                        item
                        for item in section[option].split('\n')
                        if item
                    )

        return cfg

    def _read_file(self, filepath, *, ignore_missing=False):
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except OSError as e:
            if isinstance(e, FileNotFoundError) and ignore_missing:
                return ''
            else:
                msg = e.strerror if e.strerror else str(e)
                raise errors.ConfigError(f'{filepath}: {msg}') from e

    def write(self, *sections, include_defaults=False):
        """
        Save current configuration to :attr:`files`

        List values use ``"\\n "`` (newline followed by two spaces) as separators between items.

        :param sections: Sections to write (see :attr:`files`)
            Write all sections if no sections are provided.

        :param bool include_defaults: Whether to include commented defaults

        :raise ConfigError: if writing fails
        """
        if not sections:
            sections = tuple(self.files)

        for section in sections:
            # Generate file content.
            comment_string = self._get_comment_string(section)
            ini_string = self[section].as_ini(include_defaults=include_defaults)
            section_string = '\n'.join(
                string for string in (comment_string, ini_string)
                if string
            ) + '\n'

            # Make sure parent directory exists with the correct permissions.
            parentdir = os.path.dirname(self.files[section])
            if parentdir:
                os.makedirs(parentdir, mode=0o700, exist_ok=True)
            try:
                with open(self.files[section], 'w') as f:
                    f.write(section_string)
            except OSError as e:
                msg = e.strerror if e.strerror else str(e)
                raise errors.ConfigError(f'{self.files[section]}: {msg}') from e

    def _get_comment_string(self, section):
        paragraphs = self[section].get_comment().strip().split('\n')
        if paragraphs and paragraphs != ['']:
            return '# ' + '\n# '.join(
                '\n# '.join(
                    textwrap.wrap(
                        text=paragraph,
                        width=90,
                        replace_whitespace=False,
                    )
                )
                for paragraph in paragraphs
            ) + '\n'
        else:
            return ''


class SectionBase(ConfigDictBase):
    """
    Configuration model of one section

    Instances map subsection names to :class:`SubsectionBase` instances.

    From a user perspective, a subsection a section in an INI file, e.g. "[qbittorrent]" in
    ~/.config/upsies/clients.ini.
    """

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            raise errors.UnknownSubsectionConfigError(key) from None

    def validate_config(self, config):
        """
        Called by :meth:`ConfigBase.validate_config` with its own instance after validation

        This method does nothing by default. Subclasses can override it if access to sibling
        sections is required for validation.
        """

    def get_comment(self):
        """Optional comment that explains the section to the user"""
        return ''

    def as_ini(self, *, include_defaults=False):
        """Return section in INI file format"""
        parts = []
        for subsection in self:
            parts.extend(self._as_ini(subsection, include_defaults=include_defaults))
        return '\n'.join(parts).strip()

    def _as_ini(self, subsection, *, include_defaults):
        options = self[subsection].as_ini(include_defaults=include_defaults)
        if options:
            yield f'[{subsection}]'
            yield options
            yield ''  # Empty line as separator between sections.


class SubsectionBase(ConfigDictBase):
    """
    Configuration model of one subsection

    Instances map option names to values.

    From a user perspective, an option is a single key-value pair in a section in an INI file,
    e.g. "foo = bar".
    """

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            raise errors.UnknownOptionConfigError(key) from None

    def get_description(self, option):
        """Return the description for `option` or empty string"""
        description = type(self).__pydantic_fields__[option].description
        if description:
            return string.evaluate_fstring(
                description,
                config=self,
                __project_name__=__project_name__,
            )
        else:
            return ''

    def as_ini(self, *, include_defaults=False, comment_defaults=True):
        """Return option-value pairs in INI file format"""
        return '\n'.join(self._as_ini(
            include_defaults=include_defaults,
            comment_defaults=comment_defaults,
        ))

    def _as_ini(self, *, include_defaults=False, comment_defaults=True):
        for option in self:
            yield from self._as_ini_option_lines(
                option,
                include_default=include_defaults,
                comment_default=comment_defaults,
            )

    def _as_ini_option_lines(self, option, *, include_default, comment_default):
        value = self[option]

        def option_lines(*lines):
            yield from self._as_ini_option_lines_filter(
                option=option,
                lines=lines,
                include_default=include_default,
                comment_default=comment_default,
            )

        if utils.is_sequence(value):
            # One item per line with 2 spaces indentation.
            yield from option_lines(
                f'{option} =',
                *(f'  {item}' for item in value),
            )

        elif isinstance(value, pydantic.SecretStr):
            # Values like password are not available unless explicitly requested to prevent leaks in
            # log files and such.
            yield from option_lines(f'{option} = {value.get_secret_value()}')

        else:
            yield from option_lines(f'{option} = {value}')

    def _as_ini_option_lines_filter(self, *, option, lines, include_default, comment_default):
        value = self[option]
        default = self.defaults[option]
        if value != default or not comment_default:
            # Custom value.
            yield from lines

        elif include_default:
            # Commented default value.
            for line in lines:
                yield '# ' + line
