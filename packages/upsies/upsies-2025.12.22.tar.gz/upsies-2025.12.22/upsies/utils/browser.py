"""
Open a URL in a web browser
"""

from . import LazyModule

import logging  # isort:skip
_log = logging.getLogger(__name__)

webbrowser = LazyModule(module='webbrowser', namespace=globals())


def open(url):
    """Attempt to open URL in default web browser"""
    webbrowser.open_new_tab(str(url))
