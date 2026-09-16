"""Extensible calculator package."""

from .application import Calculator
from .errors import (
    CalculationError,
    DivisionByZeroError,
    InvalidOperandError,
    UnknownOperationError,
)

__all__ = [
    "Calculator",
    "CalculationError",
    "DivisionByZeroError",
    "InvalidOperandError",
    "UnknownOperationError",
]
