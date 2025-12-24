"""
Usage:
    03_subcommand.py foo [--foo_opt INT]
    03_subcommand.py bar [--bar_opt INT]
    03_subcommand.py --help

Example of subcommands.

Options:
    --foo_opt INT   Options of subcommand foo.   [default: 0]
    --bar_opt STR   Options of subcommand bar.   [default: 0]

Other options:
    -h, --help      Show this help message and exit.
"""

# Import YadOpt.
import yadopt


def main():
    """
    Entry point of this script.
    """
    args = yadopt.parse(__doc__)
    print(args)


if __name__ == "__main__":
    main()


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
