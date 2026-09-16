"""Behavior-level tests for the calculator's public API and CLI."""

from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal, ROUND_DOWN, ROUND_UP, getcontext, localcontext
from io import StringIO
import unittest

from calculator import CalculationError, Calculator, InvalidOperandError
from calculator.cli import build_parser, main


class SquareRootTests(unittest.TestCase):
    def test_exact_square_root_and_history(self) -> None:
        calculator = Calculator()

        result = calculator.square_root("81")

        self.assertEqual(result, Decimal("9"))
        self.assertEqual(calculator.square_root("0.25"), Decimal("0.5"))
        self.assertEqual(calculator.history[0].expression, "√81")
        self.assertEqual(calculator.history[0].result, Decimal("9"))

    def test_uses_active_precision_and_rounding_without_mutating_context(self) -> None:
        original_precision = getcontext().prec
        original_rounding = getcontext().rounding

        with localcontext() as context:
            context.prec = 5
            context.rounding = ROUND_DOWN
            self.assertEqual(Calculator().square_root("2"), Decimal("1.4142"))

            context.rounding = ROUND_UP
            self.assertEqual(Calculator().square_root("2"), Decimal("1.4143"))

        self.assertEqual(getcontext().prec, original_precision)
        self.assertEqual(getcontext().rounding, original_rounding)

    def test_accepts_signed_zero_and_large_exact_value(self) -> None:
        calculator = Calculator()

        self.assertEqual(calculator.square_root("-0"), Decimal("0"))
        self.assertEqual(calculator.square_root("1E+1000"), Decimal("1E+500"))

    def test_rejects_negative_and_non_finite_values_without_history(self) -> None:
        for value in ("-1", "NaN", "sNaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                calculator = Calculator()
                with self.assertRaises(InvalidOperandError):
                    calculator.square_root(value)
                self.assertEqual(tuple(calculator.history), ())

    def test_rejects_invalid_numeric_text_without_history(self) -> None:
        calculator = Calculator()

        with self.assertRaisesRegex(CalculationError, "Invalid number"):
            calculator.square_root("not-a-number")

        self.assertEqual(tuple(calculator.history), ())


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(arguments)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_square_root_success(self) -> None:
        self.assertEqual(self.run_cli("sqrt", "144"), (0, "12\n", ""))

    def test_build_parser_accepts_explicit_arguments(self) -> None:
        arguments = build_parser(["sqrt", "144"])

        self.assertEqual(arguments.arguments, ["sqrt", "144"])

    def test_square_root_domain_error(self) -> None:
        exit_code, stdout, stderr = self.run_cli("sqrt", "-1")

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("negative number", stderr)

    def test_existing_binary_form_remains_supported(self) -> None:
        self.assertEqual(self.run_cli("2", "add", "3"), (0, "5\n", ""))


if __name__ == "__main__":
    unittest.main()
