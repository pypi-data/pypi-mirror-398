import sys

import logging  # isort:skip
_log = logging.getLogger(__name__)


def print_stdout(*msgs):
    """Simplified version of regular :func:`print` that prints to :attr:`sys.stdout`"""
    sys.stdout.write(' '.join(str(msg) for msg in msgs) + '\n')


def print_stderr(*msgs):
    """Simplified version of regular :func:`print` that prints to :attr:`sys.stderr`"""
    sys.stderr.write(' '.join(str(msg) for msg in msgs) + '\n')


def is_tty():
    """Whether we live in a terminal and can interact with the user"""
    # If we have input and output, we have user interaction. It's ok if we don't have sys.stdout
    # (e.g. because it is redirected to a file) because prompt-toolkit writes to sys.stderr in that
    # case.
    return bool(
        # stdin does exist and is not redirected
        (sys.stdin and sys.stdin.isatty())
        and (
            # stdout exists and is not redirected.
            (sys.stdout and sys.stdout.isatty())
            # stderr exists and is not redirected.
            or (sys.stderr and sys.stderr.isatty())
        )
    )
