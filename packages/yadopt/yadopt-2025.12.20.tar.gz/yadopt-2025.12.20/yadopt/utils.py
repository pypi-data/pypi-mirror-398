"""
yadopt.utils - collections of utility functions
"""

# Declare published functins and variables.
__all__ = ["get_default", "get_error_marker", "get_section_lines", "strtobool", "strtostr",
           "retokenize", "repr_dataclass_items", "SubscriptableMetaClass"]

# Import standard libraries.
import ast
import pprint
import re
import string
import textwrap

# For type hinting.
from collections.abc import Generator
from typing          import Any


def get_default(description: str) -> tuple[str, str | None]:
    """
    Get default value.

    Args:
        description (str): [IN] Description message contains default value.

    Returns:
        (tuple): A tuple of (rest of description, default value string).

    Examples:
        >>> get_default("sample description [default: value]")
        ('sample description', 'value')
    """
    default_pattern: str = r"^(.*)\s+\[default:\s*([^\]]+)\]\s*$"

    # Search default string.
    m: re.Match[str] | None = re.fullmatch(default_pattern, description)

    # Returns entire description and None if no default string found.
    if m is None:
        return (description.strip(), None)

    # Otherwise, returns rest of descriptions and default string.
    return (m.group(1).strip(), m.group(2).strip())


def get_error_marker(line: str, token: str) -> str:
    """
    Args:
        line  (str): [IN] Entire line.
        token (str): [IN] Target token.

    Returns:
        (str): Error marker string like.

    Examples:
        >>> get_error_marker("this is a pen", "pen")
        '          ^^^'
        >>> get_error_marker("this is a pen", "pencil")
        '             '
    """
    pos: int = line.find(token)

    # Returns whitespace if the token not found in the line.
    if pos < 0:
        return " " * len(line)

    return " " * pos + "^" * len(token) + " " * (len(line) - len(token) - pos)


def get_section_lines(docstr: str, pattern: str) -> Generator[str]:
    """
    Parse docstring and split it to sections.

    Args:
        docstr  (str): [IN] Input docstring.
        pattern (str): [IN] Target section name pattern.

    Returns:
        (Generator[str]): Lines of specified section.
    """
    for line, _ in get_section_lines_and_names(docstr, pattern):
        yield line


def get_section_lines_and_names(docstr: str, pattern: str) -> Generator[tuple[str, str]]:
    """
    Parse docstring and split it to sections.

    Args:
        docstr  (str): [IN] Input docstring.
        pattern (str): [IN] Target section name pattern.

    Returns:
        (Generator[tuple[str, str]]): Lines of specified section.
    """
    def get_indent(text: str) -> str:
        """
        Get indent of the given text.
        """
        match: re.Match | None = re.match(r"^(\s*)", text)
        return match.group(1) if (match is not None) else ""

    # Initialize the section type.
    section_name     : str  = ""
    is_target_section: bool = False

    # Initialize output lines.
    lines: list[tuple[str, str]] = []

    for line in docstr.split("\n"):

        # Strip unnecessary whitespaces from right.
        line = line.rstrip()

        # Update the section flag (colon expression).
        if line.endswith(":"):
            section_name = line[:-1].strip()
            is_target_section = pattern in section_name.lower()

        # Update the section flag (bracket expression).
        elif line.startswith("[") and line.endswith("]"):
            section_name = line[1:-1].strip()
            is_target_section = pattern in section_name.lower()

        # Returns the current line if the line is inside the target section.
        elif is_target_section and line.strip() and (line[0] in string.whitespace):
            lines.append((line, section_name))

    # Do nothing if the target section is empty.
    if len(lines) == 0:
        return

    # Get indent of the target section.
    indent: str = get_indent(lines[0][0])

    # Process multiple line.
    while lines:

        (line, name) = lines.pop(0)

        # Appent lines if the indent does not match.
        while lines and (get_indent(lines[0][0]) != indent) and (lines[0][1] == name):
            line += " " + lines.pop(0)[0].lstrip()

        yield (line, name)


