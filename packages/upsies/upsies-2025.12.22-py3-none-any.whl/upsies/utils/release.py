"""
Release name parsing and formatting

:class:`ReleaseInfo` parses a string into a dictionary-like object with a
specific set of keys, e.g. "title", "resolution", "source", etc.

:class:`ReleaseName` wraps :class:`ReleaseInfo` to do the same, but in addition
it tries to read media data from the file system to get information. It also
adds a :class:`~.ReleaseName.format` method to turn everything back into a
string.
"""

import asyncio
import collections
import copy
import functools
import os
import re
import time

import unidecode

from .. import constants, errors, utils
from . import LazyModule, fs
from .types import ReleaseType

import logging  # isort:skip
_log = logging.getLogger(__name__)

# Disable debugging messages from rebulk
logging.getLogger('rebulk').setLevel(logging.WARNING)

_guessit = LazyModule(module='guessit.api', name='_guessit', namespace=globals())
natsort = utils.LazyModule(module='natsort', namespace=globals())


DELIM = r'[ \.-]'
"""
Regular expression that matches a single delimiter between release name
parts, usually ``"."`` or ``" "``
"""


class _translated_property:
    """
    Property decorator that translates values when they are accessed

    https://docs.python.org/3/howto/descriptor.html

    The translation is based on a table in the form of a mapping, which must be available as a
    ``_translate`` attribute on the decorated method's instance.

    ``_translate`` maps names of :class:`~.ReleaseName` attributes to ``{<regular expression>:
    <replacement string>}`` or ``{<regular expression>: <callable>}`` dictionaries. ``<callable>``
    gets the value returned by the property method and the :class:`~.ReleaseName` instance. It must
    return the translated value or `None`, in which case the value is not translated.

    .. note:: ``<callable>`` cannot get the untranslated value from the instance because that
              results in :class:`RecursionError`.

    Replacements are applied in the same order as they are defined.
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __set_name__(self, owner, name):
        self._property_name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            # `self._property_name` is accessed on the class (i.e. `objtype`).
            return self
        else:
            # `self._property_name` is accessed on the instance (i.e. `obj`).
            return self._apply_translation(obj._translate, obj)

    def _apply_translation(self, tables, obj):

        def translate(val):
            table_or_callable = tables.get(self._property_name, None)

            if isinstance(table_or_callable, collections.abc.Mapping):
                for regex, replacement in table_or_callable.items():
                    val = regex.sub(str(replacement), val)

            elif callable(table_or_callable):
                val_translated = table_or_callable(val, obj)
                if val_translated is not None:
                    val = str(val_translated)

            elif table_or_callable is not None:
                raise RuntimeError(f'{self._property_name}: Not a dictionary or callable: {table_or_callable!r}')

            return val

        # Get the value from the instance's property, i.e. a method that is decorated with
        # `@_translated_property`.
        value = self.fget(obj)
        try:
            if isinstance(value, str):
                value = translate(value)
            elif isinstance(value, collections.abc.Iterable):
                value = tuple(translate(v) for v in value)
        except BaseException as e:
            # If we are running a background task, exceptions may be ignored. This shouldn't be, but
            # it's easy to overlook and it doesn't cost much to log the exception.
            _log.debug('%s TRANSLATION FAILED: %r', self._property_name, e)
            raise

        return value

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("Can't set attribute")
        self.fset(obj, value)

    def __delete__(self, obj):
        raise AttributeError("Can't delete attribute")

    def setter(self, fset):
        return type(self)(self.fget, fset, self.fdel, self.__doc__)


class ReleaseName(collections.abc.Mapping):
    """
    Standardized release name

    :param str path: Path to release file or directory

        If :attr:`path` exists, it is used to read video and audio metadata,
        e.g. to detect the codecs, resolution, etc.

    :param str name: Path or other string to pass to :class:`ReleaseInfo`
        (defaults to `path`)

    :param dict translate: Map names of properties that return a string
        (e.g. ``audio_format``) to maps of regular expressions to replacement
        strings. The replacement strings may contain backreferences to groups in
        their regular expression.

        Example:

        >>> {
        >>>     'audio_format': {
        >>>         re.compile(r'^DDP$'): r'DD+',
        >>>     },
        >>>     'video_format': {
        >>>         re.compile(r'^x26([45])$'): r'H.26\\1',
        >>>     },
        >>> }

    :param str separator: Separator between release name parts (usually " " or
        ".") or `None` to use the default

    Example:

    >>> rn = ReleaseName("path/to/The.Foo.1984.1080p.Blu-ray.X264-ASDF")
    >>> rn.source
    'BluRay'
    >>> rn.format()
    'The Foo 1984 1080p BluRay DTS x264-ASDF'
    >>> "{title} ({year}) [{group}]".format(**rn)
    'The Foo (1984) [ASDF]'
    >>> rn.set_name('The Foo 1985 1080p BluRay DTS x264-AsdF')
    >>> "{title} ({year}) [{group}]".format(**rn)
    'The Foo (1985) [AsdF]'
    """

    def __init__(self, path, *, name=None, translate=None, separator=None, english_title_before_original=False):
        self._path = str(path)
        self._name = name
        self.separator = separator
        self.english_title_before_original = english_title_before_original
        self._info = ReleaseInfo(str(name) if name is not None else self._path)
        self._translate = translate or {}

    @property
    def release_info(self):
        """Internal :class:`~.ReleaseInfo` instance"""
        return self._info

    def set_release_info(self, path):
        """
        Update internal :class:`ReleaseInfo` instance

        :param path: Argument for :class:`ReleaseInfo` (path or any other
            string)
        """
        self._info = ReleaseInfo(str(path))

    def __repr__(self):
        posargs = [self._path]
        kwargs = {}
        if self._name is not None:
            kwargs['name'] = self._name
        if self._translate:
            kwargs['translate'] = self._translate
        args = ', '.join(repr(arg) for arg in posargs)
        if kwargs:
            args += ', ' + ', '.join(f'{k}={v!r}' for k, v in kwargs.items())
        return f'{type(self).__name__}({args})'

    def __str__(self):
        return self.format()

    def __len__(self):
        return len(tuple(iter(self)))

    def __iter__(self):
        # Non-private properties are dictionary keys
        cls = type(self)
        return iter(
            attr for attr in dir(self)
            if (
                    not attr.startswith('_')
                    and isinstance(getattr(cls, attr), (property, _translated_property))
            )
        )

    def __getitem__(self, name):
        if not isinstance(name, str):
            raise TypeError(f'Not a string: {name!r}')
        elif isinstance(getattr(type(self), name, None), (property, _translated_property)):
            return getattr(self, name)
        else:
            raise KeyError(name)

    @property
    def path(self):
        """:class:`str` version of the `path` instantiation argument"""
        return self._path

    @property
    def separator(self):
        """
        Separator between release name parts (usually " " or ".") or `None` to use
        the default
        """
        return self._separator

    @separator.setter
    def separator(self, separator):
        self._separator = str(separator) if separator is not None else ' '

    @property
    def type(self):
        """
        :class:`~.types.ReleaseType` enum or one of its value names

        See also :meth:`fetch_info`.
        """
        return self._info.get('type', ReleaseType.unknown)

    @type.setter
    def type(self, value):
        if not value:
            self._info['type'] = ReleaseType.unknown
        else:
            self._info['type'] = ReleaseType(value)

    @_translated_property
    def title(self):
        """
        Original name of movie or series or "UNKNOWN_TITLE"

        See also :meth:`fetch_info`.
        """
        return self._info.get('title') or 'UNKNOWN_TITLE'

    @title.setter
    def title(self, value):
        self._info['title'] = str(value)

    @_translated_property
    def title_aka(self):
        """
        Alternative name of movie or series or empty string

        For non-English original titles, this should be the English title. If
        :attr:`title` is identical, this is an empty string.

        See also :meth:`fetch_info`.
        """
        aka = self._info.get('aka') or ''
        if aka and aka != self.title:
            return aka
        else:
            return ''

    @title_aka.setter
    def title_aka(self, value):
        self._info['aka'] = str(value)

    @property
    def english_title_before_original(self):
        """
        Whether the English title is left of "AKA" and the original title is right of "AKA" in
        :attr:`title_with_aka`

        If there is no :attr:`title_aka`, this has no effect.
        """
        return getattr(self, '_english_title_before_original', False)

    @english_title_before_original.setter
    def english_title_before_original(self, value):
        self._english_title_before_original = bool(value)

    @_translated_property
    def title_with_aka(self):
        """
        Combination of :attr:`title` and :attr:`title_aka`

        See also :attr:`english_title_before_original`.
        """
        if self.title_aka:
            if self.english_title_before_original:
                return f'{self.title_aka} AKA {self.title}'
            else:
                return f'{self.title} AKA {self.title_aka}'
        else:
            return self.title

    @_translated_property
    def title_with_aka_and_year(self):
        """
        Combination of :attr:`title_with_aka` with :attr:`country` and :attr:`year`
        if appropriate

        If :attr:`date` is specified, it is appended to :attr:`title_with_aka`.
        Otherwise, if :attr:`year_required` is `True`, :attr:`year` is appended.

        If :attr:`country_required` is `True`, :attr:`country` is appended.

        In summary: This should provide a unique identifier for humans.
        """
        title = [self.title_with_aka]

        if self.date:
            title.append(self.date)
        elif self.year_required:
            title.append(self.year)

        if self.country_required:
            title.append(self.country)

        return ' '.join(title)

    @_translated_property
    def year(self):
        """
        Release year or "UNKNOWN_YEAR" if :attr:`year_required` is set, empty string
        otherwise

        See also :meth:`fetch_info`.
        """
        if self.year_required:
            return self._info.get('year') or 'UNKNOWN_YEAR'
        else:
            return self._info.get('year') or ''

    @year.setter
    def year(self, value):
        if not isinstance(value, (str, int)) and value is not None:
            raise TypeError(f'Not a number: {value!r}')
        elif not value:
            self._info['year'] = ''
        else:
            year = str(value)
            current_year = int(time.strftime('%Y')) + 2
            if len(year) != 4 or not year.isdecimal() or not 1880 <= int(year) <= current_year:
                raise ValueError(f'Invalid year: {value}')
            self._info['year'] = year

    @property
    def year_required(self):
        """
        Whether :attr:`title_with_aka_and_year` includes :attr:`year`

        See also :meth:`fetch_info`.
        """
        default = self.type is ReleaseType.movie
        return getattr(self, '_year_required', default)

    @year_required.setter
    def year_required(self, value):
        self._year_required = bool(value)

    @_translated_property
    def country(self):
        """
        Release country or "UNKNOWN_COUNTRY" if :attr:`country_required` is set,
        empty string otherwise

        See also :meth:`fetch_info`.
        """
        country = self._info.get('country')
        if self.country_required:
            return country or 'UNKNOWN_COUNTRY'
        else:
            return country or ''

    @country.setter
    def country(self, value):
        if not value:
            self._info['country'] = ''
        else:
            self._info['country'] = str(value)

    @property
    def country_required(self):
        """
        Whether :attr:`title_with_aka_and_year` includes :attr:`country`

        See also :meth:`fetch_info`.
        """
        return getattr(self, '_country_required', False)

    @country_required.setter
    def country_required(self, value):
        self._country_required = bool(value)

    @_translated_property
    def episodes(self):
        """
        Season and episodes in "S01E02"-style format or "UNKNOWN_SEASON" for season
        packs, "UNKNOWN_EPISODE" for episodes, empty string for other types

        This property can be set to one or more season numbers (:class:`str`,
        :class:`int` or sequence of those), a "S01E02"-style string (see
        :meth:`Episodes.from_string`) or any falsy value.
        """
        if self.type is ReleaseType.season:
            return str(self._info.get('episodes') or 'UNKNOWN_SEASON')
        elif self.type is ReleaseType.episode:
            episodes = self._info.get('episodes', Episodes())
            if not any(season for season in episodes.values()):
                return 'UNKNOWN_EPISODE'
            else:
                return str(episodes)
        elif self.type is ReleaseType.unknown:
            return str(self._info.get('episodes') or '')
        else:
            return ''

    @episodes.setter
    def episodes(self, value):
        if isinstance(value, str) and Episodes.has_episodes_info(value):
            self._info['episodes'] = Episodes.from_string(value)
        elif not isinstance(value, str) and isinstance(value, collections.abc.Mapping):
            self._info['episodes'] = Episodes(value)
        elif not isinstance(value, str) and isinstance(value, collections.abc.Iterable):
            self._info['episodes'] = Episodes({v: () for v in value})
        elif value:
            self._info['episodes'] = Episodes({value: ()})
        else:
            self._info['episodes'] = Episodes()

    @property
    def episodes_dict(self):
        """Episodes as :class:`Episodes` object"""
        return self._info.get('episodes') or Episodes()

    @property
    def only_season(self):
        """
        Season if there is only one season in :attr:`episodes_dict`, `None`
        otherwise
        """
        seasons = tuple(self.episodes_dict)
        return seasons[0] if len(seasons) == 1 else None

    @_translated_property
    def episode_title(self):
        """Episode title if :attr:`type` is "episode" or empty string"""
        if self.type is ReleaseType.episode:
            return self._info.get('episode_title') or ''
        else:
            return ''

    @episode_title.setter
    def episode_title(self, value):
        self._info['episode_title'] = str(value)

    @_translated_property
    def date(self):
        """
        Date (YYYY-MM-DD)

        Sometimes single episodes are not released as part of a season but with
        an air date to identify them.

        For episodes, this should be the air date or an empty string.

        For anything that isn't an episode, this is always an empty string.
        """
        if self.type is ReleaseType.episode:
            return self._info.get('date') or ''
        else:
            return ''

    @date.setter
    def date(self, value):
        self._info['date'] = str(value)

    @_translated_property
    def service(self):
        """Streaming service abbreviation (e.g. "AMZN", "NF") or empty string"""
        return self._info.get('service') or ''

    @service.setter
    def service(self, value):
        self._info['service'] = str(value)

    @_translated_property
    def edition(self):
        """
        List of "Director's Cut", "Uncut", "Unrated", etc

        :raise ContentError: if :attr:`path` exists but contains unexpected data
        """
        if 'edition' not in self._info:
            self._info['edition'] = []

        # Dual Audio
        while 'Dual Audio' in self._info['edition']:
            self._info['edition'].remove('Dual Audio')
        if self.has_dual_audio:
            self._info['edition'].append('Dual Audio')

        return self._info['edition']

    @edition.setter
    def edition(self, value):
        self._info['edition'] = [str(v) for v in value]

    @_translated_property
    def source(self):
        '''Original source (e.g. "BluRay", "WEB-DL") or "UNKNOWN_SOURCE"'''
        source = None

        # DVD
        video_ts_path = utils.fs.find_name('VIDEO_TS', self._path, validator=os.path.isdir)
        if video_ts_path:
            # Include VIDEO_TS siblings (e.g. "cover")
            release_size = utils.fs.path_size(os.path.dirname(video_ts_path))
            _log.debug('VIDEO_TS size: %r: %r', video_ts_path, release_size)
            if release_size <= 4_700_000_000:
                source = 'DVD5'
            else:
                source = 'DVD9'

        if source is None:
            # Blu-ray
            bdmv_path = utils.fs.find_name('BDMV', self._path, validator=os.path.isdir)
            if bdmv_path:
                # Include BDMV siblings (e.g. "CERTIFICATE", and "ANY!")
                release_size = utils.fs.path_size(os.path.dirname(bdmv_path))
                _log.debug('Blu-ray size: %r: %r', bdmv_path, release_size)
                if release_size <= 25e9:
                    source = 'BD25'
                elif release_size <= 50e9:
                    source = 'BD50'
                elif release_size <= 66e9:
                    source = 'BD66'
                else:
                    source = 'BD100'

        if source is None:
            source = self._info.get('source') or 'UNKNOWN_SOURCE'

        return source

    @source.setter
    def source(self, value):
        self._info['source'] = str(value)

    @_translated_property
    def resolution(self):
        """
        Resolution (e.g. "1080p") or "UNKNOWN_RESOLUTION"

        :raise ContentError: if :attr:`path` exists but contains unexpected data
        """
        res = utils.mediainfo.video.get_resolution(self._path, default=None)
        if res is None:
            res = self._info.get('resolution') or 'UNKNOWN_RESOLUTION'
        return res

    @resolution.setter
    def resolution(self, value):
        self._info['resolution'] = str(value)

    @_translated_property
    def audio_format(self):
        """
        Audio format (e.g. "FLAC") or empty string (no audio track) or "UNKNOWN_AUDIO_FORMAT"

        :raise ContentError: if :attr:`path` exists but contains unexpected data
        """
        af = utils.mediainfo.audio.get_audio_format(self._path, default=None)
        if af is None:
            af = self._info.get('audio_codec') or 'UNKNOWN_AUDIO_FORMAT'
        return af

    @audio_format.setter
    def audio_format(self, value):
        self._info['audio_codec'] = str(value)

    @_translated_property
    def audio_channels(self):
        """
        Audio channels (e.g. "5.1") or empty string (no audio track)

        :raise ContentError: if :attr:`path` exists but contains unexpected data
        """
        ac = utils.mediainfo.audio.get_audio_channels(self._path, default=None)
        if ac is None:
            ac = self._info.get('audio_channels') or ''
        return ac

    @audio_channels.setter
    def audio_channels(self, value):
        self._info['audio_channels'] = str(value)

    @_translated_property
    def hdr_format(self):
        """
        HDR format name (e.g. "DV" or "HDR10") or empty string

        If not set explicitly and :attr:`path` exists, this value is
        autodetected if possible, otherwise default to whatever
        :class:`ReleaseInfo` detected in the release name.

        Setting this value back to `None` turns on autodetection as described
        above.

        :raise ContentError: if :attr:`path` exists but contains unexpected data
        """
        # Use manually set value unless it is None
        if getattr(self, '_hdr_format', None) is not None:
            return self._hdr_format

        # Autodetect from existing files
        if os.path.exists(self._path):
            hdr_formats = utils.mediainfo.video.get_hdr_formats(self._path, default=None)
            if hdr_formats:
                self._hdr_formats = ' '.join(hdr_formats)
                return self._hdr_formats

        # Autodetect from release name
        guessed_hdr = self._info.get('hdr_format', '')
        if guessed_hdr:
            return guessed_hdr

        # No HDR detected
        return ''

    @hdr_format.setter
    def hdr_format(self, value):
        if value is None:
            # Turn on autodetection
            self._hdr_format = None
        elif not value:
            # No HDR
            self._hdr_format = ''
        elif value in utils.mediainfo.video.known_hdr_formats:
            self._hdr_format = value
        else:
            raise ValueError(f'Unknown HDR format: {value!r}')

    @_translated_property
    def video_format(self):
        """
        Video format (or encoder in case of x264/x265/XviD) or "UNKNOWN_VIDEO_FORMAT"

        :raise ContentError: if :attr:`path` exists but contains unexpected data
        """
        vf = utils.mediainfo.video.get_video_format(self._path, default=None)
        if vf is None:
            vf = self._info.get('video_codec') or 'UNKNOWN_VIDEO_FORMAT'
        return vf

    @video_format.setter
    def video_format(self, value):
        self._info['video_codec'] = str(value)

    @_translated_property
    def group(self):
        """
        Name of release group or "NOGROUP"

        "NOGRP", and "" are translated to "NOGROUP" case-insensitively.
        """
        group = self._info.get('group', '')
        if self.nogroup_regex.match(group):
            return 'NOGROUP'
        else:
            return group

    nogroup_regex = re.compile(r'^(?i:nogroup|nogrp|)$')

    @group.setter
    def group(self, value):
        self._info['group'] = str(value)

    @property
    def has_commentary(self):
        """
        Whether this release has a commentary audio track

        If not set explicitly and `:attr:`path`` exists, this value is
        autodetected by looking for "commentary" case-insensitively in any audio
        track title.

        If not set explicitly and :attr:`path` does not exists, default to
        detection by :class:`ReleaseInfo`.

        Setting this value to `None` turns on autodetection as described above.

        :raise ContentError: if :attr:`path` exists but contains unexpected data
        """
        # Use manually set value unless it is None
        if getattr(self, '_has_commentary', None) is not None:
            return self._has_commentary

        # Find "Commentary" in audio track titles
        elif os.path.exists(self._path):
            self._has_commentary = utils.mediainfo.audio.has_commentary(self._path, default=False)
            return self._has_commentary

        # Default to ReleaseInfo['has_commentary']
        else:
            return self._info.get('has_commentary')

    @has_commentary.setter
    def has_commentary(self, value):
        if value is None:
            self._has_commentary = None
        else:
            self._has_commentary = bool(value)

    @property
    def has_dual_audio(self):
        """
        Whether this release has an English and a non-English audio track

        If not set explicitly and :attr:`path` exists, this value is
        autodetected if possible, otherwise default to whatever
        :class:`ReleaseInfo` detected in the release name.

        Setting this value back to `None` turns on autodetection as described
        above.

        :raise ContentError: if :attr:`path` exists but contains unexpected data
        """
        # Use manually set value unless it is None
        if getattr(self, '_has_dual_audio', None) is not None:
            return self._has_dual_audio

        # Autodetect dual audio
        elif os.path.exists(self._path):
            self._has_dual_audio = bool(utils.mediainfo.audio.has_dual_audio(self._path, default=False))
            return self._has_dual_audio

        # Default to ReleaseInfo['edition']
        else:
            return 'Dual Audio' in self._info.get('edition', ())

    @has_dual_audio.setter
    def has_dual_audio(self, value):
        if value is None:
            self._has_dual_audio = None
        else:
            self._has_dual_audio = bool(value)

    _needed_attrs = {
        ReleaseType.movie: ('title', 'year', 'resolution', 'source', 'video_format'),
        ReleaseType.season: ('title', 'episodes', 'resolution', 'source', 'video_format'),
        ReleaseType.episode: ('title', 'episodes', 'resolution', 'source', 'video_format'),
    }

    @functools.cached_property
    def dvd_resolution(self):
        """"PAL" or "NTSC" for DVD release or `None` for non-DVD release"""
        if (
                self.source in ('DVD', 'DVD5', 'DVD9', 'DVDRip')
                and (resolution := utils.mediainfo.video.get_resolution_int(self._path, default=0))
        ):
            if resolution <= 480:
                return 'NTSC'
            elif resolution <= 576:
                return 'PAL'

    @property
    def is_complete(self):
        """
        Whether all needed information is known and the string returned by
        :meth:`format` will not contain "UNKNOWN_*"

        This always returns `False` if :attr:`type` is
        :attr:`~.ReleaseType.unknown`.
        """
        if self.type is ReleaseType.unknown:
            return False
        for attr in self._needed_attrs[self.type]:
            if self[attr].startswith('UNKNOWN_'):
                return False
        return True

    async def fetch_info(self, *, webdb, webdb_id, callback=None):
        """
        Fill in information web database

        :param webdb: :class:`~.webdbs.base.WebDbApiBase` instance (see
            :class:`~.webdbs.webdb`)
        :param str webdb_id: Valid ID for `webdb`
        :param callable callback: Function to call after info was fetched; gets
            the instance (`self`) as a keyword argument

        Attempt to set these attributes if they are supported by `webdb`:

          - :attr:`title`
          - :attr:`title_aka`
          - :attr:`type`
          - :attr:`year`
          - :attr:`year_required` (IMDb only)
          - :attr:`country`
          - :attr:`country_required` (IMDb only)

        :return: The method's instance (`self`) for convenience
        """
        await asyncio.gather(
            self._update_attributes(webdb, webdb_id),
            self._update_type(webdb, webdb_id),
            self._update_country(webdb, webdb_id),
            self._update_year_country_required(webdb, webdb_id),
            self._update_group_name(),
        )
        _log.debug('Release name updated with %s info: %s', webdb.label, self)
        if callback is not None:
            callback(self)
        return self

    async def _update_attributes(self, webdb, webdb_id):
        info = await webdb.gather(
            webdb_id,
            'title_english',
            'title_original',
            'year',
        )
        for attr, key in (
            ('title', 'title_original'),
            ('title_aka', 'title_english'),
            ('year', 'year'),
        ):
            # Only overload non-empty values
            if info[key]:
                setattr(self, attr, info[key])

    async def _update_type(self, webdb, webdb_id):
        # Use type from user-selected webdb ID if possible. It is important to keep in mind that
        # webdbs currently don't support episodes, so if guessit detects "episode", the webdb says
        # it's "season". So we only override guessit if the user selected a movie ID or if guessit
        # didn't detect an episode (in which case the webdb is more correct than guessit).
        webdb_type = await webdb.type(webdb_id)
        if webdb_type and (
                webdb_type is ReleaseType.movie
                or self.type is not ReleaseType.episode
        ):
            self.type = webdb_type

    async def _update_country(self, webdb, webdb_id):
        try:
            countries = await webdb.countries(webdb_id)
        except NotImplementedError:
            pass
        else:
            if countries:
                self.country = utils.country.tld(countries[0]).upper()

    async def _update_year_country_required(self, webdb, webdb_id):
        if self.type in (ReleaseType.season, ReleaseType.episode):
            # Find out if there are any TV show name duplicates. If so, require
            # year and/or country code in release name to pin it down.

            @functools.cache
            def normalize_title(title):
                return unidecode.unidecode(title.casefold())

            # Find result with the same title, removing any "smart" matches
            query = utils.webdbs.Query(title=self.title, type=ReleaseType.series)
            results = [
                {
                    'title': normalize_title(result.title),
                    'year': result.year,
                    'countries': await result.countries(),
                }
                for result in await webdb.search(query)
                if normalize_title(self.title) == normalize_title(result.title)
            ]

            # Assemble relevant info
            info = {
                'title': normalize_title(self.title),
                'year': await webdb.year(webdb_id),
                'countries': await webdb.countries(webdb_id),
            }

            def has_duplicates(*attributes):
                combinations = [
                    combine(result, attributes)
                    for result in results
                ]
                relevant_info = {attr: info[attr] for attr in attributes}
                return combinations.count(relevant_info) >= 2

            def combine(result, attributes):
                combined = {}
                for attr in attributes:
                    if result.get(attr):
                        combined[attr] = result[attr]
                return combined

            if has_duplicates('title'):
                if not has_duplicates('title', 'year'):
                    self.year_required = True
                elif not has_duplicates('title', 'countries'):
                    self.country_required = True
                else:
                    self.year_required = True
                    self.country_required = True

    async def _update_group_name(self):
        # For scene releases, the group name may be lowercased. To get the correct group name,
        # (e.g. "hV" or "MiMiC"), ask a predb.
        predb = utils.predbs.MultiPredbApi()
        if await predb.is_scene_release(self.path):
            search_results = await predb.search(self.path)
            if search_results:
                info = ReleaseInfo(search_results[0])
                self.group = info['group']
                _log.debug('Fixed group name: %r: %r', search_results, self.group)

    def format(self, separator=None):
        """
        Assemble all parts into string

        :param separator: Separator to use instead of space

            The typical use case would be ``.``.
        """
        # Separator (usually " " or ".")
        sep = separator if separator is not None else self.separator

        if sep == '.':
            parts = [re.sub(r'\s+-\s+', '.', self.title_with_aka_and_year)]
        else:
            parts = [self.title_with_aka_and_year]

        if self.type in (ReleaseType.season, ReleaseType.episode):
            # If YYYY-MM-DD is included in the title, doon't also add SxxExx.
            if not self.date:
                parts.append(str(self.episodes))
            if self.episode_title:
                parts.append(str(self.episode_title))

        if self.edition:
            parts.extend(self.edition)

        if not self.dvd_resolution:
            parts.append(self.resolution)

        if self.service:
            parts.append(self.service)

        # For DVDs, the resolution is specified as PAL or NTSC and should be next to the source
        # (DVDRip, DVD9, etc).
        if self.dvd_resolution:
            parts.append(self.dvd_resolution)
        parts.append(self.source)

        if self.audio_format:
            parts.append(self.audio_format)

        if self.audio_channels:
            parts.append(self.audio_channels)

        if self.hdr_format:
            parts.append(self.hdr_format)

        parts.append(self.video_format)

        # Parts with multiple values (e.g. `edition`) can have a translation that removes certain
        # values (e.g. "DC") by setting them to an empty string. We also strip any leading/trailing
        # spaces in case upstream adjustments missed them.
        joined = ' '.join(p for part in parts if (p := part.strip()))

        if sep != ' ':
            joined = joined.replace(' ', sep)

        if sep == '.':
            # Replace "&" with "and" before "&" gets removed
            joined = re.sub(r'&', 'and', joined)
            # Remove most non-word characters (e.g. ",") with some exceptions
            # (e.g. "-" is needed for "WEB-DL")
            joined = re.sub(r'[^ \w\.-]', '', joined)
            # Deduplicate "." in case there is a "." at the end of the title
            joined = re.sub(r'\.+', '.', joined)

        if self.group:
            joined += f'-{self.group}'

        return joined


class ReleaseInfo(collections.abc.MutableMapping):
    """
    Parse information from release name or path

    .. note::

       Consider using :class:`~.ReleaseName` instead to get more accurate info
       from the data of existing files.

    :param str release: Release name or path to release content

    :param bool strict: Whether to raise :class:`~.errors.ContentError` if
        `release` looks bad, e.g. an abbreviated scene release file name like
        "tf-foof.mkv"

    If `release` looks like an abbreviated scene file name (e.g.
    "abd-mother.mkv"), the parent directory's name is used if possible.

    Gathered information is provided as a dictionary with the following keys:

      - ``type`` (:class:`~.types.ReleaseType` enum)
      - ``title``
      - ``aka`` (Also Known As; anything after "AKA" in the title)
      - ``country``
      - ``year``
      - ``episodes`` (:class:`~.Episodes` instance)
      - ``episode_title``
      - ``date``
      - ``edition`` (:class:`list` of "Extended", "Uncut", etc)
      - ``resolution``
      - ``service`` (Streaming service abbreviation)
      - ``source`` ("BluRay", "WEB-DL", etc)
      - ``audio_codec`` (Audio codec abbreviation)
      - ``audio_channels`` (e.g. "2.0" or "7.1")
      - ``hdr_format``
      - ``video_codec``
      - ``group``
      - ``has_commentary`` (:class:`bool` or `None` to autodetect)

    Unless documented otherwise above, all values are strings. Unknown values
    are empty strings.
    """

    def __init__(self, path, *, strict=False):
        if strict:
            try:
                utils.predbs.assert_not_abbreviated_filename(str(path))
            except errors.SceneAbbreviatedFilenameError as e:
                raise errors.ContentError(e) from e
        self._path = str(path)
        self._abspath = os.path.abspath(self._path)
        self._dict = {}

    def __contains__(self, name):
        return hasattr(self, f'_get_{name}')

    def __getitem__(self, name):
        if name not in self:
            raise KeyError(name)
        else:
            value = self._dict.get(name, None)
            if value is None:
                value = self[name] = getattr(self, f'_get_{name}')()
            return value

    def __setitem__(self, name, value):
        if not hasattr(self, f'_get_{name}'):
            raise KeyError(name)
        elif hasattr(self, f'_set_{name}'):
            self._dict[name] = getattr(self, f'_set_{name}')(value)
        else:
            self._dict[name] = value

    def __delitem__(self, name):
        if not hasattr(self, f'_get_{name}'):
            raise KeyError(name)
        elif name in self._dict:
            del self._dict[name]

    def __iter__(self):
        return iter(name[5:] for name in dir(type(self))
                    if name.startswith('_get_'))

    def __len__(self):
        return len(tuple(name[5:] for name in dir(type(self))
                         if name.startswith('_get_')))

    def __repr__(self):
        return f'{type(self).__name__}({self._path!r})'

    def copy(self):
        """Return instance copy"""
        cp = type(self)(self._path)
        cp._dict = copy.deepcopy(self._dict)
        return cp

    @property
    def path(self):
        """`path` argument as :class:`str`"""
        return self._path

    @functools.cached_property
    def _guess(self):
        path = self._abspath

        # _log.debug('Running guessit on %r with %r', path, constants.GUESSIT_OPTIONS)
        guess = dict(_guessit.default_api.guessit(path, options=constants.GUESSIT_OPTIONS))
        # _log.debug('Original guess: %r', guess)

        # We try to do our own episode parsing to preserve order and support
        # multiple seasons and episodes
        for name in fs.file_and_parent(path):
            if Episodes.has_episodes_info(name):
                guess['episodes'] = Episodes.from_string(name)
                break
        else:
            # Guessit can parse multiple seasons/episodes to some degree
            seasons = _as_list(guess.get('season'))
            episodes = _as_list(guess.get('episode'))
            string = []
            if seasons:
                string.append(f'S{seasons[0]:02d}')
            string.extend(f'E{e:02d}' for e in episodes)
            guess['episodes'] = Episodes.from_string(''.join(string))

        # If we got an abbreviated file name (e.g. "group-titles01e02.mkv"),
        # guessit can't handle it. Try to find episode information in it.
        if guess['episodes']:
            episodes_string = str(guess['episodes'])
            if (
                'S' in episodes_string
                and 'E' not in episodes_string
                and utils.predbs.is_abbreviated_filename(path)
            ):
                filename = fs.basename(path)
                match = re.search(r'((?i:[SE]\d+)+)', filename)
                if match:
                    episodes = Episodes.from_string(match.group(1))
                    guess['episodes'].update(episodes)
                    _log.debug('Found episodes in abbreviated file name: %r: %r', filename, guess['episodes'])

        return guess

    @property
    def _guessit_options(self):
        return _guessit.default_api.advanced_config

    def _get_type(self):
        if self['date']:
            # We interpret a date as an air date, which should mean it's an
            # episode.
            return ReleaseType.episode

        elif self['episodes']:
            # guessit doesn't differentiate between episodes and season packs.
            # Does any season specify an episode?
            if any(episodes for episodes in self['episodes'].values()):
                return ReleaseType.episode
            # No single episode means it's one or more season packs.
            else:
                return ReleaseType.season
        else:
            return ReleaseType.movie

    _title_split_regex = re.compile(
        r'[ \.](?:'
        r'\d{4}|'  # Year
        r'(?i:[SE]\d+)+|'  # Sxx or SxxExx
        r'((?i:Season|Episode)[ \.]*\d+[ \.]*)+|'
        r')[ \.]'
    )

    @functools.cached_property
    def release_name_params(self):
        """
        Release name without title and year or season/episode info

        This allows us to find stuff in the release name that guessit doesn't
        support without accidentally finding it in the title.
        """
        path_no_ext = fs.strip_extension(self._abspath, only=constants.VIDEO_FILE_EXTENSIONS)

        # Look for year/season/episode info in file and parent directory name
        for name in fs.file_and_parent(path_no_ext):
            match = self._title_split_regex.search(name)
            if match:
                return self._title_split_regex.split(name, maxsplit=1)[-1]

        # Default to the file/parent that contains either " " or "." (without
        # the "." from the extension)
        for name in fs.file_and_parent(path_no_ext):
            if ' ' in name or '.' in name:
                return name

        # Default to file name
        return fs.basename(path_no_ext)

    _title_aka_regex = re.compile(rf'{DELIM}AKA{DELIM}')

    @functools.cached_property
    def _title_parts(self):
        # guessit splits AKA at " - ", so we re-join it
        title_parts = [_as_string(self._guess.get('title', ''))]
        if self._guess.get('alternative_title'):
            title_parts.extend(_as_list(self._guess.get('alternative_title')))
        title = ' - '.join(title_parts)
        title_parts = self._title_aka_regex.split(title, maxsplit=1)

        # guessit recognizes mixed seasons and episodes (e.g. "S02E10S03E05") as
        # part of the title.
        def remove_episodes(string):
            return Episodes.regex.sub('', string)

        if len(title_parts) > 1:
            return {'title': remove_episodes(title_parts[0]),
                    'aka': remove_episodes(title_parts[1])}
        else:
            return {'title': remove_episodes(title_parts[0]),
                    'aka': ''}

    def _get_title(self):
        return self._title_parts['title']

    def _get_aka(self):
        return self._title_parts['aka']

    def _get_year(self):
        return _as_string(self._guess.get('year') or '')

    _country_translation = {
        'UK': re.compile(r'^GB$'),
    }

    def _get_country(self):
        country = utils.country.tld(
            _as_string(self._guess.get('country') or ''),
        ).upper()
        for country_, regex in self._country_translation.items():
            if regex.search(country):
                country = country_
        return country

    def _get_episodes(self):
        if 'episodes' not in self._guess:
            self._guess['episodes'] = Episodes()
        return self._guess['episodes']

    def _set_episodes(self, value):
        # Keep Episodes() object ID. Ensure `value` is not the object in
        # self._guess['episodes'] so we can clear() without losing items in
        # `value`.
        value = dict(value)
        episodes = self._get_episodes()
        episodes.clear()
        episodes.update(value)

    def _get_episode_title(self):
        return _as_string(self._guess.get('episode_title', ''))

    def _get_date(self):
        return _as_string(self._guess.get('date', ''))

    _edition_translation = {
        "Collector's Edition": re.compile(r'Collector'),
        'Criterion Collection': re.compile(r'Criterion'),
        'Deluxe Edition': re.compile(r'Deluxe'),
        'Extended Cut': re.compile(r'Extended'),
        'Special Edition': re.compile(r'Special'),
        'Theatrical Cut': re.compile(r'Theatrical'),
        'Ultimate Cut': re.compile(r'Ultimate'),
    }
    _proper_repack_regex = re.compile(rf'(?:{DELIM}|^)((?i:proper\d*|repack\d*|rerip\d*))(?:{DELIM}|$)')
    _remastered_regex = re.compile(rf'(?:{DELIM}|^)((?i:4k{DELIM}+|)(?i:remaster(?:ed|)|restored))(?:{DELIM}|$)')

    def _get_edition(self):
        edition = _as_list(self._guess.get('edition'))
        for edition_fixed, regex in self._edition_translation.items():
            for i in range(len(edition)):
                if regex.search(edition[i]):
                    edition[i] = edition_fixed

        # Revision (guessit doesn't distinguish between REPACK, PROPER, etc)
        match = self._proper_repack_regex.search(self.release_name_params)
        if match:
            edition.append(match.group(1).upper())

        # Various
        guessit_other = _as_list(self._guess.get('other'))
        if 'Extras' in guessit_other:
            edition.append('Extras')
        if 'Open Matte' in guessit_other:
            edition.append('Open Matte')
        if 'Original Aspect Ratio' in guessit_other:
            edition.append('OAR')
        if 'Dual Audio' in guessit_other:
            edition.append('Dual Audio')
        if '2in1' in guessit_other:
            edition.append('2in1')

        def is_4k_source():
            # guessit only detects remastered, not if it's from 4k
            match = self._remastered_regex.search(self.release_name_params)
            if match:
                remastered_string = match.group(1)
                return '4k' in remastered_string.lower()

        if 'Remastered' in edition and is_4k_source():
            edition[edition.index('Remastered')] = '4k Remastered'
        elif 'Restored' in edition and is_4k_source():
            edition[edition.index('Restored')] = '4k Restored'

        return edition

    def _get_resolution(self):
        return _as_string(self._guess.get('screen_size', ''))

    _streaming_service_regex = re.compile(rf'{DELIM}([A-Z]+){DELIM}(?i:WEB-?(?:DL|Rip))(?:{DELIM}|$)')
    _streaming_service_translation = {
        re.compile(r'(?i:IT)'): 'iT',
        re.compile(r'(?i:4OD)'): 'ALL4',   # 4oD is old name of Channel 4's VOD service
        # Not a streaming service
        re.compile(r'OAR'): '',  # Original Aspect Ratio
        re.compile(r'UHD'): '',
    }

    def _get_service(self):
        def translate(service):
            for regex, abbrev in self._streaming_service_translation.items():
                if regex.search(service):
                    return abbrev
            return service

        service = _as_string(self._guess.get('streaming_service', ''))
        if service:
            # guessit translates abbreviations to full names (NF -> Netflix),
            # but we want abbreviations. Use the same dictionary as guessit.
            translation = self._guessit_options['streaming_service']
            for full_name, aliases in translation.items():
                if service.casefold().strip() == full_name.casefold().strip():
                    # `aliases` is either a string or a list of strings and
                    # other objects.
                    if isinstance(aliases, str):
                        return translate(aliases)
                    else:
                        # Find shortest string
                        aliases = (a for a in aliases if isinstance(a, str))
                        return translate(sorted(aliases, key=len)[0])

        # Default to manual detection
        match = self._streaming_service_regex.search(self.release_name_params)
        if match:
            return translate(match.group(1))

        return ''

    _source_translation = {
        re.compile(r'(?i:ultra hd blu-?ray)') : 'UHD BluRay',
        re.compile(r'(?i:blu-?ray)')          : 'BluRay',
        re.compile(r'(?i:hd-?dvd)')           : 'HDDVD',
        re.compile(r'(?i:dvd-?rip)')          : 'DVDRip',
        re.compile(r'(?i:tv-?rip)')           : 'TVRip',
        re.compile(r'(?i:web-?dl)')           : 'WEB-DL',
        re.compile(r'(?i:web-?rip)')          : 'WEBRip',
        re.compile(r'(?i:web)')               : 'WEB-DL',
    }
    _web_source_regex = re.compile(rf'(?:{DELIM}|^)((?i:web-?(?:dl|rip)))(?:{DELIM}|$)', flags=re.IGNORECASE)

    def _get_source(self):
        def get_translated_source(*sources):
            if not sources:
                return ''
            # guessit can provide one or multiple sources, e.g. ["DVD", "HD-DVD"].
            # We have to find the most relevant source, e.g. "HD-DVD" over "DVD".
            for regex, source_fixed in self._source_translation.items():
                for src in sources:
                    if regex.search(src):
                        return source_fixed
            return sources[0]

        guessed_other = _as_list(self._guess.get('other'))
        guessed_sources = _as_list(self._guess.get('source'))
        source = get_translated_source(*guessed_sources)

        if source.startswith('WEB'):
            # guessit doesn't distinguish between WEB-DL and WEBRip.
            match = self._web_source_regex.search(self.release_name_params)
            if match:
                source = get_translated_source(match.group(1))

        elif not source.endswith('Rip') and 'Rip' in guessed_other and source != 'BluRay':
            # For "DVDRip", guess is {"source": "DVD", "other": "Rip"}, which we translate to
            # "DVDRip". Same thing for "WEBRip". But "BDRip" is actually called "BluRay", because
            # why would any naming system must be chaotic.
            source = f'{source}Rip'

        elif source == 'DVD':
            # guessit doesn't distinguish between DVD5 and DVD9.
            if 'DVD9' in self.release_name_params:
                source = 'DVD9'
            elif 'DVD5' in self.release_name_params:
                source = 'DVD5'

        elif match := re.search(rf'(?:{DELIM}|^)(BD\d*)(?:{DELIM}|$)', self.release_name_params):
            # guessit doesn't detect disc formats. BD25/50 are detected as "Blu-ray" and BD66/100
            # aren't detected at all. This finds "BD25/50/..." in the original path.
            source = match.group(1)

        # Detect Remux and Hybrid.
        if 'Remux' in guessed_other and 'WEB' not in source and 'Rip' not in source:
            source = f'{source} Remux'
        if 'Hybrid' in guessed_other:
            source = f'Hybrid {source}'

        # Dedupe spaces.
        source = ' '.join(source.split())

        return source

    _audio_codec_translation = {
        re.compile(r'^AC-?3')             : 'DD',
        re.compile(r'Dolby Digital$')     : 'DD',
        re.compile(r'^E-?AC-?3')          : 'DDP',
        re.compile(r'Dolby Digital Plus') : 'DDP',
        re.compile(r'TrueHD')             : 'TrueHD',
        re.compile(r'Dolby Atmos')        : 'Atmos',
        re.compile(r'Master Audio')       : 'MA',
        re.compile(r'High Resolution')    : 'HR',
        re.compile(r'Extended Surround')  : 'ES',
        re.compile(r'High Efficiency')    : 'HE',
        re.compile(r'Low Complexity')     : 'LC',
        re.compile(r'High Quality')       : 'HQ',
    }

    def _get_audio_codec(self):
        audio_codec = _as_string(self._guess.get('audio_codec'))
        if not audio_codec:
            return ''
        else:
            if isinstance(audio_codec, str):
                infos = [audio_codec]
            else:
                infos = audio_codec

            parts = []
            for info in infos:
                for regex,abbrev in self._audio_codec_translation.items():
                    if regex.search(info):
                        parts.append(abbrev)
                        continue

            # Join translations, default to what guessit detected
            audio_codec = ' '.join(parts or infos)

            # Final adjustments
            audio_codec = re.sub(r'DDP? TrueHD', 'TrueHD', audio_codec)
            audio_codec = re.sub(r'DDP? Atmos', 'Atmos', audio_codec)

            return audio_codec

    _audio_channels_regex = re.compile(rf'{DELIM}(\d\.\d){DELIM}')

    def _get_audio_channels(self):
        audio_channels = _as_string(self._guess.get('audio_channels', ''))
        if not audio_channels:
            match = self._audio_channels_regex.search(self.release_name_params)
            if match:
                return match.group(1)
        return audio_channels

    _hdr_translation = {
        re.compile(rf'(?:{DELIM}|^)(?i:DV|DoVi|Dolby{DELIM}Vision)(?:{DELIM}|$)'): 'DV',
        re.compile(rf'(?:{DELIM}|^)(?i:HDR10\+)(?:{DELIM}|$)'): 'HDR10+',
        re.compile(rf'(?:{DELIM}|^)(?i:HDR10)(?!:\+)(?:{DELIM}|$)'): 'HDR10',
        re.compile(rf'(?:{DELIM}|^)(?i:HDR)(?!:10\+)(?:{DELIM}|$)'): 'HDR',
    }

    def _get_hdr_format(self):
        for regex, hdr_format in self._hdr_translation.items():
            if regex.search(self.release_name_params):
                return hdr_format
        return ''

    _x264_regex = re.compile(rf'(?:{DELIM}|^)(?i:x264)(?:{DELIM}|$)')
    _x265_regex = re.compile(rf'(?:{DELIM}|^)(?i:x265)(?:{DELIM}|$)')

    def _get_video_codec(self):
        video_codec = _as_string(self._guess.get('video_codec', ''))
        if video_codec == 'H.264' and self._x264_regex.search(self.release_name_params):
            return 'x264'

        elif video_codec == 'H.265' and self._x265_regex.search(self.release_name_params):
            return 'x265'

        return video_codec

    def _get_group(self):
        return _as_string(self._guess.get('release_group', ''))

    _has_commentary_regex = re.compile(rf'{DELIM}(?i:plus{DELIM}+comm|commentary){DELIM}')

    def _get_has_commentary(self):
        if self._guess.get('has_commentary', None) is None:
            self._guess['has_commentary'] = \
                bool(self._has_commentary_regex.search(self.release_name_params))
        return self._guess['has_commentary']

    def _set_has_commentary(self, value):
        if value is None:
            self._guess['has_commentary'] = None
        else:
            self._guess['has_commentary'] = bool(value)


class Episodes(dict):
    """
    :class:`dict` subclass that maps season numbers to lists of episode numbers

    All keys and values are :class:`str` objects. All episodes from a season are
    indicated by an empty sequence. For episodes from any sason, the key is an
    empty string.

    This class accepts the same arguments as :class:`dict`.

    To provide seasons as keyword arguments, you need to prefix "S" to each
    keyword. This is because numbers can't be keyword arguments, but it also
    looks nicer.

    >>> e = Episodes({"1": ["1", "2", "3"], "2": []})
    >>> e.update(S01=[3, "4"], S3=range(2, 4), s05=[], S=[10, "E11", 12])
    >>> e
    >>> Episodes({'1': ['1', '2', '3', '4'], '2': [], '3': ['2', '3'], '5': [], '': ['10', '11', '12']})
    """

    regex = re.compile(rf'(?:{DELIM}|^)((?i:[SE]\d+)+)(?:{DELIM}|$)')
    """Regular expression that matches "S01E02"-like episode information"""

    @classmethod
    def has_episodes_info(cls, string):
        """Whether `string` contains "S01E02"-like episode information"""
        return bool(cls.regex.search(string))

    _is_episodes_info_regex = re.compile(r'^(?i:[SE]\d+)+$')

    @classmethod
    def is_episodes_info(cls, string):
        """Whether `string` is "S01E02"-like episode information and nothing else"""
        return bool(cls._is_episodes_info_regex.search(string))

    @classmethod
    def from_string(cls, value):
        """
        Create instance from release name or string that contains "Sxx" and "Exx"

        Examples:

            >>> Episodes.from_string('foo.E01 bar')
            {'': ('1',)}
            >>> Episodes.from_string('foo E01E2.bar')
            {'': ('1', '2')}
            >>> Episodes.from_string('foo.bar.E01E2S03')
            {'': ('1', '2'), '3': ()}
            >>> Episodes.from_string('E01E2S03E04E05.baz')
            {'': ('1', '2'), '3': ('4', '5')}
            >>> Episodes.from_string('S09E08S03E06S9E1')
            {'9': ('1', '8',), '3': ('6',)}
            >>> Episodes.from_string('E01S03E06.bar.E02')
            {'': ('1', '2',), '3': ('6',)}
        """
        def extract_number(string):
            n = ''.join(c for c in string if c in '0123456789').lstrip('0')
            return '0' if n == '' else n

        def split_episodes(string):
            return {extract_number(e) for e in string.split('E') if e.strip()}

        # Extract episode information to get "S..E.." string without any other
        # characters. The original value might have delimiters,
        # e.g. "...S09E14-E15...", and we want "S09E14E15".
        episodes_string = ''.join(re.findall(
            (
                r'(?i:[^SE\d]*|^)'
                r'((?i:[SE]\d+)+)'
                r'(?i:[^SE\d]+|$)'
            ),
            str(value).upper(),
        ))

        seasons = collections.defaultdict(lambda: set())
        for part in (k for k in episodes_string.split('S') if k):
            season = re.sub(r'E.*$', '', part)
            season = str(int(season)) if season else ''
            episodes = re.sub(r'^\d+', '', part)
            episodes = split_episodes(episodes) if episodes else ()
            seasons[season].update(episodes)

        args = {season: tuple(natsort.natsorted(episodes))
                for season, episodes in natsort.natsorted(seasons.items())}
        return cls(args)

    @classmethod
    def from_sequence(cls, sequence):
        """
        Combine episode information from multiple strings

        Examples:

            >>> Episodes.from_sequence(['foo.S01E01.bar', 'hello'])
            {'1': ('1',)}
            >>> Episodes.from_sequence(['foo.S01E01.bar', 'bar.S01E02.baz'])
            {'1': ('1', '2')}
        """
        episodes = Episodes()
        for string in sequence:
            eps = cls.from_string(string)
            for season in eps:
                if season in episodes:
                    episodes[season] += eps[season]
                else:
                    episodes[season] = eps[season]
        return episodes

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._set(*args, **kwargs)

    def update(self, *args, clear=False, **kwargs):
        """
        Set specific episodes from specific seasons, remove all other episodes and
        seasons

        :params bool clear: Whether to remove all seasons and episodes first
        """
        if clear:
            self.clear()
        self._set(*args, **kwargs)

    def _set(self, *args, **kwargs):
        # Validate all values before applying any changes
        validated = {}
        update = dict(*args, **kwargs)
        for season, episodes in update.items():
            season = self._normalize_season(season)
            if not isinstance(episodes, collections.abc.Iterable) or isinstance(episodes, str):
                episodes = [self._normalize_episode(episodes)]
            else:
                episodes = [self._normalize_episode(e) for e in episodes]

            if season in validated:
                validated[season].extend(episodes)
            else:
                validated[season] = episodes

        # Set validated values
        for season, episodes in validated.items():
            if season in self:
                self[season].extend(episodes)
            else:
                self[season] = episodes

            # Remove duplicates
            self[season][:] = set(self[season])

            # Sort naturally
            self[season].sort(key=natsort.natsort_key)

    def _normalize_season(self, value):
        return self._normalize(value, name='season', prefix='S', empty_string_ok=True)

    def _normalize_episode(self, value):
        return self._normalize(value, name='episode', prefix='E', empty_string_ok=False)

    def _normalize(self, value, name, *, prefix=None, empty_string_ok=False):
        if isinstance(value, int):
            if value >= 0:
                return str(value)

        elif isinstance(value, str):
            if value == '' and empty_string_ok:
                return str(value)

            if value.isdigit():
                return str(int(value))

            if prefix and len(value) >= len(prefix):
                prefix_ = value[:len(prefix)].casefold()
                if prefix_ == prefix.casefold():
                    actual_value = value[len(prefix):]
                    return self._normalize(
                        actual_value,
                        name=name,
                        prefix=None,
                        empty_string_ok=empty_string_ok,
                    )

        raise TypeError(f'Invalid {name}: {value!r}')

    def remove_specific_episodes(self):
        """Remove episodes from each season, leaving only complete seasons"""
        for season in tuple(self):
            if season:
                self[season] = ()
            else:
                del self[season]

    def __repr__(self):
        return f'{type(self).__name__}({dict(self)!r})'

    def __str__(self):
        parts = []
        for season, episodes in sorted(self.items()):
            if season:
                parts.append(f'S{season:0>2}')
            parts.extend(f'E{episode:0>2}' for episode in episodes)
        return ''.join(parts)


def _as_list(value):
    if not value:
        return []
    elif isinstance(value, str):
        return [value]
    elif isinstance(value, list):
        return list(value)
    else:
        return [value]

def _as_string(value):
    if not value:
        return ''
    elif isinstance(value, str):
        return value
    elif isinstance(value, list):
        return ' '.join(value)
    else:
        return str(value)
