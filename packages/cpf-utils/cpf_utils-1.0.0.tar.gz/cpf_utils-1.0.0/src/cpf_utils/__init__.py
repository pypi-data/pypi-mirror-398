from cpf_fmt import (
    CpfFormatter,
    CpfFormatterError,
    CpfFormatterHiddenRangeError,
    CpfFormatterInputLengthError,
    CpfFormatterOptions,
    cpf_fmt,
)
from cpf_gen import (
    CpfGenerator,
    CpfGeneratorError,
    CpfGeneratorOptions,
    CpfGeneratorPrefixLengthError,
    CpfGeneratorPrefixNotValidError,
    cpf_gen,
)
from cpf_val import CpfValidator, cpf_val

from .cpf_utils import CpfUtils

__all__ = [
    "CpfFormatter",
    "CpfFormatterError",
    "CpfFormatterHiddenRangeError",
    "CpfFormatterInputLengthError",
    "CpfFormatterOptions",
    "CpfGenerator",
    "CpfGeneratorError",
    "CpfGeneratorOptions",
    "CpfGeneratorPrefixLengthError",
    "CpfGeneratorPrefixNotValidError",
    "CpfUtils",
    "CpfValidator",
    "cpf_fmt",
    "cpf_gen",
    "cpf_utils",
    "cpf_val",
]

__version__ = "1.0.0"

# Default instance of CpfUtils
cpf_utils = CpfUtils()
