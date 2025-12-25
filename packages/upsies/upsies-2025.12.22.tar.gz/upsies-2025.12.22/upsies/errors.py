"""
Exception classes

Abstraction layers should raise one of these exceptions if an error message
should be displayed to the user. If the programmer made a mistake, any
appropriate builtin exception (e.g. :class:`ValueError`, :class:`TypeError`) or
:class:`RuntimeError` should be raised.

For example, :func:`~.utils.http.get` always raises :class:`RequestError`,
regardless of which library is used or what went wrong, except when something
like caching fails, which is most likely due to a bug.
"""

import json

_NO_DEFAULT_VALUE = object()


class UpsiesError(Exception):
    """Base class for all exceptions raised by upsies"""

    def __eq__(self, other):
        if isinstance(other, type(self)) and str(other) == str(self):
            return True
        else:
            return NotImplemented


class ConfigError(UpsiesError):
    """Error while reading/writing config file or setting config file option"""


class ConfigValueError(ConfigError, ValueError):
    """Configuration option is set to an invalid value"""

    def __init__(self, message, *, path=()):
        if path:
            super().__init__('.'.join(path) + f': {message}')
        else:
            super().__init__(message)
        self.message = message
        self.path = path


class UnknownConfigError(ConfigError, KeyError):
    """
    Unknown section, subsection or option accessed

    Because this exception is raised in ``__getitem__`` methods, it is a subclass of
    :class:`KeyError`. That means the error message is quoted because it is supposed to be a key. An
    actual error message is available via the :attr:`message` attribute. Likewise, the section,
    subsection or option name is available as :attr:`name`.
    """

    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.message = f'Unknown config: {name}'

class UnknownSectionConfigError(UnknownConfigError):
    """Unknown section accessed (see :class:`UnknownConfigError`)"""

    def __init__(self, section_name):
        super().__init__(section_name)
        self.message = f'Unknown config section: {section_name}'


class UnknownSubsectionConfigError(UnknownConfigError):
    """Unknown subsection accessed (see :class:`UnknownConfigError`)"""

    def __init__(self, subsection_name):
        super().__init__(subsection_name)
        self.message = f'Unknown config subsection: {subsection_name}'


class UnknownOptionConfigError(UnknownConfigError):
    """Unknown option accessed (see :class:`UnknownConfigError`)"""

    def __init__(self, option_name):
        super().__init__(option_name)
        self.message = f'Unknown config option: {option_name}'


class UiError(UpsiesError):
    """Fatal user interface error that cannot be handled by the UI itself"""


class DependencyError(UpsiesError):
    """Some external tool is missing (e.g. ``mediainfo``)"""


class ContentError(UpsiesError):
    """
    Something is wrong with user-provided content, e.g. no video files in the
    given directory or no permission to read
    """


class ProcessError(UpsiesError):
    """Executing subprocess failed"""


class RequestError(UpsiesError):
    """Network request failed"""
    def __init__(self, msg, url='', headers={}, status_code=None, text=''):
        super().__init__(msg)
        self._url = url
        self._headers = headers
        self._status_code = status_code
        self._text = text

    @property
    def url(self):
        """URL that produced this exception"""
        return self._url

    @property
    def headers(self):
        """HTTP headers from server response or empty `dict`"""
        return self._headers

    @property
    def status_code(self):
        """HTTP status code (e.g. 404) or `None`"""
        return self._status_code

    @property
    def text(self):
        """Response string if available"""
        return self._text

    def json(self, default=_NO_DEFAULT_VALUE):
        """
        Parse the :attr:`text` as JSON

        :param default: Return value if :attr:`text` is not valid JSON

        :raise RequestError: if :attr:`text` is not proper JSON and `default` is
            not given
        """
        try:
            return json.loads(self.text)
        except ValueError as e:
            if default is _NO_DEFAULT_VALUE:
                raise RequestError(f'Malformed JSON: {self.text}: {e}') from e
            else:
                return default


class TfaRequired(UpsiesError):
    """Raised by :meth:`.TrackerBase._login` if 2FA one-time password is required"""


class TimeoutError(RequestError):
    """
    Raised when something took too long

    :param seconds: How many seconds we waited before giving up
    :param resource: What we were waiting for (e.g. URL)
    """

    def __init__(self, seconds, *, resource=None):
        message = f'Timeout after {seconds} second' + ('' if seconds == 1 else 's')
        if resource:
            message = f'{resource}: {message}'
        super().__init__(message)


