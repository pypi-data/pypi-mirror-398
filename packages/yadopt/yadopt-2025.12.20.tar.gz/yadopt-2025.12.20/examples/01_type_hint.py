"""
Usage:
    01_type_hint.py <config_path> [--epochs INT] [--model STR] [--lr FLT]
    01_type_hint.py --help

Example if type hinting.

Arguments:
    config_path     Path to config file.

Training options:
    --epochs INT    The number of training epochs.   [default: 100]
    --model STR     Neural network model name.       [default: mlp]
    --lr FLT        Learning rate.                   [default: 1.0E-3]

Other options:
    -h, --help      Show this help message and exit.
"""

# Import standard libraries.
import pathlib

# Import YadOpt.
import yadopt


def main():
    """
    Entry point of this script.
    """
    # Parse command line arguments using YadOpt.
    args = yadopt.parse(__doc__)
    print(args)

    # Data type assertions.
    assert isinstance(args.config_path, pathlib.Path)
    assert isinstance(args.epochs, int)
    assert isinstance(args.model, str)
    assert isinstance(args.lr, float)
    assert isinstance(args.help, bool)


if __name__ == "__main__":
    main()


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
