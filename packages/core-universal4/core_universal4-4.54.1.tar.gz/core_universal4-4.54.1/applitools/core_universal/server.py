import atexit
import contextlib
import sys
from logging import getLogger
from subprocess import PIPE, Popen  # nosec

try:
    # assume python>=3.9 and try to import new resources API
    from importlib.resources import as_file, files

    def resource_filename(package, file_name):
        cleanup_manager = contextlib.ExitStack()
        ref = files(package) / file_name
        path = cleanup_manager.enter_context(as_file(ref))
        atexit.register(cleanup_manager.close)
        return path

except ImportError:
    # fallback to importlib_resources backport for python<3.9
    from importlib_resources import as_file, files

    def resource_filename(package, file_name):
        cleanup_manager = contextlib.ExitStack()
        ref = files(package) / file_name
        path = cleanup_manager.enter_context(as_file(ref))
        atexit.register(cleanup_manager.close)
        return path


logger = getLogger(__name__)

_exe_name = "core.exe" if sys.platform == "win32" else "core"
executable_path = resource_filename("applitools.core_universal", "bin/" + _exe_name)


class SDKServer(object):
    def __init__(self, debug=None, mask_log=None):
        """Start core-universal service subprocess and obtain its port number."""
        command = [
            executable_path,
            "universal",
            "--no-singleton",
            "--shutdown-mode",
            "stdin",
        ]
        if debug:
            command.append("--debug")
        if mask_log:
            command.append("--maskLog")
        # Capture and keep stdin reference to notify USDK when it should terminate.
        # USDK is expected to terminate when it receives EOF on its stdin.
        # The pipe is automatically closed and EOF is sent by OS when python terminates.
        self._usdk_subprocess = Popen(command, stdin=PIPE, stdout=PIPE)  # nosec
        self.port = int(self._usdk_subprocess.stdout.readline())
        logger.info("Started Universal SDK server at %s", self.port)

    def __repr__(self):
        """Produce helpful debugging description."""
        return "SDKServer(port={})".format(self.port)