def find_nearest_str(target: str, texts: set[str]) -> str:
    """
    Returns the nearest string in the string list (in terms of Levenshtein distance).

    Args:
        target (str)     : Target string.
        texts  (set[str]): Set of strings to be searched.

    Returns:
        (str): Nearest string in the texts.
    """
    def levenshtein_distance(src: str, dst: str) -> int:
        """
        Simple implementation of Levenshtein distance from "src" to "dst", the minimum number of
        single-character edits (insertions, deletions or substitutions) required to change one word
        into the other.

        Args:
            src (str): [IN] Source string.
            dst (str): [IN] Destination string.

        Returns:
            (int): Levenshtein distance between "src" and "dst".

        Example:
            >>> levenshtein_distance("kitten", "sitting")
            3
        """
        n_src: int = len(src)
        n_dst: int = len(dst)

        # Initialize the distance metrix.
        mat: list[list[int]] = [[0] * (n_dst + 1) for _ in range(n_src + 1)]
        for i in range(n_src + 1):
            mat[i][0] = i
        for j in range(n_dst + 1):
            mat[0][j] = j

        for i in range(1, n_src + 1):
            for j in range(1, n_dst + 1):
                cost: int = 0 if (src[i - 1] == dst[j - 1]) else 1
                mat[i][j] = min(mat[i-1][j  ] + 1,     # insertion
                                mat[i  ][j-1] + 1,     # deletion
                                mat[i-1][j-1] + cost)  # replacement

        return mat[n_src][n_dst]

    # Convert the set of strings to list.
    list_texts: list[str] = list(texts)

    # Initialize the minimum Levenshtein distance and it's index.
    (idx_min, min_val) = (0, levenshtein_distance(target, list_texts[0]))

    # Update the minimum distance and it's index.
    for idx, text in enumerate(list_texts[1:], start=1):
        val: int = levenshtein_distance(target, text)
        if val < min_val:
            (idx_min, min_val) = (idx, val)

    return list_texts[idx_min]


def strtobool(s: str) -> bool | None:
    """
    Convert the given string to bool instance. The function `bool(...)` is not suitable
    for this purpose, because `bool("False")` returns `True`.

    Args:
        s (str): [IN] Input string.

    Returns:
        (bool | None): Corresponding boolean value.

    Examples:
        >>> strtobool("True")
        True
        >>> strtobool("False")
        False
        >>> strtobool("-") is None
        True
    """
    if s.lower() in {"t", "true", "y", "yes", "on", "1"}:
        return True
    if s.lower() in {"f", "false", "n", "no", "off", "0"}:
        return False
    return None


def strtostr(s: str) -> str:
    """
    Convert string expression to string.

    Args:
        s (str): [IN] Input string.

    Returns:
        (str): Corresponding string value.

    Examples:
        >>> strtostr("this is a pen")
        'this is a pen'
        >>> strtostr("'this is a pen'")
        'this is a pen'
        >>> strtostr("'''this is a pen'''")
        'this is a pen'
        >>> strtostr("'1'")
        '1'
        >>> strtostr("'1.0'")
        '1.0'
    """
    try:
        return str(ast.literal_eval(s))
    except (SyntaxError, ValueError):
        return str(s)


def retokenize(argv: list[str]) -> Generator[str]:
    """
    Tokenize the argument vector.

    Args:
        argv (list[str]): [IN] Argument vector to be tokenized.

    Returns:
        (Generator[str]): Re-tokenized tokens.

    Examples:
        >>> list(retokenize(["A=a", "B=b"]))
        ['A', 'a', 'B', 'b']
    """
    for token in argv:
        yield from token.split("=", maxsplit=1)


def repr_dataclass_items(name: str, data: Any) -> str:
    """
    String expression of dataclass that has items.

    Args:
        name (str): [IN] Name of the dataclass.
        data (Any): [IN] Instance of dataclass.

    Returns:
        (str): String expression of the given dataclass.
    """
    # Header of the string expression.
    text: str = f"{name}:\n"

    # Append item info.
    for idx, item in enumerate(data.entries):
        text += f" |-({idx:02d}) " + textwrap.indent(pprint.pformat(item), " |      ")[8:] + "\n"

    # Append docstring info.
    text += f" |-(docstr) str of length {len(data.docstr)}"

    return text.strip()


class SubscriptableMetaClass(type):
    """
    Mateclass to make class subscriptable.
    """
    def __getitem__(cls, key: str, default: Any = None) -> Any:
        """
        """
        return cls.__dict__.get(key, default)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
