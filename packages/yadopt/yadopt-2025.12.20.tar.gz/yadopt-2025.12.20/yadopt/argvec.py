"""
yadopt.argvec - argment vector parser
"""

# Declare published functins and variables.
__all__ = ["parse_argvec"]

# Import standard libraries.
import copy

# For type hinting.
from collections.abc import Generator

# Import custom modules.
from .dtypes import OptsInfo, ArgVector
from .usage  import UsageEntry, UsageOpt, UsageInfo


def parse_argvec(argv: list[str], usage: UsageInfo, opts: OptsInfo) -> ArgVector | None:
    """
    Try to match with the given arguemtn vector and usage patterns.
    If matched usage found, this function returns a dictionary that represents name-value
    correspondance. Otherwise, returns None.

    Args:
        argv  (list[str]): [IN] Argument vector.
        usage (UsageInfo): [IN] Parsed result of docstring.
        opts  (OptsInfo) : [IN] Options information of docstring.

    Returns:
        (ArgVector | None): Correspondance of argument/option names and values.
    """
    # Get a map from altanative name to standard name.
    alt_names: dict[str, str] = {opt.name_alt: opt.name for opt in opts.entries if opt.name_alt is not None}

    # Standardize option names of argument vector.
    argv_std: list[str] = list(standerdize_option_names_in_argument_vector(argv, alt_names))

    for usage_entry in usage.entries:

        # Convert options in usage to dict.
        usage_opt_dict: dict[str, UsageOpt] = {opt.name: opt for opt in usage_entry.opts}

        # Standardize option names of usage pattern.
        usage_opt_dict = {alt_names.get(key, key): value for key, value in usage_opt_dict.items()}

        # Try to match the argument vector and usage pattern.
        argvec: ArgVector | None = match_argvec_and_usage(argv_std, usage_entry, usage_opt_dict)

        # If matched, returns the ArgVector instance.
        if argvec is not None:

            # Append all unused precesing tokens as False.
            for u in usage.entries:
                for token_pre in u.pres[1:]:
                    if token_pre not in argvec.pres:
                        argvec.pres[token_pre] = False

            # Append all optional arguments that has default value but not appears in the user input.
            for opt in opts.entries:
                if (opt.name not in argvec.opts) and (opt.default is not None):
                    if (opt.name in usage_opt_dict) and (not usage_opt_dict[opt.name].required):
                        argvec.opts[opt.name] = opt.default

            return argvec

    # If appropriate usage not found, return empty user input.
    return None


def standerdize_option_names_in_argument_vector(argv: list[str], alt_names: dict[str, str]) -> Generator[str]:
    """
    Standardize option names of argument vector.
    For example, "-h" -> "--help".

    Args:
        argv      (list[str])     : [IN] Argument vector.
        alt_names (dict[str, str]): [IN] A map from altanative name to standard name.

    Returns:
        (Generator[str]): Standerdized option names.
    """
    for idx, (prefix, key) in enumerate((token[0], token[1:]) for token in argv):
        yield f"--{alt_names[key]}" if (prefix == "-") and (key in alt_names) else argv[idx]


def match_argvec_and_usage(argv: list[str], usage: UsageEntry, usage_opt_dict: dict[str, UsageOpt]) -> ArgVector | None:
    """
    Try to match the given argument vector and usage pattern.
    If matched, returns ArgVector instance, and otherwise, returns None.

    Args:
        argv           (list[str])          : [IN] Argument vector.
        usage          (UsageEntry)         : [IN] Usage pattern.
        usage_opt_dict (dict[str, UsageOpt]): [IN] Dictionary form of options in usage.

    Returns:
        (ArgVector): ArgVector instance if matched, and None otherwise.
    """
    # Copy the input argment vector for safety.
    argv = copy.deepcopy(argv)

    # Initialize the output dictionary.
    argvec: ArgVector = ArgVector(pres={}, args={}, opts={})

    # Check preceding strings. It's convenient for users to ignore the first
    # preceding argument, which is often the name of the called Python script.
    for idx, token in enumerate(usage.pres[1:], start=1):

        # Return None if preceding token does not match.
        if (len(argv) <= idx) or (argv[idx] != token):
            return None

        argvec.pres[token] = True

    # Drop the preceding tokens from the argument vector.
    argv = argv[len(usage.pres):]

    # Make a copy of available argument names.
    available_args: list[str] = copy.deepcopy(usage.args)

    while argv:

        # Get next token.
        token = argv.pop(0)

        # Case 1: Option token.
        if token.startswith("-"):
            is_matched = proc_opt_token(token, argv, argvec, usage_opt_dict)

        # Case 2: Argument token.
        else:
            is_matched = proc_arg_token(token, argvec, available_args)

        # Return None if not matched.
        if not is_matched:
            return None

    # If unused arguments remaining, that means the usage does not match.
    if any(not arg.endswith("...") for arg in available_args):
        return None

    # If any of the required options are missing, that means the usage does not match.
    if not all(name in argvec.opts for name, opt in usage_opt_dict.items() if opt.required):
        return None

    return argvec


def proc_arg_token(token: str, argvec: ArgVector, available_args: list[str]) -> bool:
    """
    Process argument token.

    Args:
        token          (str)      : [IN] Input token.
        argvec         (ArgVector): [IN] User input instance.
        available_args (list[str]): [IN] Rest of available arguments.

    Returns:
        (bool): True if matched.
    """
    # NOT MATRCHED!: too many arguments.
    if not available_args:
        return False

    # Case 2.1: multiple arguments.
    if available_args[0].endswith("..."):

        # Get argument name.
        target_arg: str = available_args[0].rstrip(".")

        # Create a list.
        if target_arg not in argvec.args:
            argvec.args[target_arg] = []

        # Append the token to the list.
        argvec.args[target_arg].append(token)

    # Case 2.2: single arguments.
    else:
        argvec.args[available_args.pop(0)] = token

    return True


def proc_opt_token(token: str, argv: list[str], user_input: ArgVector, usage_opt_dict: dict[str, UsageOpt]) -> bool:
    """
    Process option token.

    Args:
        token      (str)       : [IN] Input token.
        argv       (list[str]) : [IN] Argument vector.
        user_input (ArgVector) : [IN] User input instance.
        usage      (UsageEntry): [IN] Usage pattern.

    Returns:
        (bool): True if matched.
    """
    # Remove hyphens.
    token = token.lstrip("-")

    # NOT MATRCHED!: unknown option.
    if token not in usage_opt_dict:
        return False

    # Get the target option.
    usage_opt: UsageOpt = usage_opt_dict[token]

    # Case 1.1: Option with value.
    if usage_opt.has_val:

        # NOT MATRCHED!: option value not found: there is no remaining token.
        if not argv:
            return False

        # Get option value.
        token_value: str = argv.pop(0)

        # NOT MATRCHED!: option value not found: seems like option token.
        if token_value.startswith("-"):
            return False

        # Add {option_name: token_value} to the option dictionary of the user input.
        user_input.opts |= {token: token_value}

    # Case 1.2: Option without value.
    else:

        # Add {option_name: "True"} to the option dictionary of the user input.
        user_input.opts |= {token: "True"}

    return True


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
