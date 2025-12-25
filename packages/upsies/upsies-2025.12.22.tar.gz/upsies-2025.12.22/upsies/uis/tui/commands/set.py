"""
Change or show configuration file options
"""

import collections
import functools
import os
import textwrap

from .... import constants, defaults, errors, imagehosts, jobs, utils
from .base import CommandBase


class set(CommandBase):
    """
    Change or show configuration file options

    Without any arguments, all options are listed with their current values.

    OPTION consists of three segments which are delimited with a period (".").
    The first segment in OPTION is the INI file name without the extension.
    The second segment is the section name in that file. The third segment
    is the option name.

    List values are given as one argument per list item. If non-list values are
    given as multiple arguments, they are concatenated with single spaces. In
    the INI file, list items are delimited by one line break and one or more
    spaces (e.g. "\\n    ").
    """

    names = ('set',)

    cli_arguments = {
        'OPTION': {
            'nargs': '?',
            'help': 'Option to change or show',
        },
        'VALUE': {
            'nargs': '*',
            'default': '',  # FIXME: https://bugs.python.org/issue41854
            'help': 'New value for OPTION',
            'group': 'value',
        },
        ('--reset', '-r'): {
            'action': 'store_true',
            'help': 'Reset OPTION to default value',
            'group': 'value',
        },
        ('--dump', '-d'): {
            # Accept zero or more sections defined in defaults.Config, e.g. "clients" or "trackers".
            'type': utils.argtypes.one_of(defaults.Config.section_names),
            'nargs': '*',
            'metavar': 'FILE',
            'help': (
                f'Write current configuration to '
                f'{utils.fs.tildify_path(os.path.join(constants.CONFIG_DIRECTORYPATH, "FILE"))}.ini\n'
                'with commented-out default values\n'
                f'FILE may be ' + ", ".join(sorted(f'"{x}"' for x in defaults.Config.section_names)) +
                ', or it may be omitted to write all configuration files.\n'
                'WARNING: You will lose any comments and custom structure in your .ini files.'
            ),
            'group': 'value',
        },
        ('--options',): {
            'action': 'store_true',
            'help': 'Show description of all configuration options',
        },
        ('--fetch-ptpimg-apikey',): {
            'nargs': 2,
            'metavar': ('EMAIL', 'PASSWORD'),
            'help': (
                'Fetch ptpimg API key and save it in '
                f'{utils.fs.tildify_path(constants.IMGHOSTS_FILEPATH)}\n'
                '(EMAIL and PASSWORD are not saved)'
            ),
        },
    }

    @functools.cached_property
    def jobs(self):
        if self.args.options:
            return (self.documentation_job,)
        elif self.args.fetch_ptpimg_apikey is not None:
            return (self.fetch_ptpimg_apikey_job,)
        else:
            return (
                jobs.set.SetJob(
                    config=self.config,
                    option=self.args.OPTION,
                    # VALUE is always a list. SetJob should handle this gracefully.
                    value=self.args.VALUE,
                    reset=self.args.reset,
                    dump=self.dump_sections,
                ),
            )

    @property
    def dump_sections(self):
        if self.args.dump:
            return self.args.dump
        elif self.args.dump is None:
            return ()
        else:
            return tuple(self.config)

    @functools.cached_property
    def fetch_ptpimg_apikey_job(self):
        return jobs.custom.CustomJob(
            name='fetch-ptpimg-apikey',
            label='API key',
            worker=self.fetch_ptpimg_apikey,
            catch=(errors.RequestError, errors.ConfigError),
            ignore_cache=True,
        )

    async def fetch_ptpimg_apikey(self, job):
        if len(self.args.fetch_ptpimg_apikey) <= 0:
            job.error('Missing EMAIL and PASSWORD')
        elif len(self.args.fetch_ptpimg_apikey) <= 1:
            job.error('Missing PASSWORD')
        elif len(self.args.fetch_ptpimg_apikey) > 2:
            unknown_args = ' '.join(self.args.fetch_ptpimg_apikey[2:])
            job.error(f'Unrecognized arguments: {unknown_args}')
        else:
            email = self.args.fetch_ptpimg_apikey[0]
            password = self.args.fetch_ptpimg_apikey[1]
            ptpimg = imagehosts.imagehost('ptpimg')
            apikey = await ptpimg.get_apikey(email, password)
            job.add_output(apikey)
            self.config['imghosts']['ptpimg']['apikey'] = apikey
            self.config.write('imghosts')

    @functools.cached_property
    def documentation_job(self):
        return jobs.custom.CustomJob(
            name='documentation-job',
            label='Documentation',
            hidden=True,
            worker=self.display_documentation,
            ignore_cache=True,
        )

    async def display_documentation(self, job):
        lines = []
        for section_name, subsections in self.config.items():
            for subsection_name, options in subsections.defaults.items():
                for option_name in options:
                    lines.extend(
                        self._document_option(section_name, subsection_name, option_name)
                    )
                    lines.append('')

        # Remove trailing empty line.
        del lines[-1]
        job.add_output('\n'.join(lines))

    def _document_option(self, section, subsection, option):
        default = self.config[section][subsection].defaults[option]

        if isinstance(default, (int, float)):
            option_type_name = 'number'
        elif isinstance(default, str):
            option_type_name = 'string'
        elif isinstance(default, collections.abc.Sequence):
            option_type_name = 'list'
        elif hasattr(default, 'options'):
            option_type_name = 'choice'
        else:
            option_type_name = ''

        # Display option path and type.
        if option_type_name:
            lines = [f'{section}.{subsection}.{option} ({option_type_name})']
        else:
            lines = [f'{section}.{subsection}.{option}']

        if option_type_name == 'choice':
            lines.append('  Options: ' + ', '.join(default.options))

        # Handle list value.
        if utils.is_sequence(default):
            if default:
                lines.append(f'  Default: {default[0]}')
                lines.extend(
                    f'           {item}'
                    for item in default[1:]
                )
            else:
                lines.append('  Default: <empty>')
        else:
            lines.append(f'  Default: {default}')

        # Add description indented.
        description = self.config[section][subsection].get_description(option)
        if description:
            description_lines = []
            for paragraph in description.strip().split('\n'):
                description_lines.extend(
                    textwrap.wrap(
                        text=paragraph,
                        width=72,
                    )
                )
            lines.extend('  ' + line for line in description_lines)

        return lines
