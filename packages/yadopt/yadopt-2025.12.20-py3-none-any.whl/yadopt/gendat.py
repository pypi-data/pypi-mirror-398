"""
yadopt.gendat - generate YadoptArgument data class
"""

# Declare published functions and variables.
__all__ = ["generate_data"]

# Import standard libraries.
import copy

# Import custom modules.
from .argvec import ArgVector
from .dtypes import ArgsInfo, OptsInfo, YadOptArgs


def generate_data(argvec: ArgVector, args: ArgsInfo, opts: OptsInfo, argv: list[str], docstr: str) -> YadOptArgs:
    """
    Create YadOptArgs instance, fill the values, and return it.

    Args:
        argvec (ArgVector) : [IN] Parsed user input.
        args   (ArgsInfo)  : [IN] Arguments information.
        opts   (OptsInfo)  : [IN] Options information.
        argv   (list[str]) : [IN] Argument vector.
        docstr (str)       : [IN] Docstring.

    Returns:
        (YadOptArgs): Parsed command line arguments.
    """
    # Create data instance.
    data: YadOptArgs = YadOptArgs()

    # Fill user input preceding values.
    for name, value in argvec.pres.items():
        setattr(data, name, bool(value))

    # Fill user input arguments and options.
    for name, value in (argvec.args | argvec.opts).items():
        setattr(data, name, value)

    # Append extra data.
    setattr(data, "_args_", copy.deepcopy(args))
    setattr(data, "_opts_", copy.deepcopy(opts))
    setattr(data, "_user_", copy.deepcopy(argvec))
    setattr(data, "_argv_", copy.deepcopy(argv))
    setattr(data, "_dstr_", copy.deepcopy(docstr))

    return data


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
