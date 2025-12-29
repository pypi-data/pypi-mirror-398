<div align="center">
  <img src="docs/images/yadopt_logo.svg" width="80%">
</div>

<div align="center">
  <img src="https://img.shields.io/badge/PYTHON-%3E%3D3.10-blue.svg?style=for-the-badge&logo=python&logoColor=white">
  &nbsp;
  <img src="https://img.shields.io/badge/LICENSE-MIT-orange.svg?style=for-the-badge">
  &nbsp;
  <img src="https://img.shields.io/badge/COVERAGE-99%25-green.svg?style=for-the-badge">
  &nbsp;
  <img src="https://img.shields.io/badge/QUALITY-10.0/10.0-yellow.svg?style=for-the-badge">
</div>

YadOpt - Yet another docopt
====================================================================================================

YadOpt is a Python re-implementation of [docopt](https://github.com/docopt/docopt) and
[docopt-ng](https://github.com/jazzband/docopt-ng), a human-friendly command-line argument parser
with type hinting and utility functions. YadOpt helps you creating beautiful command-line
interfaces, just like docopt and docopt-ng. However, **YadOpt also supports (1) date type hinting,
(2) conversion to dictionaries and named tuples, and (3) save and load functions**.

The following is the typical usage of YadOpt:

```python
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
    args = yadopt.parse(__doc__)
    print(args)
```

Please save the above code as `sample.py` and run it as follows:

```console
$ python3 sample.py config.toml --epochs 10 --model=cnn
YadOptArgs(config_path=config.toml, epochs=10, model=cnn, lr=0.001, help=False)
```

In the above code, the parsed command-line arguments are stored in the `args` variable, and you can
access each argument using dot notation, like `arg.config_path`. Also, the parsed command-line
arguments are typed, in other words, the `args` variable satisfies the following assertions:

```python
assert isinstance(args.config_path, pathlib.Path)
assert isinstance(args.epochs, int)
assert isinstance(args.model, str)
assert isinstance(args.lr, float)
assert isinstance(args.help, bool)
```

More realistic examples can be found in the [examples](./examples/README.md) directory.


Installation
----------------------------------------------------------------------------------------------------

Please install from [pip](https://pip.pypa.io/en/stable/).

```console
$ pip install yadopt
```


Usage
----------------------------------------------------------------------------------------------------

### Use `parse` function

The `yadopt.parse` function allows you to parse command-line arguments based on your docstring.
The function is designed to parse `sys.argv` by default, but you can explicitly specify the argument
vector by using the second argument of the function, just like as follows:

```python
# Parse "sys.argv" (default behaviour).
args = yadopt.parse(__doc__)

# Parse the given argument vector "argv".
args = yadopt.parse(__doc__, argv)
```

### Use `wrap` function

YadOpt supports the decorator approach for command-line parsing by the decorator `@yadopt.wrap`
which takes the same arguments as the function `yadopt.parse`.

```python
@yadopt.wrap(__doc__)
def main(args: yadopt.YadOptArgs, arg1: int, arg2: str):
    ...

if __name__ == "__main__":
    main(arg1=1, arg2="2")
```

### How to type arguments and options

YadOpt provides two ways to type arguments and options: (1) type name postfix and (2) description
head declaration.

**(1) Type name postfix**: Users can type arguments and options by adding a type name at the end of
the arguments/options name, such as the following:

```
Options:
    --opt1 FLT    Option of float type.
    --opt2 STR    Option of string type.
```

**(2) Description head declaration**: An alternative way to type arguments and options is
to precede the description with the type name in parentheses.

```
Options:
    --opt1 VAL1    (float) Option of float type.
    --opt2 VAL2    (str)   Option of string type.
```

The following is the list of available type names.

| Data type in Python | Type name in YadOpt          |
|---------------------|------------------------------|
| `bool`              | bool, BOOL, boolean, BOOLEAN |
| `int`               | int, INT, integer, INTEGER   |
| `float`             | flt, FLT, float FLOAT        |
| `str`               | str, STR, string, STRING     |
| `pathlib.Path`      | path, PATH                   |


### Dictionary and named tuple support

The returned value of `yadopt.parse` is an instance of `YadOptArgs`, a regular mutable Python class.
However, sometimes a dictionary with the `get` accessor, or an immutable named tuple, may
be preferable. In such cases, please try `yadopt.to_dict` or `yadopt.to_namedtuple` function.

```python
# Convert the returned value to dictionary.
args = yadopt.to_dict(yadopt.parse(__doc__))

# Convert the returned value to namedtuple.
args = yadopt.to_namedtuple(yadopt.parse(__doc__))
```

### Restore arguments from a file

YadOpt has the ability to save parsed argument instances to a file and restore them from the file.
These features are useful, for example, in machine learning code, when you want to call exactly
the same arguments again after a previous execution. Supported file formats include TOML and JSON.

```python
# At first, create a parsed arguments (i.e. YadOptArgs instance).
args = yadopt.parse(__doc__)

# Save the parsed arguments as a TOML file.
yadopt.save("args.toml", args)

# Resotre parsed YadOptArgs instance from the TOML file.
args_restored = yadopt.load("args.toml")
```

The format of the TOML and JSON file is pretty straightforward &mdash; what the user types
on the command line is stored in the `"argv"` key, and the docstring is stored in the `"docstr"`
key in the TOML/JSON file. If users want to write the TOML/JSON file manually, the author recommends
making a TOML/JSON file using the `yadopt.save` function at first and investigating the contents
of the file.


API reference
----------------------------------------------------------------------------------------------------

See [API reference page](https://tiskw.github.io/yadopt/index.html#sec4) of the online document.


Tips
----------------------------------------------------------------------------------------------------

### Merge two YadOptArgs objects

The `YadOptArgs` class, which is the return value of the `yadopt.parse` function, supports the merge
operator `|`, similar to Python's dictionary type. This operator combines the two given YadOptArgs
objects into a new one. In case of a key conflict, the values from the left-hand operand are used.

This merge operator is particularly useful for implementing a feature to read an existing
configuration file (for example, a file specified with the `--config` argument) and then overwrite
those settings with values explicitly provided in the command line arguments. For example:

```python
"""
Usage:
    train.py <config_path> [--epochs INT] [--model STR] [--lr FLT]
    train.py --help

Train a neural network model.

Arguments:
    config_path     Path to base config file.

Training options:
    --epochs INT    The number of training epochs.   [default: 100]
    --model STR     Neural network model name.       [default: mlp]
    --lr FLT        Learning rate.                   [default: 1.0E-3]

Other options:
    -h, --help      Show this help message and exit.
"""

import yadopt

if __name__ == "__main__":

    # Parse the command line arguments.
    args = yadopt.parse(__doc__, ignore_default_values=True)

    # Load the base config file.
    args_base = yadopt.load(args.config_path)

    # Update the parsed command line arguments.
    args_updated = args | args_base
    print(args_updated)
```

### More complex validations for the input command-line arguments

If you want more complex validations for the command-line arguments, the author recommends using
[Pydantic](https://docs.pydantic.dev/latest/) for the dictionary form of the parsed object generated
by YadOpt. Let me explain it using the sample code at the beginning of this README. Suppose you
want to constrain the command line argument "lr" such that "0 <= lr <= 1.0". The following code
will achieve that:

```python
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
```

(It might be a good idea to add features to YadOpt that make it easier for users to implement
the above code. However, the author hasn't implemented it yet because he wants to keep
the dependency of YadOpt small.)


Developer's note
----------------------------------------------------------------------------------------------------

### Preparation

Additional commands and Python packages are required for developers to measure the number of lines
in the code, code quality, etc. Please run the following command (the author recommends using
[venv](https://docs.python.org/3/library/venv.html) to avoid polluting your development
environment).

```console
$ apt install cloc docker.io
$ pip install -r requirements-dev.txt
```

### Utility commands for developers

Utility commands are summarized in the Makefile. Please run `make` at the root directory of this
repository to see the details of the subcommands in the Makefile.

```console
$ make
Usage:
    make <command>

Build commands:
    build         Build package
    testpypi      Upload package to TestPyPi
    pypi          Upload package to PyPi
    install-test  Install from TestPyPi

Test and code check commands:
    check         Check the code quality
    count         Count the lines of code
    coverage      Measure code coverage
	test          Run test on this device
	testall       Run test on Docker

Other commands:
    clean         Cleanup cache files
    help          Show this message
```

### Architecture diagram

![software\_architecture](./docs/images/software_architecture.svg)

