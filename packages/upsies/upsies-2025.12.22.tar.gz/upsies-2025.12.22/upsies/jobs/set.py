"""
Manage configuration files
"""

from .. import errors, utils
from . import JobBase

import logging  # isort:skip
_log = logging.getLogger(__name__)


class SetJob(JobBase):
    """Display or change configuration file option"""

    name = 'set'
    label = 'Set'
    hidden = True

    # Don't read output from cache.

    # TODO: Currently there is no way to prevent output from being written. We could do this by
    #       implementing an Enum with the values "NO_READ" and "NO_READ_WRITE".
    cache_id = None

    def initialize(self, *, config, option=None, value=(), reset=None, dump=()):
        """
        Set and display option(s)

        :param config: :class:`~.config.ConfigBase` instance

        :param str option: "."-delimited path to option in `config` or `None`

        :param value: New value for `option` or any falsy value to display the current value

            If `value` is a sequence and `option` is not, the items are joined with a space.
            If `value` is not a sequence and `option` is, `value` is turned into a sequence with the
            single item `value`.

        :param bool reset: Whether to reset `option` to default value and ignore `value`

        :param bool dump: Sequence of sections in `config`

            Read and write configuration the :attr:`~.ConfigBase.files` associated with each
            section. Default values are commented out so the user can easily edit each file.

        If only `config` is given, display all options and values.

        If `option` is given, only display its value.

        If `option` and `value` is given, set `option` to `value` and display the new value.

        If `dump` is given, it is a sequence of sections. For each section, the corresponding file
        is written.
        """
        if option and dump:
            raise RuntimeError('Arguments "option" and "dump" are mutually exclusive.')

        if value:
            if reset:
                raise RuntimeError('Arguments "value" and "reset" are mutually exclusive.')
            if dump:
                raise RuntimeError('Arguments "value" and "dump" are mutually exclusive.')

        self._config = config
        self._option = option
        self._value = value
        self._reset = reset
        self._dump = dump

    async def run(self):
        try:
            if self._reset:
                self._reset_mode()
            elif self._value:
                self._set_mode()
            elif self._dump:
                self._dump_mode()
            else:
                self._display_mode()

        except errors.UnknownConfigError as e:
            # UnknownConfigError is a subclass of KeyError, so ``str(e)`` is quoted and so the
            # actual error message has to come from an attribute.
            self.error(e.message)

        except errors.ConfigError as e:
            self.error(e)

    def _display_mode(self):
        self._display_option(self._option)

    def _set_mode(self):
        self._set_option(self._option, self._value)
        self._write_section(self._option)
        self._display_option(self._option)

    def _reset_mode(self):
        path = self._normalize_path(self._option)
        section, subsection, option, *_ = (*path, None, None, None)

        try:
            if section and subsection and option:
                _log.debug('Resetting option: %s', '.'.join((section, subsection, option)))
                default = self._config[section][subsection].defaults[option]
                self._config[section][subsection][option] = default
            elif section and subsection:
                _log.debug('Resetting subsection: %s', '.'.join((section, subsection)))
                default = self._config[section][subsection].defaults
                self._config[section][subsection] = default
            elif section:
                _log.debug('Resetting section: %s', section)
                default = self._config[section].defaults
                self._config[section] = default
            else:
                _log.debug('Resetting all sections')
                self._config = self._config.defaults
        except errors.UnknownConfigError as e:
            # Prepend the path to the error message.
            raise errors.ConfigError('.'.join(path) + f': {e.message}') from e
        else:
            self._write_section(self._option)
            self._display_option(self._option)

    def _dump_mode(self):
        for section in self._dump:
            # Write file
            self._config.write(section, include_defaults=True)

            # Display file
            banner_width = 78
            self.add_output('#' * banner_width)
            msg = f' Wrote {self._config.files[section]} '
            self.add_output('###' + msg.ljust(banner_width - 3, '#'))
            self.add_output('#' * banner_width)
            with open(self._config.files[section], 'r') as f:
                self.add_output(f.read())

    def _display_option(self, path):
        """
        Show value(s) of option, subsection or section referred to by `path`

        :param path: See :meth:`_get_valid_path_and_value`.
        """
        def display(value, path):
            if isinstance(value, utils.config.ConfigDictBase):
                # Display section or subsection of options.
                for option_name, value_ in value.items():
                    display(value_, path=(*path, option_name))

            elif utils.is_sequence(value):
                value_string = '\n  '.join(str(v) for v in value)
                if value_string:
                    value_string = '\n  ' + value_string
                self.add_output('.'.join(path) + ' =' + value_string)
            else:
                value_string = ' ' + str(value)
                self.add_output('.'.join(path) + ' =' + value_string)

        parent_path, value = self._get_valid_path_and_value(path)
        display(value, parent_path)

    def _set_option(self, path, value):
        """
        Set option referred to by `path` to `value`

        :param path: See :meth:`_get_valid_option_path_and_value`.
        """
        (section, subsection, option), current_value = self._get_valid_option_path_and_value(path)

        # Make sure `value` is (not) a sequence, depending on current value. Conversion from `str`
        # should be automatically handled by `self._config`.
        if utils.is_sequence(current_value) and not utils.is_sequence(value):
            value = (value,)
        elif not utils.is_sequence(current_value) and utils.is_sequence(value):
            value = ' '.join(value)

        # Set new value.
        self._config[section][subsection][option] = value

        # Some options need the whole config for validation, e.g. if `trackers.*.add_to` is set to
        # "foo", `TrackersConfig` must check if `clients.foo` exists.
        self._config.validate_config()

        return '.'.join(path), self._config[section][subsection][option]

    def _write_section(self, path):
        """
        Write section to its associated file (see :meth:`~.ConfigBase.write`)

        :param path: See :meth:`_normalize_path`.
        """
        section_name, *_ = self._normalize_path(path)
        self._config.write(section_name)

    def _get_valid_path_and_value(self, path):
        """
        Return normalized and validated option/subsection/section path and the corresponding
        value/subsection/section

        :param path: See :meth:`_normalize_path`.

        :raise ConfigError: if `path` does not refer to an existing option, subsection or section
        """
        path = self._normalize_path(path)
        value = self._config
        valid_path = []
        for key in path:
            try:
                value = value[key]
            except errors.UnknownConfigError as e:
                raise errors.ConfigError('.'.join(path) + f': {e.message}') from e
            else:
                valid_path.append(key)
        return (tuple(valid_path), value)

    def _get_valid_option_path_and_value(self, path):
        """
        Return normalized and validated option path and corresponding value

        :param path: See :meth:`_normalize_path`.

        :raise ConfigError: if `path` does not refer to an existing option
        """
        path, value = self._get_valid_path_and_value(path)
        if len(path) == 0:
            raise errors.ConfigError('Missing section, subsection and option')
        elif len(path) == 1:
            raise errors.ConfigError(f'Missing subsection and option in section {path[0]}')
        elif len(path) == 2:
            raise errors.ConfigError(f'Missing option in subsection {path[0]}.{path[1]}')
        else:
            return path, value

    def _normalize_path(self, path):
        """
        Return any valid path, e.g. ``(section,)``, ``(section, subsection)`` or ``(section,
        subsection, option)``

        :param path: :class:`str` (``section.subsection.option``, ``section.subsection`` or
            ``section``) or any valid return value of this method

        .. note:: This method does only return ``path`` in a valid format. It does not check if
            ``path`` resolves to an existing option, subsection or section.

        :raise ConfigError: if `path` is not a valid path to a section, subsection or option
        """
        if not path:
            return ()
        else:
            if not isinstance(path, (tuple, list)):
                path = tuple(k for k in path.split('.') if k.strip())
            if len(path) > 3:
                raise errors.ConfigError('.'.join(path) + ': Invalid option')
            else:
                return path
