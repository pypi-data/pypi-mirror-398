"""
yadopt.argopt - docstring parsers for argument and option sections
"""

# Declare published functions and variables.
__all__ = ["parse_docstr_args", "parse_docstr_opts"]

# Import standard libraries.
import re

# Import custom modules.
from .dtypes   import ArgEntry, ArgsInfo, OptEntry, OptsInfo
from .errors   import YadOptError
from .matchers import match_arg, match_opt
from .utils    import get_default, get_section_lines, get_section_lines_and_names


def parse_docstr_args(docstr: str) -> ArgsInfo:
    """
    Parse docstring and returns arguments info.

    Args:
        docstr (str): [IN] Docstring to be parsed.

    Returns:
        (ArgsInfo): Arguments information of docstring.
    """
    # Get arguments information.
    entries: list[ArgEntry] = []
    for line, section_name in get_section_lines_and_names(docstr, "arguments"):
        if isinstance(entry := parse_line(line, section_name), ArgEntry):
            entries.append(entry)

    # Get arguments sections of docstring.
    docstr_args: str = "Arguments:\n" + "\n".join(get_section_lines(docstr, "arguments"))

    return ArgsInfo(entries, docstr_args)


def parse_docstr_opts(docstr: str) -> OptsInfo:
    """
    Parse docstring and returns options info.

    Args:
        docstr (str): [IN] Docstring to be parsed.

    Returns:
        (OptsInfo): Options information of docstring.
    """
    # Get options information.
    entries: list[OptEntry] = []
    for line, section_name in get_section_lines_and_names(docstr, "options"):
        if isinstance(entry := parse_line(line, section_name), OptEntry):
            entries.append(entry)

    # Get options sections of docstring.
    docstr_opts: str = "Options:\n" + "\n".join(get_section_lines(docstr, "options"))

    return OptsInfo(entries, docstr_opts)


def parse_line(line: str, group: str) -> ArgEntry | OptEntry | None:
    """
    Parse an entry of argument and option sections.

    Args:
        line  (str): [IN] Input line.
        group (str): [IN] Group name.

    Returns:
        (ArgEntry | OptEntry | None): Parsed result.

    Examples:
        >>> parse_line("  -o   msg", "g1")
        OptEntry(name='o', name_alt=None, val_name=None, type_dsc='bool', desc='msg', default='False', group='g1')
        >>> parse_line("  --opt   msg", "g2")
        OptEntry(name='opt', name_alt=None, val_name=None, type_dsc='bool', desc='msg', default='False', group='g2')
        >>> parse_line("  -o, --opt   msg", "g3")
        OptEntry(name='opt', name_alt='o', val_name=None, type_dsc='bool', desc='msg', default='False', group='g3')
        >>> parse_line("  -o, --opt INT   msg", "g4")
        OptEntry(name='opt', name_alt='o', val_name='INT', type_dsc=None, desc='msg', default=None, group='g4')
        >>> parse_line("  arg1 msg", "g5")
        ArgEntry(name='arg1', type_dsc=None, desc='msg', default=None, group='g5')
        >>> parse_line("  arg1  (INT) msg  [default: 10]", "g6")
        ArgEntry(name='arg1', type_dsc='INT', desc='msg', default='10', group='g6')
    """
    # Try to parse as argument line.
    (outputs, description, _) = match_arg(line)

    # Returns ArgEntry if matched.
    if len(outputs) > 0:

        # Get matched argument name.
        name: str | None = outputs[0]

        # The name should not be None.
        if not isinstance(name, str):
            raise YadOptError.internal_error

        # Get data type.
        (dtype_str, description) = get_dtype_desc(description)

        # Get default value.
        (description, default) = get_default(description)

        return ArgEntry(name, dtype_str, description, default, group)

    # Try to parse as option line.
    (outputs, description, has_value) = match_opt(line)

    # Returns OptEntry if matched.
    if len(outputs) > 0:

        # Unpack matched results.
        (name, name_alt, val_name) = outputs

        # The name should be a string.
        if not isinstance(name, str):
            raise YadOptError.internal_error

        # Get data type.
        (dtype_str, description) = get_dtype_desc(description)

        # Get default value.
        (description, default) = get_default(description)

        # If the option has no value (i.e. has_value is False),
        # then the data type and defualt value should be bool and False, respectively.
        if has_value is False:
            (val_name, dtype_str, default) = (None, "bool", "False")

        return OptEntry(name, name_alt, val_name, dtype_str, description, default, group)

    # Otherwise, returns None.
    return None


def get_dtype_desc(description: str) -> tuple[str | None, str]:
    """
    Get data type string from the description.

    Args:
        description (str): [IN] Description line.

    Returns:
        (tuple): A pair of appropriate data type name and the rest of description.

    Examples:
        >>> get_dtype_desc("Integer value.")
        (None, 'Integer value.')
        >>> get_dtype_desc("(INT) Integer value.")
        ('INT', 'Integer value.')
    """
    # Try to get type from the description.
    if (m := re.match(r"^\s*\((\w+)\)\s*", description)) is not None:

        # Get matched data type name and description.
        dtype_str = m.group(1).strip()
        description = description[len(m.group(0)):]

        # If the matched data type name is valid, then return them.
        return (dtype_str, description)

    return (None, description)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
