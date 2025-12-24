"""
Custom error classes.
"""

# Declare published functins and variables.
__all__ = ["YadOptError"]

# Import standard libraries.
import os
import textwrap

# For type hinting.
from typing import Any

# Import custom modules.
from .color import colorize_error_message
from .utils import get_error_marker


class YadOptErrorBase(Exception):
    """
    Base class of exception in YadOpt.
    """
    EPILOGUE = textwrap.dedent("""
    If you find a bug in YadOpt, please let me know via GitHub issue.
    <https://github.com/tiskw/yadopt/issues>
    """.rstrip())

    def __init__(self, *pargs: Any):
        """
        Constructor.
        """
        self.pargs = pargs

    def __str__(self) -> str:
        """
        Returns string expression of this error.
        """
        return colorize_error_message(self.stringify(*self.pargs))

    def stringify(self, *pargs: Any, **kwargs: Any) -> str:
        """
        Convert myself to a string.
        """
        # Get a docstring.
        docstr: str = textwrap.dedent(self.__doc__) if (self.__doc__ is not None) else ""

        # Returns a string expression of the error class.
        return "\n" + docstr.format(*pargs, **kwargs).strip() + "\n" + self.EPILOGUE


class YadOptErrorUsageParse(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      YadOpt failed to parse a token in the usage section.

    <Location>
      The following line in the usage setion.

        {0}
        {1}

    <Details>
      Each token in the usage section have to follow the specific format.
      For example, all argument tokens should be enclosed by angle bracket,
      all option tokens should be enclosed by bracket, and so on.
      Please see the YadOpt documentation for more details.

    <Solution>
      This is unknown token error therefore no concrete solution can be suggest,
      sorry. Please see the YadOpt documentation and modigy your usage pattern
      in the usage section.
    """
    def __str__(self) -> str:
        """
        Returns string expression of this error.
        """
        line = self.pargs[0].strip()
        mark = "^" * len(line)
        return self.stringify(line, mark)


class YadOptErrorInvalidConstant(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      A constant token appears after an argument or option token.
      This usage pattern is now allowed in YadOpt, sorry.

    <Location>
      The following line in the usage setion.

        {1}
        {2}

    <Details>
      Constant tokens are only allowed at the beginning of a usage.
      For example,

        sample.py subcmd <arg1> bad_constant_token
                                ^^^^^^^^^^^^^^^^^^

      the above "bad_constant_token" cause the error because it appears after
      the argument <arg1>. The same error occurs if a constant token follows
      an option token, for example,

        sample.py subcmd [--opt1 val1] bad_constant_token
                                       ^^^^^^^^^^^^^^^^^^

    <Solution>
      Please remove the constant token from the usage pattern. In some cases,
      you may need to reconsider the usage of your command. If you intended
      the argument, not constant token, please enclose the token in angle brackets
      because all arguments should be enclosed by brackets in the usage section.
    """
    def __str__(self) -> str:
        """
        Returns string expression of this error.
        """
        token  = self.pargs[0]
        line   = self.pargs[1].strip()
        marker = get_error_marker(line, token)
        return self.stringify(token, line, marker)


class YadOptErrorInvalidTypeFunc(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      Invalid type function.

    <Location>
      Argument "type_func" in "yadopt.parse" or "yadopt.wrap" function.

    <Details>
      The type function should be a callable object or None, but the spacified
      object "{0}" does not satisfy either of them.

    <Solution>
      Modify the value of the "type_func" argument.
    """


class YadOptErrorInvalidTypeName(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      Invalid type name '{0}'.

    <Location>
      Argument "type_func" in "yadopt.parse" or "yadopt.wrap" function.

    <Details>
      Type name '{0}' is invalid. Acceptable type names are "int", "integer",
      "flt", "float", or "str", "string", "path", or their uppercases.

    <Solution>
      Modify the type name, or give your custom typing function to "type_fn"
      argument of "yadopt.parse" or "yadopt.wrap" function.
    """


class YadOptErrorInvalidIOFileFormat(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      Invalid I/O file format

    <Location>
      Argument of {0}: {1}

    <Details>
      The "yadopt.save" and "yadopt.load" functions does not support "{2}" format.

    <Solution>
      Please specify the supported file format, for example, ".toml" or ".json".
    """


class YadOptErrorUnknownArgument(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      Unknown argument is found in the usage.

    <Details>
      The argument "{0}" in the usage does exist in arguments definition.
      {1}
    """


class YadOptErrorUnknownOptionUsage(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      Unknown option is found in the usage.

    <Details>
      The option '{0}' in the usage does not exist in the option definition.
      {1}
    """


class YadOptErrorUnknownOptionArgv(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      Unknown option detected in the argument vector.

    <Details>
      Unknown option '{0}' detected in the argument vector.
      {1}
    """


class YadOptErrorValidUsageNotFound(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      Valid usage not found

    <Location>
      {1}
        {2}
        {3}

    <Details>
      The user input does not match any of the command usage.

    <Solution>
      Please check the user input and the command usage.

    {0}
    """
    def __str__(self) -> str:
        """
        Returns string expression of this error.
        """
        line_num = self.pargs[1].lineno
        funcname = self.pargs[1].function
        filename = os.path.basename(self.pargs[1].filename)
        err_pos  = f"{filename} : {funcname} : L.{line_num}"
        err_code = self.pargs[1].code_context[0].strip()
        err_mark = "^" * len(err_code)
        return self.stringify(self.pargs[0], err_pos, err_code, err_mark)


class YadOptErrorCannotLoadTomllib(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      Failed to load a library for parsing TOML file.

    <Details>
      YadOpt uses "tomllib", a standard library of Python, if Python >= 3.11, and
      uses "tomli" otherwise. The "tomli" library is specified as a dependency of
      YadOpt when Python <= 3.10 and will be installed automatically when users
      install YadOpt on Python<= 3.10. However, this mechanism doesn't seem to work
      well for some reason.

    <Solution>
      Please check the tomli library if importable if Python <= 3.10,
      and the tomllib otherwise.
    """


class YadOptErrorCannotMergeDtype(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      Invalid data merge with unexpected datatype.

    <Details>
      Only YadOptArgs objects are supported as operands for the merge operator '|'.
    """


class YadOptErrorInternal(YadOptErrorBase):
    """
    --------------------------------------------------------------------------------
    <Error summary>
      Internal error.

    <Location>
      See the traceback above.

    <Details>
      This error means that something happened that the author didn't anticipate
      during the execution of the YadOpt code, NOT that the user is using
      the library incorrectly.
    """


class YadOptError(YadOptErrorBase):
    """
    General Error class for YadOpt.
    """
    usage_parse            = YadOptErrorUsageParse
    invalid_constant       = YadOptErrorInvalidConstant
    invalid_type_func      = YadOptErrorInvalidTypeFunc
    invalid_type_name      = YadOptErrorInvalidTypeName
    invalid_io_file_format = YadOptErrorInvalidIOFileFormat
    unknown_argument       = YadOptErrorUnknownArgument
    unknown_option_usage   = YadOptErrorUnknownOptionUsage
    unknown_option_argv    = YadOptErrorUnknownOptionArgv
    valid_usage_not_found  = YadOptErrorValidUsageNotFound
    cannot_load_tomllib    = YadOptErrorCannotLoadTomllib
    cannot_merge_dtype     = YadOptErrorCannotMergeDtype
    internal_error         = YadOptErrorInternal


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
