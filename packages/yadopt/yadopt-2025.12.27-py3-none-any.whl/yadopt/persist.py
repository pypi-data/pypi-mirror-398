"""
yadopt.persist - persist YadOptArgs object
"""

# Import standard libraries.
import gzip
import json
import pathlib
import shlex

# For type hinting.
from collections.abc import Callable

# Import custom modules.
from .dtypes import YadOptArgs
from .errors import YadOptError
from .toml   import dump_toml, load_toml
from .yadopt import parse


def save(path: str, args: YadOptArgs, indent: int = 4) -> None:
    """
    Save the parsed command line arguments as a JSON file.

    Args:
        path   (str)       : [IN] Destination path.
        args   (YadOptArgs): [IN] Parsed command line arguments to be saved.
        indent (int)       : [IN] Indent size of the output JSON file.
    """
    # Conver the given path as an instance of pathlib.Path.
    path_out: pathlib.Path = pathlib.Path(path)

    # Determine the open function.
    open_fn: Callable = gzip.open if path_out.suffix.endswith(".gz") else open

    # Case 1: JSON file.
    if any(path_out.name.endswith(sfx) for sfx in [".json", ".json.gz"]):

        # Create the contents to save.
        data_json: dict = {"argv": getattr(args, "_argv_"), "docstr": getattr(args, "_dstr_")}

        # Write as a JSON file.
        with open_fn(path_out, "wt") as ofp:
            json.dump(data_json, ofp, indent=indent)

    # Case 2: text format.
    elif any(path_out.name.endswith(sfx) for sfx in [".txt", ".txt.gz"]):

        # Create the contents to save.
        data_txt: str = shlex.join(getattr(args, "_argv_")) + "\n\n" + getattr(args, "_dstr_")

        # Write as a text file.
        with open_fn(path_out, "wt") as ofp:
            ofp.write(data_txt)

    # Case 3: TOML format.
    elif any(path_out.name.endswith(sfx) for sfx in [".toml", ".toml.gz"]):

        # Write as a TOML file.
        with open_fn(path_out, "wt") as ofp:
            ofp.write(dump_toml(args))

    # Otherwise: raise an error.
    else:
        raise YadOptError.invalid_io_file_format("yadopt.save", path)


def load(path: str) -> YadOptArgs:
    """
    Load a parsed command line arguments from a text file.

    Args:
        path (str): [IN] Source path.

    Returns:
        (YadOptArgs): Restored parsed command line arguments.
    """
    # Conver the given path as an instance of pathlib.Path.
    path_out: pathlib.Path = pathlib.Path(path)

    # Determine the open function.
    open_fn: Callable = gzip.open if path_out.suffix.endswith(".gz") else open

    # Case 1: JSON file.
    if any(path_out.name.endswith(sfx) for sfx in [".json", ".json.gz"]):

        # Load the JSON file.
        with open_fn(path_out, "rt") as ifp:
            data_json: dict = json.load(ifp)

        # Parse the loaded argument vector using the loaded docstring.
        return parse(data_json["docstr"], data_json["argv"])

    # Case 2: text format.
    if any(path_out.name.endswith(sfx) for sfx in [".txt", ".txt.gz"]):

        # Load the text file.
        with open_fn(path_out, "rt") as ifp:
            lines: list[str] = ifp.read().split("\n")

        # Restore argument vector and docstring.
        argv  : list[str] = shlex.split(lines[0])
        docstr: str       = "\n".join(lines[2:])

        # Parse the loaded argument vector using the loaded docstring.
        return parse(docstr, argv)

    # Case 3: TOML format.
    if any(path_out.name.endswith(sfx) for sfx in [".toml", ".toml.gz"]):

        # Load the TOML file.
        with open_fn(path_out, "rt") as ifp:
            data_toml: dict = load_toml(ifp)

        # Parse the loaded argument vector using the loaded docstring.
        return parse(data_toml["docstr"], data_toml["argv"])

    # Otherwise: raise an error.
    raise YadOptError.invalid_io_file_format("yadopt.load", path, path_out.suffix)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
