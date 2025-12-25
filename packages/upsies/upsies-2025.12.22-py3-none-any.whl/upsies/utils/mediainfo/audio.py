import functools
import os
import re

from ... import errors, utils

import logging  # isort:skip
_log = logging.getLogger(__name__)

langcodes = utils.LazyModule(module='langcodes', namespace=globals())

NO_DEFAULT_VALUE = object()


def has_dual_audio(path, default=NO_DEFAULT_VALUE):
    """
    Return `True` if `path` contains multiple audio tracks with different languages and one of
    them is English, `False` otherwise

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    try:
        audio_tracks = utils.mediainfo.lookup(path, ('Audio',))
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        languages = set()
        for track in audio_tracks:
            title = track.get('Title', '')
            language = track.get('Language', '')
            if (
                    # Not a commentary track.
                    'commentary' not in title.lower()
                    and language not in (
                        '',     # No language tag found
                        'und',  # Unknown language
                        'zxx',  # No language (e.g. only music score)
                    )
            ):
                # `language` is 2-letter ISO 639-1 or 3-letter ISO 639-2 code with optional ISO
                # 3166-1 country code separated by a dash if available (e.g. en, en-US, en-CN).
                # https://mediaarea.net/en/MediaInfo/Support/Fields
                languages.add(language.casefold()[:2])
        return len(languages) > 1


def has_language(path, default=NO_DEFAULT_VALUE):
    """
    Return `True` if `path` has one or more audio tracks and the language of the main audio
    track is not "zxx"

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    try:
        default_audio_track = utils.mediainfo.lookup(path, ('Audio', 'DEFAULT'))
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        return default_audio_track.get('Language', '') != 'zxx'
    return True


