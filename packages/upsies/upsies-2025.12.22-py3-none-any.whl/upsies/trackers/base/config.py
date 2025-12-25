"""
Base class for tracker configuration
"""

from ... import btclients, constants, utils

import logging  # isort:skip
_log = logging.getLogger(__name__)


def base_url(default):
    return utils.config.fields.string(
        default=default,
        description='Base URL of the website.\n(Changing this is only useful for debugging purposes.)',
    )


def upload_url(default):
    return utils.config.fields.string(
        default=default,
        description='Upload API URL.\n(Changing this is only useful for debugging purposes.)',
    )


def announce_url(default, *, autofetched=False, instructions=''):
    description = 'Your personal announce URL.'
    if autofetched:
        description += '\nAutomatically fetched from the website if not set.'
    if instructions:
        description += '\n' + str(instructions)
    return utils.config.fields.string(
        default=default,
        description=description,
        secret=True,
    )


def apikey(default, *, instructions=''):
    description = 'Your personal API key.'
    if instructions:
        description += '\n' + str(instructions)
    return utils.config.fields.string(
        default=default,
        description=description,
        secret=True,
    )


def username(default):
    return utils.config.fields.string(
        default=default,
        description='Your personal username.',
    )


def password(default):
    return utils.config.fields.string(
        default=default,
        description='Your personal password.',
        secret=True,
    )


def exclude(*defaults):
    return utils.config.fields.custom(
        cls=utils.types.ListOf(utils.types.Regex),
        default=defaults,
        description='List of regular expressions. Matching files are excluded from generated torrents.',
    )


def anonymous(default):
    return utils.config.fields.boolean(
        default=default,
        description='Whether your username is displayed on your uploads.',
    )


def image_host(Imagehost, *, default):
    return utils.config.fields.custom(
        cls=utils.types.ListOf(Imagehost, separator=','),
        default=default,
        description=(
            'List of image hosting service names. The first service is normally used '
            'with the others as backup if uploading fails.\n'
            'Supported services: ' + ', '.join(Imagehost.options)
        ),
    )


def screenshots_count(default, *, min, max, description=''):
    if not description:
        description = 'How many screenshots to make.'
    description += f'\nMinimum is {min}, maximum is {max}.'
    return utils.config.fields.integer(
        default=default,
        min=min,
        max=max,
        description=description,
    )


def screenshots_columns(default, *, min, max, description=''):
    if not description:
        description = 'Maximum number of columns in screenshot table.'
    description += f'\nMinimum is {min}, maximum is {max}.'
    return utils.config.fields.integer(
        default=default,
        min=min,
        max=max,
        description=description,
    )


def cookies_filepath(default):
    return utils.config.fields.string(
        default=default,
        description=(
            'File that stores permanent session cookies.\n'
            'If this is not set, a new login session is started for each submission.'
        ),
    )


class TrackerConfigBase(utils.config.SubsectionBase):
    """
    Base class for a tracker's user configuration (e.g. via config file or CLI arguments)

    Options defined in this class are available for all trackers. Subclasses may add more options or
    override values of this class' options.
    """

    exclude: exclude()

    add_to: utils.config.fields.string(
        default='',
        description=(
            'BitTorrent client to add torrent to after successful submission.\n'
            'Valid values are ' + ", ".join(f'"{c}"' for c in btclients.client_names()) + ' or one of the section names '
            f'in {utils.fs.tildify_path(constants.CLIENTS_FILEPATH)}.'
        ),
    )

    copy_to: utils.config.fields.string(
        default='',
        description='Directory path to copy torrent file to after successful submission.',
    )
