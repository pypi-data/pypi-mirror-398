"""
yadopt.dtypes - collections of data types and classes
"""

# Declare published functions and variables.
__all__ = ["ArgEntry", "ArgsInfo", "OptEntry", "OptsInfo", "UsageOpt", "UsageEntry", "ArgVector", "YadOptArgs"]

# Import standard libraries.
import collections
import copy
import dataclasses
import pathlib

# For type hinting.
from typing import Any, TypeAlias

# Import custom modules.
from .errors import YadOptError
from .utils  import repr_dataclass_items


############################################################
# Path class for YadOpt
############################################################

# File path class for YadOpt.
Path: TypeAlias = pathlib.Path


############################################################
# Data types for parsing docstring
############################################################

@dataclasses.dataclass
class ArgEntry:
    """
    Parsed result of argument definition in docstring.
    """
    name    : str         # Option name.
    type_dsc: str | None  # Data type string written in the head of description.
    desc    : str         # Description of this option.
    default : str | None  # Default value (string).
    group   : str         # Group name of this entry.


@dataclasses.dataclass
class ArgsInfo:
    """
    Arguments information of docstring.
    """
    entries: list[ArgEntry]  # Arguments information.
    docstr : str             # Arguments section of docstring.

    def __str__(self) -> str:
        return repr_dataclass_items("ArgsInfo", self)


@dataclasses.dataclass
class OptEntry:
    """
    Parsed result of option definition in docstring.
    """
    name     : str         # Option name.
    name_alt : str | None  # Alternative option name.
    val_name : str | None  # Name of option value (used for type hinting).
    type_dsc : str | None  # Data type string written in the head of description.
    desc     : str         # Description of this option.
    default  : str | None  # Default value (string).
    group    : str         # Group name of this entry.


@dataclasses.dataclass
class OptsInfo:
    """
    Options information of docstring.
    """
    entries: list[OptEntry]  # Options information.
    docstr : str             # Options section of docstring.

    def __str__(self) -> str:
        return repr_dataclass_items("OptsInfo", self)


@dataclasses.dataclass
class UsageOpt:
    """
    Parsed result of usage definition in docstring.
    """
    name    : str   # Option name.
    has_val : bool  # True if this option has a value.
    required: bool  # True if this option is mandatory.


@dataclasses.dataclass
class UsageEntry:
    """
    Parsed result of usage definition in docstring.
    """
    pres: list[str]       # Preceding tokens.
    args: list[str]       # Argument tokens.
    opts: list[UsageOpt]  # Option tokens.


############################################################
# Data types for parsing argument vector
############################################################

@dataclasses.dataclass
class ArgVector:
    """
    Information of user input.
    """
    pres: dict[str, bool]
    args: dict[str, Any]
    opts: dict[str, str|None]

    def __str__(self):
        text  = "ArgVector:\n"
        text += " |- pres = " + str(self.pres) + "\n"
        text += " |- args = " + str(self.args) + "\n"
        text += " |- opts = " + str(self.opts) + "\n"
        return text.strip()


############################################################
# A class to store parsed results
############################################################

class YadOptArgs:
    """
    Command line arguments parsed by YadOpt.
    """
    def __len__(self) -> int:
        """
        Returns the number of items.
        """
        return len(self.__normal_dict__())

    def __normal_dict__(self) -> dict:
        """
        Returns "normal" dictionary that contains keys not starting with the underscore.
        """
        return {key:value for key, value in self.__dict__.items() if not key.startswith("_")}

    def __named_tuple__(self) -> tuple[Any, ...]:
        """
        """
        args_d: dict = self.__normal_dict__()
        fields: list = list(args_d.keys())
        return collections.namedtuple("YadOptArgs", fields)(**args_d)

    def __repr__(self) -> str:
        """
        Representation of this class.
        """
        return str(self.__named_tuple__())

    def __str__(self) -> str:
        """
        String expression of this class.
        """
        return self.__repr__()

    def __eq__(self, other: object) -> bool:
        """
        Returns True if equivarent.
        """
        if isinstance(other, self.__class__):
            return self.__normal_dict__() == other.__normal_dict__()
        return False

    def __or__(self, other: object) -> object:
        """
        """
        # The operand should be YadOptArgs instance.
        if not isinstance(other, YadOptArgs):
            raise YadOptError.cannot_merge_dtype

        # Create a copy of myself and the attributes dictionary.
        args_copy = copy.deepcopy(self)

        # Update the attributes dictionary.
        args_copy.__dict__ |= other.__dict__

        return args_copy


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
