"""Application facade for calculator clients."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Iterable

from .commands import CalculationCommand, CalculationRecord, UnaryCalculationCommand
from .errors import CalculationError
from .operations import OperationRegistry, SquareRoot


class Calculator:
    """Facade coordinating parsing, operation lookup, execution, and history."""

    def __init__(self, registry: OperationRegistry | None = None) -> None:
        self._registry = registry or OperationRegistry.with_defaults()
        self._history: list[CalculationRecord] = []

    def calculate(self, left: object, operation: str, right: object) -> Decimal:
        left_value = self._to_decimal(left)
        right_value = self._to_decimal(right)
        strategy = self._registry.resolve(operation)
        command = CalculationCommand(left_value, right_value, strategy)
        result = command.execute()
        self._history.append(
            CalculationRecord(
                expression=f"{left_value} {strategy.symbol} {right_value}",
                result=result,
            )
        )
        return result

    def square_root(self, value: object) -> Decimal:
        operand = self._to_decimal(value)
        strategy = SquareRoot()
        command = UnaryCalculationCommand(operand, strategy)
        result = command.execute()
        self._history.append(
            CalculationRecord(expression=f"{strategy.symbol}{operand}", result=result)
        )
        return result

    @property
    def history(self) -> Iterable[CalculationRecord]:
        return tuple(self._history)

    def clear_history(self) -> None:
        self._history.clear()

    @staticmethod
    def _to_decimal(value: object) -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise CalculationError(f"Invalid number: {value!r}") from exc
