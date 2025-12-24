"""
Check argument vector based on the parsed arguments and options.
"""

# Declare published functions and variables.
__all__ = ["check_user_input"]

# Import custom modules.
from .dtypes import ArgsInfo, OptsInfo
from .errors import YadOptError
from .utils  import find_nearest_str


def check_user_input(argv: list[str], args: ArgsInfo, opts: OptsInfo, usage) -> bool:
    """
    Check all user input variables are defined in arguments/options section.

    Args:
        argvec  (ArgVector) : [IN] User input info.

    Returns:
        (bool): Returns True if all checks are passed.
    """
    return check_arguments(args, usage) and check_options(argv, opts, usage)


def check_arguments(args, usage) -> bool:
    """
    Check the contents of argument information and usage.
    """
    # Generate a set of all available argument names.
    arg_names: set[str] = {item.name for item in args.entries}

    # Check all user input is defined in argument sections.
    for usage_entry in usage.entries:
        for name in usage_entry.args:

            # If available arguments is empty, raise an error.
            if len(arg_names) == 0:
                raise YadOptError.unknown_argument(name, "")

            # If the argument does not exist in the available arguments, raise an error.
            if name.rstrip(".") not in arg_names:
                arg_nearest: str = find_nearest_str(name, arg_names)
                raise YadOptError.unknown_argument(name, f"Do you mean '{arg_nearest}'?")

    return True


def check_options(argv: list[str], opts: OptsInfo, usage) -> bool:
    """
    Check the contents of the argument vector and option information.

    Args:
        argv (list[str]): [IN] Argument vector to be checked.
        opts (OptsInfo) : [IN] Parsed option information.
    """
    # Get a set of option names including short expression, except None.
    opt_names: set[str] = {opt.name     for opt in opts.entries if opt.name     is not None}
    opt_names          |= {opt.name_alt for opt in opts.entries if opt.name_alt is not None}

    # Check all user input is defined in argument sections.
    for usage_entry in usage.entries:
        for opt in usage_entry.opts:

            # If available option is empty, raise an error.
            if len(opt_names) == 0:
                raise YadOptError.unknown_option_usage("--" + opt.name, "")

            # If the option does not exist in the available options, raise an error.
            if opt.name not in opt_names:
                opt_nearest = find_nearest_str(opt.name, opt_names)
                raise YadOptError.unknown_option_usage("--" + opt.name, f"Do you mean '--{opt_nearest}'?")

    # Check all arguments in the argument vector.
    for arg_opt in (arg for arg in argv if arg.startswith("-")):

        # If available option is empty, raise an error.
        if len(opt_names) == 0:
            raise YadOptError.unknown_option_argv(arg_opt, "")

        # If the option does not exist in the available options, raise an error.
        if arg_opt.lstrip("-") not in opt_names:

            # Do not search nearest option for short options.
            if not arg_opt.startswith("--"):
                raise YadOptError.unknown_option_argv(arg_opt, "")

            # Otherwise, search nearest option name and show it in the error message.
            opt_nearest = find_nearest_str(arg_opt.lstrip("-"), opt_names)
            raise YadOptError.unknown_option_argv(arg_opt, f"Do you mean '--{opt_nearest}'?")

    return True


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
