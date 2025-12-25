"""
String formatting and parsing
"""

import os
import re
import sys

from .. import errors, utils

import logging  # isort:skip
_log = logging.getLogger(__name__)


_max_nfo_size = 1048576

def read_nfo(path, *, strip=False):
    """
    Recursively search directory for ``*.nfo`` files and read the first one found

    `path` may also be an nfo file.

    The nfo file is decoded with :func:`decode_nfo`.

    Files larger than 1 MiB are ignored.

    If no ``*.nfo`` file is found, return `None`.

    :param bool strip: See :func:`decode_nfo`

    :raise ContentError: if the nfo file is not readable
    """
    if os.path.isdir(path):
        # Look only for *.nfo files.
        extensions = ('nfo', 'NFO')
    else:
        # `path` is a file. Ignore its extension.
        extensions = ()

    # Try all *.nfo files before raising an exception. We don't want to raise on the first file if
    # the second file is perfectly fine.
    failures = []
    for nfo_filepath in utils.fs.file_list(path, extensions=extensions):
        try:
            if os.path.getsize(nfo_filepath) <= _max_nfo_size:
                with open(nfo_filepath, 'rb') as f:
                    return decode_nfo(f.read(), strip=strip)
        except OSError as e:
            failures.append((
                nfo_filepath,
                e.strerror if e.strerror else str(e),
            ))

    if failures:
        nfo_filepath, msg = failures[0]
        raise errors.ContentError(f'Failed to read nfo: {nfo_filepath}: {msg}')


def decode_nfo(bytes, *, strip=False):
    r"""
    Return decoded `bytes`

    Try to decode as UTF-8 first. If that fails, decode as CP437 and replace invalid characters with
    "�" (U+FFFD).

    All line breaks (e.g. CR+LF) are converted to "\n".

    :param bool strip: Whether to remove whitespace at the beginning and end

        .. note:: To preserve ASCII art, spaces at the beginning of the first
                  non-empty line are kept.
    """
    try:
        text = bytes.decode('utf8', 'strict')
    except UnicodeDecodeError:
        text = bytes.decode('cp437', 'replace')

    # Replace all line breaks (e.g. CR+LF) with "\n".
    # NOTE: str.splitlines() does not preserve trailing line breaks.
    for linebreak in ('\r\n', '\r'):
        text = text.replace(linebreak, '\n')

    if strip:
        # Remove any whitespace at the end.
        text = text.rstrip()
        # Remove empty lines at the beginning while keeping any leading spaces
        # on the first non-empty line to preserve ASCII art.
        text = re.sub(r'^\s*?\n(\s*)', r'\1', text)

    return text


_capitalize_regex = re.compile(r'(\s*)(\S+)(\s*)')

def capitalize(text):
    """
    Capitalize each word in `text`

    Unlike :meth:`str.title`, only words at in front of a space or at the
    beginning of `text` are capitalized.
    """
    return ''.join(
        match.group(1) + match.group(2).capitalize() + match.group(3)
        for match in re.finditer(_capitalize_regex, text)
    )


def star_rating(rating, max_rating=10):
    """
    Return star rating string with the characters "★" (U+2605), "⯪" (U+2BEA) and
    "☆" (U+2605)

    :param float,int rating: Number between 0 and `max_rating`
    :param float,int max_rating: Maximum rating
    """
    import math
    rating = min(max_rating, max(0, rating))
    left = '\u2605' * math.floor(rating)
    if rating >= max_rating:
        middle = ''
    # Avoid floating point precision issues by rounding to 1 digit after comma
    elif round(rating % 1, 1) <= 0.3:
        middle = '\u2606'  # Empty star
    elif round(rating % 1, 1) < 0.7:
        middle = '\u2bea'  # Half star
    else:
        middle = '\u2605'  # Full star
    right = '\u2606' * (math.ceil(max_rating - rating) - 1)
    return f'{left}{middle}{right}'


if sys.version_info >= (3, 9, 0):
    def remove_prefix(string, prefix):
        return string.removeprefix(prefix)

    def remove_suffix(string, suffix):
        return string.removesuffix(suffix)

else:
    def remove_prefix(string, prefix):
        if string.startswith(prefix):
            return string[len(prefix):]
        else:
            return string

    def remove_suffix(string, suffix):
        if string.endswith(suffix):
            return string[:-len(suffix)]
        else:
            return string


def evaluate_fstring(template, **variables):
    """
    Deferred f-string evaluation

    Unlike ``"Bar: {foo}".format(foo="bar")``, this function will also evaluate function calls
    inside the curly braces.

    .. warning:: Because `template` is passed to :func:`eval`, this function
        must NEVER be called with code that comes from the user. Only use this
        function to evaluate hardcoded strings.

    :param str template: Unevaluated f-string (i.e. a normal string containing
        curly braces without the ``f`` in front of the quote)
    :param dict variables: :class:`dict` instance that maps names that can be
        used in `template` in curly braces to objects that replace the curly
        braced name.

    Example:

    >>> template = 'Evaluate {x}: {sum((1, 2, 3)) * 2}'
    >>> evaluate_fstring(template, x='this')
    Evaluate this: 12
    >>> evaluate_fstring(template, x='that')
    Evaluate that: 12

    References:

        https://pypi.org/project/f-yeah/
        https://stackoverflow.com/a/42497694
    """
    fstring = 'f' + repr(template)
    return eval(fstring, variables)


class CaseInsensitiveString(str):
    """:class:`str` that ignores case when compared or sorted"""

    def __hash__(self):
        return hash(self.casefold())

    def __eq__(self, other):
        if not isinstance(other, str):
            return NotImplemented
        else:
            return self.casefold() == other.casefold()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.casefold() < other.casefold()

    def __le__(self, other):
        return self.casefold() <= other.casefold()

    def __gt__(self, other):
        return self.casefold() > other.casefold()

    def __ge__(self, other):
        return self.casefold() >= other.casefold()
