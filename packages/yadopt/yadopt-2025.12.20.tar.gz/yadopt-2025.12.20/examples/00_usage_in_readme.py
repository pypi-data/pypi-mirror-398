"""
Usage:
    train.py <config_path> [--epochs INT] [--model STR] [--lr FLT]
    train.py --help

Train a neural network model.

Arguments:
    config_path     Path to config file.

Training options:
    --epochs INT    The number of training epochs.   [default: 100]
    --model STR     Neural network model name.       [default: mlp]
    --lr FLT        Learning rate.                   [default: 1.0E-3]

Other options:
    -h, --help      Show this help message and exit.
"""

import yadopt

if __name__ == "__main__":
    argv = ["train.py", "config.toml", "--epochs", "10", "--model=cnn"]
    args = yadopt.parse(__doc__, argv)
    print(args)

# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
