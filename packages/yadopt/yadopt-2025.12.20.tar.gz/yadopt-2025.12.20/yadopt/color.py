"""
yadopt.color - colorize strings
"""

# Declare published functins and variables.
__all__ = ["colorize_help_message", "colorize_error_message"]

# Import standard libraries.
import re
import sys

# For type hinting.
from .matchers import match_arg, match_opt

# Define colors.
COLOR_ARG: str = "\x1B[33;1m"
COLOR_SHT: str = "\x1B[32;1m"
COLOR_LNG: str = "\x1B[34;1m"
COLOR_SEC: str = "\x1B[35;1m"
COLOR_STR: str = "\x1B[31;1m"
COLOR_NON: str = "\x1B[0m"


def colorize_help_message(help_message: str) -> str:
    """
    Returns colored help message.

    Args:
        help_message (str): Help message.

    Returns:
        (str): Colorized string.
    """
    def colorize_arg(line: str, key: str | None) -> str:
        """
        Colorize argument.
        """
        if key is not None:
            return line.replace(f" {key} ", f" {COLOR_ARG}{key}{COLOR_NON} ", 1)
        return line

    def colorize_opt(line: str, key: str | None) -> str:
        """
        Colorize options.
        """
        if (key is not None) and (f" --{key}" in line):
            return line.replace(f" --{key}", f" {COLOR_LNG}--{key}{COLOR_NON}", 1)
        if (key is not None) and (f" -{key}" in line):
            return line.replace(f" -{key}", f" {COLOR_SHT}-{key}{COLOR_NON}", 1)
        return line

    def colorize_sec(line: str) -> str:
        """
        Colorize_section.
        """
        return COLOR_SEC + line[:-1] + COLOR_NON + ":"

    def colorize_arg_line(line: str) -> str:
        """
        Colorize argument tolens in a line.
        """
        # Parse the line as an argument line, and do nothing if not matched.
        match_info = match_arg(line)[0]
        if len(match_info) == 0:
            return line

        line = colorize_arg(line, match_info[0])
        return line

    def colorize_opt_line(line: str) -> str:
        """
        Colorize option tokens in a line.
        """
        # Parse the line as an option line, and do nothing if not matched.
        match_info = match_opt(line)[0]
        if len(match_info) == 0:
            return line

        line = colorize_opt(line, match_info[0])
        line = colorize_opt(line, match_info[1])
        line = colorize_arg(line, match_info[2])
        return line

    def colorize_usg_line(line: str) -> str:
        """
        Colorize usage line.
        """
        line = re.sub(r"<(\w+)>", f"<{COLOR_ARG}\\1{COLOR_NON}>", line)
        line = re.sub(r"(--\w+)( |\]|$)", F"{COLOR_LNG}\\1{COLOR_NON}\\2", line)
        line = re.sub(r"(-\w+)( |\]|$)", f"{COLOR_SHT}\\1{COLOR_NON}\\2", line)
        line = re.sub(r"\[([^\]]*) (\w+)\]", f"[\\1 {COLOR_ARG}\\2{COLOR_NON}]", line)
        return line

    # Do nothing if the output is TTY.
    if not sys.stdout.isatty():
        return help_message

    # Initialize the output lines.
    output_lines: list[str] = []

    # Initialize section flags.
    is_usg: bool = False
    is_arg: bool = False
    is_opt: bool = False

    # Initialize the output lines.
    for line in help_message.split("\n"):

        # Colorize the line.
        if is_usg:
            line = colorize_usg_line(line)
        elif is_arg:
            line = colorize_arg_line(line)
        elif is_opt:
            line = colorize_opt_line(line)

        # Update section flags.
        if line.endswith(":") or (line.startswith("[") and line.endswith("]")):
            is_usg = "usage"     in line.lower()
            is_arg = "arguments" in line.lower()
            is_opt = "options"   in line.lower()
            line = colorize_sec(line)

        output_lines.append(line)

    return "\n".join(output_lines)


def colorize_error_message(help_message: str) -> str:
    """
    Colorize error message.
    """
    # Colorize section header.
    help_message = re.sub(r"^(<[^>]+>)\s*$", f"{COLOR_SEC}\\1{COLOR_NON}", help_message, flags=re.MULTILINE)

    # Colorize string literal.
    help_message = re.sub(r"('[^\']*')", f"{COLOR_STR}\\1{COLOR_NON}", help_message)
    help_message = re.sub(r'("[^\"]*")', f"{COLOR_STR}\\1{COLOR_NON}", help_message)

    return help_message


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
