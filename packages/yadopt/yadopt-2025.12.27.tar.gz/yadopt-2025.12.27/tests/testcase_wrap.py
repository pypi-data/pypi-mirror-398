"""
Test for wrap function of YadOpt.
"""

# Import standard libraries.
import sys

# Import Yadopt.
sys.path.append(".")
import yadopt


docstring = """
Usage:
    train.py <config_path> [--epochs INT] [--model STR] [--lr FLT] [--output PATH] [--verbose]
    train.py --help

Train a neural network model.

Arguments:
    config_path     Path to config file.

Training options:
    --epochs INT    The number of training epochs.   [default: 100]
    --model STR     Neural network model name.       [default: mlp]
    --lr FLT        Learning rate.                   [default: 1.0E-3]

Output options:
    --output PATH   Path to output directory.        [default: runs]

Other options:
    -h, --help      Show this help message and exit.
    -v, --verbose   Enables verbose output.
"""

argv = ["train.py", "config.toml", "--epochs", "10", "--model=cnn"]


@yadopt.wrap(docstring, argv)
def main(args: yadopt.YadOptArgs, real_arg: str):
    """
    Target of yadopt.wrap function.
    """
    # Check parsed arguments.
    assert args.config_path == yadopt.Path("config.toml")
    assert args.epochs == 10
    assert args.model == "cnn"
    assert abs(args.lr - 1.0E-3) < 1.0E-8
    assert args.output == yadopt.Path("runs")
    assert args.help == False
    assert args.verbose == False

    # Check the other arguments.
    assert real_arg == "real argument"

    # Print YadOptArgs just for a test.
    print(args)


def test():
    """
    Entry point of the test.
    """
    # Call the main function that is decorated by yadopt.wrap function.
    main("real argument")


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
