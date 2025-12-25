"""
Execute external commands
"""

import os
import pty
import selectors

from .. import errors
from ..utils import LazyModule

subprocess = LazyModule(module='subprocess', namespace=globals())


class Process:
    """
    Convenience wrapper around :class:`subprocess.Popen`

    The main benefit of it is that you can easily iterate over lines on stdout or stderr.
    """

    def __init__(self, popen):
        self._popen = popen

    def _iterlines(self, fh):
        # Tell readline() to return an empty string if there is nothing to read.
        os.set_blocking(fh.fileno(), False)

        selector = selectors.DefaultSelector()
        selector.register(fh.fileno(), selectors.EVENT_READ)

        while True:
            line = fh.readline()
            yield line
            if not line:
                is_running = self.is_running
                if not is_running:
                    # Process terminated and we consumed all buffered lines.
                    return
                else:
                    # This is essnentially `time.sleep(0.1)`, but the call is interrupted as soon as
                    # there is anything to read on `fh`. It means we can sleep for a long time but
                    # still read output when the subprocess writes it.
                    for _ in selector.select(timeout=0.1):
                        pass

    @property
    def stdout(self):
        """
        Iterator that yields lines from standard output

        If there is nothing to read, an empty string is yielded after a short timeout to prevent
        your loop from being blocked.
        """
        yield from self._iterlines(self._popen.stdout)

    @property
    def stderr(self):
        """
        Iterator that yields lines from standard error or nothing if standard error is
        redirected to standard out.

        If there is nothing to read, an empty string is yielded after a short timeout to prevent
        your loop from being blocked.
        """
        if self._popen.stderr:
            yield from self._iterlines(self._popen.stderr)
        else:
            # Popen.stderr is None if the "stderr" argument wasn't `subprocess.PIPE`.
            # This means stderr is redirected to stdout.
            yield from ()

    @property
    def is_running(self):
        """Whether the process is still running"""
        return self._popen.poll() is None

    def terminate(self):
        """
        Ask process to terminate (SIGTERM) and kill it (SIGKILL) if it doesn't do that after 1
        second

        This method does nothing if the process is not running.
        """
        if self.is_running:
            self._popen.terminate()
            try:
                self._popen.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._popen.kill()

    @property
    def exitcode(self):
        """
        Exit code or termination signal after process ended

        See :attr:`subprocess.Popen.returncode`
        """
        return self._popen.returncode


def run(argv, *, ignore_errors=False, join_stderr=False, return_exitcode=False, communicate=False):
    """
    Execute command in subprocess

    :param argv: Command to execute
    :type argv: list of str
    :param bool ignore_errors: Do not raise :class:`.ProcessError` if stderr is
        non-empty
    :param bool join_stderr: Redirect stderr to stdout
    :param bool return_exitcode: Return a 2-tuple of `(stdout, exitcode)` instead of only `stdout`
    :param bool communicate: Instead of the command's output, return a :class:`~.subproc.Process`
        instance

    :raise DependencyError: if the command fails to execute
    :raise ProcessError: if stdout is not empty and `ignore_errors` is `False`

    :return: Output from process
    :rtype: str
    """
    argv = tuple(str(arg) for arg in argv)

    # STDOUT and STDERR
    stdout_argument = subprocess.PIPE
    if join_stderr:
        stderr_argument = subprocess.STDOUT
    else:
        stderr_argument = subprocess.PIPE

    # - We MUST NOT use the terminal's STDIN because ffmpeg and BDInfo capture user input
    #   (e.g. Ctrl-C) and break our own TUI.
    # - BDInfo refuses to run if STDIN is not a TTY (which is the case with stdin=subprocess.PIPE).
    # - The builtin `pty` module provides a pseudo TTY we can use, but it does not work on Windows.
    _pty_stdin_master, pty_stdin_slave = pty.openpty()

    try:
        process = Process(subprocess.Popen(
            argv,
            shell=False,
            text=True,
            universal_newlines=True,
            stdout=stdout_argument,
            stderr=stderr_argument,
            stdin=pty_stdin_slave,
            # Line buffering
            bufsize=1,
        ))
    except OSError as e:
        raise errors.DependencyError(f'Missing dependency: {argv[0]}') from e
    else:
        if communicate:
            return process
        else:
            # The process is finished when we have consumed all stdout/stderr. It is important to
            # not call Popen.wait() here (at least not before all output is consumed) because we
            # might end up in a deadlock:
            # https://docs.python.org/3/library/subprocess.html#subprocess.Popen.wait
            stdout = ''.join(process.stdout)
            stderr = ''.join(process.stderr)

            if stderr and not ignore_errors:
                raise errors.ProcessError(stderr)
            elif return_exitcode:
                return stdout, process.exitcode
            else:
                return stdout
