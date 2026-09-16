"""Operation strategies and their registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal, getcontext, localcontext

from .errors import DivisionByZeroError, InvalidOperandError, UnknownOperationError


class Operation(ABC):
    """Strategy interface for a binary calculation."""

    symbol: str

    @abstractmethod
    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        """Return the result of applying the operation."""


class UnaryOperation(ABC):
    """Strategy interface for a unary calculation."""

    symbol: str

    @abstractmethod
    def execute(self, operand: Decimal) -> Decimal:
        """Return the result of applying the operation."""


class Add(Operation):
    symbol = "+"

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        return left + right


class Subtract(Operation):
    symbol = "-"

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        return left - right


class Multiply(Operation):
    symbol = "*"

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        return left * right


class Divide(Operation):
    symbol = "/"

    def execute(self, left: Decimal, right: Decimal) -> Decimal:
        if right == 0:
            raise DivisionByZeroError("Cannot divide by zero")
        return left / right


class SquareRoot(UnaryOperation):
    """Return a context-rounded square root for a finite, non-negative value."""

    symbol = "√"
    _guard_digits = 10

    def execute(self, operand: Decimal) -> Decimal:
        if not operand.is_finite():
            raise InvalidOperandError("Square root requires a finite operand")
        if operand.is_signed() and not operand.is_zero():
            raise InvalidOperandError("Cannot calculate the square root of a negative number")

        target_context = getcontext().copy()
        with localcontext(target_context) as work_context:
            work_context.prec += self._guard_digits
            result = operand.sqrt(context=work_context)

        with localcontext(target_context):
            return +result


@dataclass
class OperationRegistry:
    """Registry/factory that resolves strategies by symbol or name."""

    _operations: dict[str, Operation] = field(default_factory=dict)

    def register(self, name: str, operation: Operation, *aliases: str) -> None:
        for key in (name, operation.symbol, *aliases):
            self._operations[key.lower()] = operation

    def resolve(self, key: str) -> Operation:
        try:
            return self._operations[key.lower()]
        except KeyError as exc:
            raise UnknownOperationError(f"Unknown operation: {key}") from exc

    @classmethod
    def with_defaults(cls) -> "OperationRegistry":
        registry = cls()
        registry.register("add", Add(), "plus")
        registry.register("subtract", Subtract(), "minus")
        registry.register("multiply", Multiply(), "times", "x")
        registry.register("divide", Divide())
        return registry
