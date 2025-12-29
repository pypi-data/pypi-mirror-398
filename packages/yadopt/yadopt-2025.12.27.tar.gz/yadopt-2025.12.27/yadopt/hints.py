"""
yadopt.hints - assign types based on type hinting string
"""

# Declare published functins and variables.
__all__ = ["type_func", "type_hint"]

# Import standard libraries.
import ast

# For type hinting.
from collections.abc import Callable

# Import custom modules.
from .argvec import ArgVector
from .dtypes import ArgsInfo, OptEntry, OptsInfo, Path
from .errors import YadOptError
from .utils  import strtobool, strtostr


def auto_type(value: str) -> int | float | str | Path:
    """
    Automatically determine the data type.

    Args:
        value    (str)       : [IN] String expression of value.
        name     (str)       : [IN] Option / argument name.
        val_name (str | None): [IN] Option value name.
        type_dsc (str | None): [IN] Type name written in description.

    Returns:
        (int | float | str | Path): Parsed value.
    """
    try:
        return ast.literal_eval(value)
    except ValueError:
        return str(value)


def type_func(name: str, val_name: str | None, type_dsc: str | None) -> Callable:
    """
    Determine data type of arguments/options.

    Args:
        name     (str)       : Argument/option name.
        val_name (str | None): Option value name.
        type_dsc (str | None): Type name written in description head.
    """
    # Define a map from data type string to data type.
    dtype_hints: dict[str, Callable] = {
        # Booleans.
        "bool": strtobool, "boolean": strtobool,
        # Integers.
        "int": int, "integer": int,
        # Floating numbers.
        "flt": float, "float": float,
        # Strings.
        "str": strtostr, "string": strtostr,
        # Path.
        "path": Path,
    }

    # Case 1: description head.
    if type_dsc is not None:

        # Raise an error if type name is unknown.
        if type_dsc.lower() not in dtype_hints:
            raise YadOptError.invalid_type_name(type_dsc)

        return dtype_hints[type_dsc.lower()]

    # Case 2: value name suffix.
    if val_name is not None:

        # Get the type name candidate from the value name.
        val_type_name: str = val_name.rsplit("_", maxsplit=1)[-1]

        # Returns the type if the type name is valid.
        if val_type_name.lower() in dtype_hints:
            return dtype_hints[val_type_name.lower()]

    # Case 3: argument/option name suffix.
    if name:

        # Returns the type if the name ends with the type name.
        for key, dtype in dtype_hints.items():
            if name.endswith(key):
                return dtype

    # Otherwise, returns default type.
    return auto_type


def fill_default_values(argvec: ArgVector, opts: OptsInfo) -> ArgVector:
    """
    Fill default values.

    Args:
        argvec (ArgVector): [IN] Parsed user input.
        opts   (OptsInfo) : [IN] Options information of docstring.

    Returns:
        (ArgVector): Parsed user input.
    """
    for opt_entry in opts.entries:
        if opt_entry.name not in argvec.opts:
            argvec.opts[opt_entry.name] = opt_entry.default

    return argvec


def type_hint(argvec: ArgVector, args: ArgsInfo, opts: OptsInfo, type_fn: Callable, fill_default: bool) -> None:
    """
    Apply type hints.

    Args:
        argvec       (ArgVector): [IN] Parsed user input.
        args         (ArgsInfo) : [IN] Arguments information of docstring.
        opts         (OptsInfo) : [IN] Options information of docstring.
        type_fn      (Callable) : [IN] A function that assign types to values.
        fill_default (bool)     : [IN] Fill default values if True.
    """
    def set_typed_value(val_dict: dict, args_or_opts: ArgsInfo | OptsInfo, type_fn: Callable) -> None:
        """
        Get typed value.
        """
        for entry in args_or_opts.entries:

            # Do nothing if the entry is not in the value dictionary.
            if entry.name not in val_dict:
                continue

            # If the value is None, not necessary to assign type.
            if val_dict[entry.name] is None:
                continue

            # If the value looks like None, set real None.
            if (val_dict[entry.name] == "None") or (val_dict[entry.name] == "NONE"):
                val_dict[entry.name] = None
                continue

            # Get type function.
            fn = type_fn(entry.name, entry.val_name if isinstance(entry, OptEntry) else None, entry.type_dsc)

            # If the target value is list of string, then apply the type function
            # to the list contents.
            if isinstance(val_dict[entry.name], list):
                val_dict[entry.name] = [fn(v) for v in val_dict[entry.name]]

            # Else, normaly apply type function to the value.
            else:
                val_dict[entry.name] = fn(val_dict[entry.name])

    # Fill deafult values to the user input.
    if fill_default:
        fill_default_values(argvec, opts)

    # Assign type to the values.
    set_typed_value(argvec.args, args, type_fn)
    set_typed_value(argvec.opts, opts, type_fn)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
