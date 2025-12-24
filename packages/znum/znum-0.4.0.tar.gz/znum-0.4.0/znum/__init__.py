"""
Znum - Z-number data type for fuzzy arithmetic and multi-criteria decision making.

A Z-number is a fuzzy number with two parts:
- A: The main fuzzy set values (restriction on values)
- B: The confidence/belief values (reliability of A)

Example:
    >>> from znum import Znum
    >>> z1 = Znum([1, 2, 3, 4], [0.1, 0.2, 0.3, 0.4])
    >>> z2 = Znum([2, 4, 8, 10], [0.5, 0.6, 0.7, 0.8])
    >>> z3 = z1 + z2
    >>> print(z3)
"""

from .core import Znum
from .topsis import Topsis
from .vikor import Vikor
from .promethee import Promethee
from .utils import Beast
from .exceptions import (
    InvalidAPartOfZnumException,
    InvalidBPartOfZnumException,
    InvalidZnumDimensionException,
    InvalidZnumCPartDimensionException,
    IncompatibleABPartsException,
    ZnumMustBeEvenException,
    ZnumsMustBeInSameDimensionException,
)

__version__ = "0.1.0"

__all__ = [
    "Znum",
    "Topsis",
    "Vikor",
    "Promethee",
    "Beast",
    "InvalidAPartOfZnumException",
    "InvalidBPartOfZnumException",
    "InvalidZnumDimensionException",
    "InvalidZnumCPartDimensionException",
    "IncompatibleABPartsException",
    "ZnumMustBeEvenException",
    "ZnumsMustBeInSameDimensionException",
]
