"""
Usage:
    02_decorator.py <config_path> [--epochs INT] [--model STR] [--lr FLT]
    02_decorator.py --help

Example of the decorator "yadopt.wrap".

Arguments:
    config_path     Path to config file.

Training options:
    --epochs INT    The number of training epochs.   [default: 100]
    --model STR     Neural network model name.       [default: mlp]
    --lr FLT        Learning rate.                   [default: 1.0E-3]

Other options:
    -h, --help      Show this help message and exit.
"""

# Import YadOpt.
import yadopt


@yadopt.wrap(__doc__, verbose=True)
def main(args: yadopt.YadOptArgs):
    """
    Entry point of this script.
    """
    print(args)


if __name__ == "__main__":
    main()


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