def has_commentary(path, default=NO_DEFAULT_VALUE):
    """
    Return `True` if `path` has an audio track with "Commentary" (case-insensitive) in its
    ``Title`` field, `False` otherwise

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    try:
        audio_tracks = utils.mediainfo.lookup(path, ('Audio',))
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        for track in audio_tracks:
            if _is_commentary(track):
                return True
        return False


def _is_commentary(track):
    title = track.get('Title', '')
    return bool(re.search(r'\b(commentary|comments)\b', title, flags=re.IGNORECASE))


def get_audio_languages(path, default=NO_DEFAULT_VALUE, *, exclude_commentary=True):
    """
    Return sequence of two-letter (ISO 639-1) language codes from audio tracks

    If an audio track does not specify a language, use `default` if specified, otherwise ignore that
    audio track.

    :param str path: Path to release files

        For directories, the return value of :func:`find_main_video` is used.

        BDMV and VIDEO_TS releases are supported. For multi-disc releases (i.e. `path` contains multiple
        directories with "BDMV" or "VIDEO_TS" subdirectories), languages from all discs are accumulated.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :param exclude_commentary: Ignore any track with a ``"Title"`` field that contains the string
        "commentary" (case-insensitive)

        .. warning:: Commentary detection is not supported for BDMV and VIDEO_TS releases.

    :raise ContentError: if anything goes wrong
    """
    languages = []

    if utils.disc.is_disc(path, multidisc=True):
        # BDMV or VIDEO_TS
        languages.extend(get_audio_languages_from_discs(
            path,
            default=default,
            exclude_commentary=exclude_commentary,
        ))

    else:
        # Regular video file(s)
        languages.extend(
            get_audio_languages_from_mediainfo(
                path,
                default=default,
                exclude_commentary=exclude_commentary,
            )
        )

    return tuple(languages)


def get_audio_languages_from_mediainfo(path, default=NO_DEFAULT_VALUE, *, exclude_commentary=True):
    """
    Return sequence of BCP47 language codes from audio tracks

    This function supports regular video files (.mkv, .mp4, .avi, etc).

    See :func:`get_audio_languages`.
    """
    try:
        audio_tracks = utils.mediainfo.lookup(path, ('Audio',))
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        languages = []
        for track in audio_tracks:
            if not exclude_commentary or not _is_commentary(track):
                language = re.sub(r'^([a-zA-Z]+).*$', r'\1', track.get('Language', ''))
                if language:
                    # `language` should be in format "LANGUAGE" or "LANGUAGE-REGION" or "LANGUAGE /
                    # LANGUAGE" (I don't know what that means), where each "LANGUAGE" and "REGION"
                    # are two-character codes (probably BCP47). But we don't know for sure, so we
                    # fall back to adding the language as is if it's an invalid code.
                    try:
                        langcode = langcodes.Language.get(language)
                    except ValueError:
                        _log.debug('No such language code: %r', language)
                        languages.append(language)
                    else:
                        languages.append(langcode.language)
                elif default is not NO_DEFAULT_VALUE:
                    languages.append(default)
        return tuple(languages)


@functools.cache
def get_audio_languages_from_discs(path, default=NO_DEFAULT_VALUE, *, exclude_commentary=True):
    """
    Return sequence of two-letter (ISO 639-1) language codes from audio tracks

    This function reads audio languages from .MPLS or .IFO playlists in a "VIDEO_TS" or "BDMV"
    subdirectory. `path` may be a multidisc release.

    See :func:`get_audio_languages`.
    """
    if not os.path.exists(path):
        if default is NO_DEFAULT_VALUE:
            raise errors.ContentError(f'No such file or directory: {path}')
        else:
            return default
    else:
        if utils.disc.is_bluray(path, multidisc=True):
            disc_module = utils.disc.bluray
        elif utils.disc.is_dvd(path, multidisc=True):
            disc_module = utils.disc.dvd
        else:
            _log.debug('Not a disc path: %r', path)
            return ()

        languages = []
        for disc_path in disc_module.get_disc_paths(path):
            main_playlists = tuple(
                playlist
                for playlist in disc_module.get_playlists(disc_path)
                if playlist.is_main
            )
            for playlist in main_playlists:
                languages.extend(get_audio_languages_from_mediainfo(
                    playlist.filepath,
                    default=default,
                    exclude_commentary=exclude_commentary,
                ))
            _log.debug('Audio languages from disc tree: %r', languages)
        return tuple(languages)


_audio_format_translations = (
    # (<format>, <<key>:<regex> dictionary>)
    # - All <regex>s must match each <key> to identify <format>.
    # - All identified <format>s are appended (e.g. "TrueHD Atmos").
    # - {<key>: None} means <key> must not exist.
    ('AAC', {'Format': re.compile(r'^AAC$')}),
    # NOTE: The "Format" field can be "AC-3" even if the "CodecID" field is "A_EAC3". "CodecID"
    # seems to be more accurate.
    ('DD', {'Format': re.compile(r'^AC.?3')}),
    ('DDP', {'Format': re.compile(r'^E.?AC.?3')}),
    ('TrueHD', {'Format': re.compile(r'MLP ?FBA')}),
    ('TrueHD', {'Format_Commercial_IfAny': re.compile(r'TrueHD')}),
    ('Atmos', {'Format_Commercial_IfAny': re.compile(r'Atmos')}),
    ('DTS', {'Format': re.compile(r'^DTS$'), 'Format_Commercial_IfAny': None}),
    ('DTS-ES', {'Format_Commercial_IfAny': re.compile(r'DTS-ES')}),
    ('DTS-HD', {'Format_Commercial_IfAny': re.compile(r'DTS-HD(?! Master Audio)')}),
    ('DTS-HD MA', {
        'Format_Commercial_IfAny': re.compile(r'DTS-HD Master Audio'),
        'Format_AdditionalFeatures': re.compile(r'XLL$'),
    }),
    ('DTS:X', {'Format_AdditionalFeatures': re.compile(r'XLL X')}),
    ('FLAC', {'Format': re.compile(r'FLAC')}),
    ('MP2', {'CodecID': re.compile(r'A_MPEG/L2')}),
    ('MP3', {'CodecID': re.compile(r'A_MPEG/L3')}),
    ('Vorbis', {'Format': re.compile(r'\bVorbis\b')}),
    ('Vorbis', {'Format': re.compile(r'\bOgg\b')}),
    ('Opus', {'Format': re.compile(r'\bOpus\b')}),
    ('PCM', {'Format': re.compile(r'PCM')}),
)

@functools.cache
def get_audio_format(path, default=NO_DEFAULT_VALUE):
    """
    Return audio format of default audio track (e.g. "AAC", "DDP Atmos") or empty string if
    `path` has no audio track

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    try:
        # Check if `path` has any audio tracks at all.
        if 'Audio' in utils.mediainfo.get_tracks(path):
            audio_track = utils.mediainfo.lookup(path, ('Audio', 'DEFAULT'))
        else:
            _log.debug('No audio track found: %r', path)
            return ''

    except errors.ContentError as e:
        # `path` does not exist.
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default

    else:

        def is_match(regexs, audio_track):
            for key, regex in regexs.items():
                if regex is None:
                    if key in audio_track:
                        # `key` must not exists but it does exist: No match.
                        return False
                elif key not in audio_track:
                    # `key` does not exist.
                    return False
                elif not regex.search(audio_track[key]):
                    # `key` exists, but its value does not match `regex`.
                    return False
            # All `regexs` match and no forbidden keys in `audio_track`.
            return True

        parts = []
        for fmt, regexs in _audio_format_translations:
            if fmt not in parts and is_match(regexs, audio_track):
                parts.append(fmt)

        if parts:
            return ' '.join(parts)

        elif default is NO_DEFAULT_VALUE:
            raise errors.ContentError('Unable to detect audio format')

        else:
            _log.debug('Failed to detect audio format, falling back to default: %s', default)
            return default


_audio_channels_translations = (
    ('1.0', re.compile(r'^1$')),
    ('2.0', re.compile(r'^2$')),
    ('2.0', re.compile(r'^3$')),
    ('2.0', re.compile(r'^4$')),
    ('2.0', re.compile(r'^5$')),
    ('5.1', re.compile(r'^6$')),
    ('5.1', re.compile(r'^7$')),
    ('7.1', re.compile(r'^8$')),
    ('7.1', re.compile(r'^9$')),
    ('7.1', re.compile(r'^10$')),
)

def get_audio_channels(path, default=NO_DEFAULT_VALUE):
    """
    Return audio channels of default audio track (e.g. "5.1") or empty_string
    (e.g. if `path` has no audio track)

    :param str path: Path to video file

        For directories, the return value of :func:`find_main_video` is used.

    :param default: Return value if `path` doesn't exist, raise :exc:`~.ContentError` if not
        provided

    :raise ContentError: if anything goes wrong
    """
    try:
        audio_track = utils.mediainfo.lookup(path, ('Audio', 'DEFAULT'))
    except errors.ContentError as e:
        if default is NO_DEFAULT_VALUE:
            raise e
        else:
            return default
    else:
        audio_channels = ''
        channels = audio_track.get('Channels', '')
        for achan, regex in _audio_channels_translations:
            if regex.search(channels):
                audio_channels = achan
                break
        return audio_channels
