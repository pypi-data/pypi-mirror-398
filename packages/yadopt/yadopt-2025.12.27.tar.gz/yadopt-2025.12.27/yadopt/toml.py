"""
yadopt.toml - TOML parser and writer for YadOpt
"""

# Declare published functions and variables.
__all__ = ["dump_toml", "load_toml"]

# Import standard libraries.
import datetime
import getpass
import importlib
import platform
import pprint
import socket
import subprocess
import sys
import textwrap

# For type hinting.
from typing import Any, TextIO

# Import custom modules.
from .dtypes import YadOptArgs
from .errors import YadOptError


def dump_toml(args: YadOptArgs) -> str:
    """
    Convert the given YadOptArgs instance to a TOML string.
    """
    # Raise an error if TOML is not suppoerted by Python.
    check_toml_supported()

    # Create TOML file template.
    template_toml: str = textwrap.dedent("""
        [YadOptArgs]

        # Argument vector.
        argv = {argv}

        # Docstring used for YadOpt.
        docstr = '''
        {docstr}
        '''

        [Metadata]

        # Information of execution environment and time.
        hostname = '{hostname}'
        username = '{username}'
        platform = '{platform}'
        timestamp = '{timestamp}'

        # Python runtime information.
        python_ver = '{python_ver}'

        # Git information.
        git_hash = '{git_hash}'
        git_changed = {git_changed}
    """).strip()

    # Get string expression of argv and docstr.
    base_info: dict[str, str] = {
        "argv": pprint.pformat(getattr(args, "_argv_"), compact=True).replace("\n", "\n" + " " * 7),
        "docstr": getattr(args, "_dstr_").strip(),
    }

    return template_toml.format(**base_info, **get_metadata())


def load_toml(fp: TextIO) -> dict:
    """
    Load TOML file and returns YadOptArgs section.

    Args:
        fp (TextIO): File pointer of the target file.

    Returns:
        (dict): Contents of the TOML file.
    """
    # Raise an error if TOML is not suppoerted by Python.
    check_toml_supported()

    # Import tomllib library.
    tomllib = load_tomllib()

    # Load text from the given file pointer and parse it as TOML.
    return tomllib.loads(fp.read())["YadOptArgs"]


def load_tomllib() -> Any:
    """
    Load module for loading TOML file.
    """
    # Determine the module name to load.
    module_name: str = "tomllib" if (sys.version_info.minor >= 11) else "tomli"

    # Load the module.
    return importlib.import_module(module_name)


def check_toml_supported() -> bool:
    """
    Returns True if the current Python supports TOML.

    Returns:
        (bool): True if the runtime Python supports TOML.
    """
    try:
        load_tomllib()
    except ImportError as e:
        raise YadOptError.cannot_load_tomllib() from e

    return True


def get_metadata() -> dict:
    """
    Returns metadata information.

    Returns:
        (dict): Metadata dictionary.
    """
    def get_datetime_str() -> str:
        """
        Returns datetime string with timezone.
        """
        # Get the current time in UTC timezone, convert it to the system timezone, and stringify.
        return datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y/%m/%d %H:%M:%S %Z")

    def get_git_hash() -> str:
        """
        Get git information.
        """
        output: bytes = run_command(["git", "rev-parse", "HEAD"])
        return "???" if len(output)== 0 else output.decode().strip()

    def get_git_changed() -> str:
        """
        Returns 'true' if Git status is 'changed' otherwise 'false'.
        """
        output: bytes = run_command(["git", "status", "--porcelain"])
        return "false" if len(output) == 0 else "true"

    def get_username() -> str:
        """
        Get username.
        """
        try:
            return getpass.getuser()
        except (ImportError, KeyError, OSError):
            return "???"

    def run_command(tokens: list[str]) -> bytes:
        """
        Run the given command as a shell command.
        """
        return subprocess.run(tokens, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    return {"hostname"   : socket.gethostname(),
            "username"   : get_username(),
            "platform"   : platform.platform(),
            "timestamp"  : get_datetime_str(),
            "python_ver" : platform.python_version(),
            "git_hash"   : get_git_hash(),
            "git_changed": get_git_changed()}


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
