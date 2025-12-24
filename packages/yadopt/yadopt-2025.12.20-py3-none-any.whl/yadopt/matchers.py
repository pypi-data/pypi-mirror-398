"""
yadopt.machers - utility class to match string using regular expression
"""

# Declare published functions and variables.
__all__ = ["match_arg", "match_opt"]

# Import standard libraries.
import re

# Alias for data type annotations.
PatternType = tuple[str, list[int], bool]
MatchedType = tuple[tuple[str | None, ...], str, bool]

# Define matching patterns.
PATTERNS_AND_INDICES_ARG: list[PatternType] = [
    # regular expression, [name index], optional flag
    # ------------------------------------------------
    (r"\s+(\w+)",         [1],          False),
]
PATTERNS_AND_INDICES_OPT: list[PatternType] = [
    # regular expression,        (name, alt, value), has_value # | type  | value  | delim |
    # -------------------------------------------------------- # --------------------------
    (r"\s+-(\w+)=(\w+), --(\w+)=(\w+)", [3,  1,  2], True ),   # | both  | double | equal |
    (r"\s+-(\w+) (\w+), --(\w+) (\w+)", [3,  1,  2], True ),   # | both  | double | space |
    (r"\s+-(\w+), --(\w+)=(\w+)",       [2,  1,  3], True ),   # | both  | single | equal |
    (r"\s+-(\w+), --(\w+) (\w+)",       [2,  1,  3], True ),   # | both  | single | space |
    (r"\s+-(\w+), --(\w+)",             [2,  1, -1], False),   # | both  | none   | -     |
    (r"\s+--(\w+)=(\w+)",               [1, -1,  2], True ),   # | long  | single | equal |
    (r"\s+--(\w+) (\w+)",               [1, -1,  2], True ),   # | long  | single | space |
    (r"\s+--(\w+)",                     [1, -1, -1], False),   # | long  | none   | -     |
    (r"\s+-(\w+)=(\w+)",                [1, -1,  2], True ),   # | short | single | equal |
    (r"\s+-(\w+) (\w+)",                [1, -1,  2], True ),   # | short | single | space |
    (r"\s+-(\w+)",                      [1, -1, -1], False),   # | short | none   | -     |
]
PATTERNS_AND_INDICES_SEC: list[PatternType] = [
    # regular expression,  [section_name_index], Dummy flag #
    # ----------------------------------------------------- #
    (r"^([\w ]+):\s*$",    [1,],                 False),    # SectionName:
    (r"^\[([\w ]+)\]\s*$", [1,],                 False),    # [SectionName]
]


def match_and_get(line: str, patterns_and_indices: list[PatternType]) -> MatchedType:
    """
    Parse the given string and returns specified matched strings.

    Args:
        line (str) : [IN] The target line.

    Returns:
        (tuple[str]): A tuple of matched strings corresponding to the indices,
                      and the rest of matched strings.

    Examples:
        >>> match_and_get("-h, --help", [(r"-(\\w+), --(\\w+)", (2, 1), None)])
        (('help', 'h'), '', None)
    """
    for pattern, indices, optional_flag in patterns_and_indices:

        # Compute regular expression match, and continue the loop if not matched.
        if (m := re.match(pattern, line, re.ASCII)) is None:
            continue

        # Get the required matched strings.
        output: list[str | None] = [None if idx < 0 else m[idx] for idx in indices]

        # Get the rest of the matched strings.
        rest: str = line[len(m.group(0)):]

        return (tuple(output), rest, optional_flag)

    return ((), line, False)


def match_arg(line: str) -> MatchedType:
    """
    Parse arguments line.

    Args:
        line (str): Target string.

    Returns:
        (MatchedType): A tuple of matched strings.
    """
    return match_and_get(line, PATTERNS_AND_INDICES_ARG)


def match_opt(line: str) -> MatchedType:
    """
    Parse arguments line.

    Args:
        line (str): [IN] Target string.

    Returns:
        (MatchedType): A tuple of matched strings.

    Examples:
        >>> match_opt("  -h, --help   show this message and exit.")
        (('help', 'h', None), '   show this message and exit.', False)
    """
    return match_and_get(line, PATTERNS_AND_INDICES_OPT)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