class FoundDupeError(RequestError):
    """
    Tried to upload files that have already been uploaded

    :param filenames: Sequence of file names that have already been uploaded
    """
    def __init__(self, filenames):

        if not filenames:
            msg = ['Potential duplicate files found']

        else:
            files_count = len(filenames)
            if files_count != 1:
                msg = [f'{files_count} potential duplicate files found']
            else:
                msg = ['1 potential duplicate file found']

            msg.append(':\n - ')
            msg.append('\n - '.join(filenames))

        super().__init__(''.join(msg))


class AnnounceUrlNotSetError(RequestError):
    """Announce URL is required but not provided by the user"""
    def __init__(self, *_, tracker):
        super().__init__('Announce URL is not set')
        self._tracker = tracker

    @property
    def tracker(self):
        """:attr:`~.TrackerBase` instance that raised this exception"""
        return self._tracker


class RequestedNotFoundError(RequestError):
    """
    Something was requested and not found

    This is different from a :class:`~.RequestError` that was raised because the
    service is down, authentication failed, etc.

    :param requested: Human-readable representation of the requested thing.
    """
    def __init__(self, requested):
        self._requested = requested
        super().__init__(f'Not found: {requested}')

    @property
    def requested(self):
        """The `requested` argument from initialization"""
        return self._requested


class ImageError(UpsiesError):
    """Any errors related to image creation or manipulation"""


class ScreenshotError(ImageError):
    """Screenshot creation failed"""


class ImageResizeError(ImageError):
    """Image resizing failed"""


class ImageOptimizeError(ImageError):
    """Image optimization failed"""


class ImageConvertError(ImageError):
    """Image optimization failed"""


class TorrentCreateError(UpsiesError):
    """Torrent file creation failed"""


class TorrentAddError(UpsiesError):
    """Adding torrent to client failed"""


def DaemonProcessError(exception, original_traceback):
    """
    Exception from a :class:`~.DaemonProcess` target

    This exception has an `original_traceback` attribute that provides the trace of the `exception`.
    """
    exception.original_traceback = f'Daemon process traceback:\n{original_traceback.strip()}'
    return exception


class DaemonProcessTerminated(UpsiesError):
    """Raised by a :class:`~.DaemonProcess` target if it received :class:`~.MsgType.terminate`"""


class SceneError(UpsiesError):
    """Base class for scene-related errors"""

class SceneRenamedError(SceneError):
    """Renamed scene release"""
    def __init__(self, *, original_name, existing_name):
        super().__init__(f'{existing_name} should be named {original_name}')
        self._original_name = original_name
        self._existing_name = existing_name

    @property
    def original_name(self):
        """What the release name should be"""
        return self._original_name

    @property
    def existing_name(self):
        """What the release name is"""
        return self._existing_name

class SceneFileSizeError(SceneError):
    """Scene release file size differs from original release"""
    def __init__(self, filename, *, original_size, existing_size):
        super().__init__(f'{filename} should be {original_size} bytes, not {existing_size}')
        self._filename = filename
        self._original_size = original_size
        self._existing_size = existing_size

    @property
    def filename(self):
        """Name of the file in the scene release"""
        return self._filename

    @property
    def original_size(self):
        """Size of the file in the scene release"""
        return self._original_size

    @property
    def existing_size(self):
        """Size of the file in the local file system"""
        return self._existing_size

class SceneMissingInfoError(UpsiesError):
    """Missing information about a file from a scene release"""
    def __init__(self, file_name):
        super().__init__(f'Missing information: {file_name}')

class SceneAbbreviatedFilenameError(UpsiesError):
    """
    An abbreviated scene file name (e.g. foo-bar.mkv) was provided

    These contain almost no information and should always be provided via a
    properly named parent directory.
    """
    def __init__(self, file_name):
        super().__init__(f'Abbreviated scene file name is verboten: {file_name}')


class RuleBroken(UpsiesError):
    """
    Raised by :meth:`.TrackerRuleBase.check` if a rule is broken
    """

    def __init__(self, reason):
        super().__init__(f'Rule broken: {reason}')


class BannedGroup(RuleBroken):
    """Raised by :meth:`.BannedGroup.check` if release group is banned"""

    def __init__(self, group, additional_info=None):
        if additional_info:
            super().__init__(f'Banned group: {group} ({additional_info})')
        else:
            super().__init__(f'Banned group: {group}')
