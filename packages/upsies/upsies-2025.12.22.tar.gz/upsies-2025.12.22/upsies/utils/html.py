"""
HTML parsing
"""

import re
import warnings

from . import LazyModule

bs4 = LazyModule(module='bs4', namespace=globals())


def parse(string):
    """
    Return :class:`~.bs4.BeautifulSoup` instance

    :param string: HTML document

    :raise ContentError: if `string` is invalid HTML
    """
    if isinstance(string, bs4.element.Tag):
        return string
    else:
        # Disable bs4 warnings, e.g. "MarkupResemblesLocatorWarning: The input
        # looks more like a filename than markup. You may want to open this file
        # and pass the filehandle into Beautiful Soup."
        with warnings.catch_warnings():
            warnings.simplefilter(action='ignore', category=UserWarning)
            return bs4.BeautifulSoup(string, features='html.parser')


def dump(html, filepath):
    """
    Write `html` to `filepath` for debugging

    :param html: String or :class:`~.bs4.BeautifulSoup` instance
    """
    with open(filepath, 'w') as f:
        if isinstance(html, bs4.BeautifulSoup):
            f.write(html.prettify())
        else:
            f.write(parse(str(html)).prettify())


def get(soup, *attributes):
    """
    Get `attributes` from `soup`

    These two calls are equivalent if all attributes exist:

    >>> soup.table.tr.td
    "td value"
    >>> html.get(soup, "table", "tr", "td")
    "td value"

    But if any attribute is `None` (which is what :class:`~.bs4.BeautifulSoup`
    returns for unknown tags), you get `None` instead of forcing you to catch an
    :class:`AttributeError`:

    >>> soup.table.no_such_attribute.td
    AttributeError: 'NoneType' object has no attribute 'td'
    >>> html.get(soup, "table", "no_such_attribute", "td")
    None
    """
    for attr in attributes:
        soup = getattr(soup, attr, None)
        if soup is None:
            return None
    return soup


def as_text(html):
    """Strip HTML tags from string and return text without markup"""
    # Translate "<br>" to "\n" first.
    html = re.sub(r'<br\s*/?>', '\n', str(html))

    doc = parse(html)

    # BeautifulSoup stopped parsing tags like "<b>bold</b>" at some point when they are inside a
    # "<textarea>...</textarea>" tags. But we really want all HTML parsed.
    for textarea in doc.find_all('textarea'):
        textarea_content = ''.join(
            parse(c).get_text()
            for c in textarea.contents
        )
        textarea.replace_with(textarea_content)

    # Do normal HTML -> text conversion.
    text = doc.get_text()

    # Deduplicate spaces.
    text = re.sub(r'(\s)\s+', r'\1', text, flags=re.MULTILINE).strip()
    return text


def purge_tags(html):
    """
    Return `html` with <script> and <style> tags removed

    :param str html: HTML string
    """
    def is_javascript(tag):
        # Match <script> tags that don't have type="application/ld+json".
        if tag.name == 'script':
            return tag.get('type') != 'application/ld+json'

        # Match <style> (CSS) tags.
        elif tag.name == 'style':
            return True

        return False

    soup = parse(html)
    for script_tag in soup.find_all(is_javascript):
        script_tag.decompose()
    return str(soup)
