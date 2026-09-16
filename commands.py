"""Command objects used to execute and audit calculations."""

from dataclasses import dataclass
from decimal import Decimal

from .operations import Operation, UnaryOperation


@dataclass(frozen=True)
class CalculationCommand:
    left: Decimal
    right: Decimal
    operation: Operation

    def execute(self) -> Decimal:
        return self.operation.execute(self.left, self.right)


@dataclass(frozen=True)
class UnaryCalculationCommand:
    operand: Decimal
    operation: UnaryOperation

    def execute(self) -> Decimal:
        return self.operation.execute(self.operand)


@dataclass(frozen=True)
class CalculationRecord:
    expression: str
    result: Decimal
