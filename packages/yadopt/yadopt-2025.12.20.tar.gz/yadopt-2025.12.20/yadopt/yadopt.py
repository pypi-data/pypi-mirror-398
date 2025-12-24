"""
Yet another docopt, a human-friendly command line arguments parser.
"""

# Declare published functins and variables.
__all__ = ["parse", "wrap", "to_dict", "to_namedtuple", "get_group"]

# Import standard libraries.
import collections
import copy
import functools
import inspect
import os
import sys

# For type hinting.
from collections.abc import Callable
from typing          import Any

# Import custom modules.
from .argopt  import parse_docstr_args, parse_docstr_opts
from .argvec  import ArgVector, parse_argvec
from .color   import colorize_help_message
from .checker import check_user_input
from .dtypes  import ArgsInfo, OptsInfo, YadOptArgs
from .errors  import YadOptError
from .gendat  import generate_data
from .hints   import type_func, type_hint
from .usage   import parse_docstr_usage, UsageInfo
from .utils   import retokenize


def parse(docstr: str, argv: list[str] = sys.argv, type_fn: Callable = type_func, verbose: bool = False) -> YadOptArgs:
    """
    Parse a given docstring and an argument vector, and return a YadoptArgs instance.

    Args:
        docstr  (str)       : [IN] Docstring to be parsed.
        argv    (list[str]) : [IN] Argument vector.
        type_fn (Callable)  : [IN] A function that determin types of argument/option values.
        verbose (bool)      : [IN] Displays verbose messages that are useful for debugging.

    Returns:
        (YadOptArgs): Parsed command line arguments.
    """
    # Retokenize the input vector.
    argv = list(retokenize(copy.copy(argv)))

    # Check the type function.
    if not callable(type_fn):
        raise YadOptError.invalid_type_func(type_fn)

    # Parse usage section.
    usage: UsageInfo = parse_docstr_usage(docstr)
    if verbose:
        print("usage =", usage)

    # Parse argument sections.
    args: ArgsInfo = parse_docstr_args(docstr)
    if verbose:
        print("args =", args)

    # Parse option sections.
    opts: OptsInfo = parse_docstr_opts(docstr)
    if verbose:
        print("opts =", opts)

    # Expand OPTIONS in usage.
    usage.expand_options(opts)

    # Check argv using the parsed doc info.
    check_user_input(argv, args, opts, usage)

    # Parse the given command line arguments.
    argvec: ArgVector | None = parse_argvec(argv, usage, opts)
    if verbose:
        print("argvec =", argvec)

    # If appropriate usage not found, print message and raise an error.
    if argvec is None:
        raise YadOptError.valid_usage_not_found(usage.docstr, inspect.stack()[-1])

    # Apply type hints. This function also fill default values.
    type_hint(argvec, args, opts, type_fn, fill_default=True)

    # Print help message and exit if --help is specified, and exit.
    # You can stop exiting the software by catching the SystemExit error.
    if argvec.opts.get("help", False) or ("help" in argvec.pres):
        print(colorize_help_message(docstr.strip()))
        sys.exit(os.EX_USAGE)

    # Returns YadOptArgs instance.
    return generate_data(argvec, args, opts, argv, docstr)


def wrap(*pargs: Any, **kwargs: Any) -> Callable:
    """
    Wrapper function for the command line parsing.

    Args:
        pargs  (Any): [IN] Positional arguments for 'yadopt.parse' function.
        kwargs (Any): [IN] Keyword arguments for 'yadopt.parse' function.

    Returns:
        (Callable): Decorator function.

    Note:
        This function atually returns a function bacause this function
        is designed as a decorator function with argument (= docstr).
    """
    def decolate(func: Callable) -> Callable:
        """
        Decolate the given function.
        """
        args: YadOptArgs = parse(*pargs, **kwargs)

        @functools.wraps(func)
        def wrapper_func(*pargs_func: Any, **kwargs_func: Any) -> Any:
            return func(args, *pargs_func, **kwargs_func)

        return wrapper_func

    return decolate


def to_dict(args: YadOptArgs) -> dict[str, Any]:
    """
    Convert YadOptArgs instance to a dictionary.

    Args:
        args (YadOptArgs): [IN] Parsed command line arguments.

    Returns:
        (dict[str, Any]): Dictionary of the given parsed arguments.
    """
    return {key:val for key, val in vars(args).items() if (key[0] != "_") and (key[-1] != "_")}


def to_namedtuple(args: YadOptArgs) -> tuple[Any, ...]:
    """
    Convert YadOptArgs instance to a named tuple.

    Args:
        args (YadOptArgs): [IN] Parsed command line arguments.

    Returns:
        (namedtuple): Namedtuple of the given parsed arguments.
    """
    args_d: dict = to_dict(args)
    fields: list = list(args_d.keys())
    return collections.namedtuple("YadOptArgsNt", fields)(**args_d)


def get_group(args: YadOptArgs, group: str) -> YadOptArgs:
    """
    Returns the parsed result of the specified section only as a dictionary.

    Args:
        args  (YadOptArgs): [IN] Parsed command line arguments.
        group (str)       : [IN] Name of group to extract.

    Returns:
        (YadOptArgs): Parsed command line arguments of the group.
    """
    # Get the list of keys in the group.
    list_keys  = [entry.name for entry in getattr(args, "_args_").entries if entry.group == group]
    list_keys += [entry.name for entry in getattr(args, "_opts_").entries if entry.group == group]

    data: YadOptArgs = YadOptArgs()

    # Append group members.
    for key, value in to_dict(args).items():
        if key in list_keys:
            setattr(data, key, value)

    # Append extra data.
    setattr(data, "_args_", copy.deepcopy(getattr(args, "_args_", None)))
    setattr(data, "_opts_", copy.deepcopy(getattr(args, "_opts_", None)))
    setattr(data, "_user_", copy.deepcopy(getattr(args, "_user_", None)))
    setattr(data, "_argv_", copy.deepcopy(getattr(args, "_argv_", None)))
    setattr(data, "_dstr_", copy.deepcopy(getattr(args, "_dstr_", None)))

    return data


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
