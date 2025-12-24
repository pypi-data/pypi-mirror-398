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

import pathlib
import pydantic
import yadopt

class CommandlineArgumentsModel(pydantic.BaseModel):
    """
    Pydantic model for validation.
    """
    config_path: pathlib.Path
    epochs: int
    model: str
    lr: float = pydantic.Field(ge=0.0, le=1.0)

if __name__ == "__main__":

    # Parse command-line arguments using YadOpt.
    args = yadopt.parse(__doc__)

    # Validate using the Pydantic model.
    valid_args = CommandlineArgumentsModel(**yadopt.to_dict(args))
    print(valid_args)

# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
