"""
Usage:
    04_save_and_load.py train [OPTIONS]
    04_save_and_load.py test  [OPTIONS]
    04_save_and_load.py --restore PATH
    04_save_and_load.py --help

Example of "yadopt.load" function.

Training options:
    --epochs INT        The number of training epochs.   [default: 100]
    --model STR         Neural network model name.       [default: mlp]
    --optimizer STR     Optimizer name.                  [default: adamw]
    --lr FLT            Learning rate.                   [default: 1.0E-3]
    --weight_decay FLT  Weight decay.                    [default: 5.0E-4]
    --batch_size INT    Batch size.                      [default: 64]

Other options:
    --restore PATH      Restore saved arguments.         [default: None]
    -h, --help          Show this help message and exit.
"""

import sys
sys.path.append(".")

# Import YadOpt.
import yadopt


@yadopt.wrap(__doc__)
def main(args: yadopt.YadOptArgs):
    """
    Entry point of this script.
    """
    # Restore the saved arguments.
    if args.restore is not None:
        args = yadopt.load(args.restore)

    print(args)


if __name__ == "__main__":
    main()


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
