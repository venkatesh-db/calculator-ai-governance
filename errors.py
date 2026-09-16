"""Domain-specific exceptions."""


class CalculationError(Exception):
    """Base class for calculator domain errors."""


class DivisionByZeroError(CalculationError):
    """Raised when division by zero is requested."""


class InvalidOperandError(CalculationError):
    """Raised when an operand is outside an operation's accepted domain."""


class UnknownOperationError(CalculationError):
    """Raised when an operation is not registered."""
