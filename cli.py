"""Command-line adapter for the calculator domain."""

import argparse
import sys
from decimal import Decimal
from typing import Sequence

from .application import Calculator
from .errors import CalculationError


def _format(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f") if normalized == normalized.to_integral() else str(normalized)


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Perform a precise arithmetic calculation.",
        usage="%(prog)s LEFT OPERATION RIGHT | %(prog)s sqrt VALUE",
    )
    parser.add_argument(
        "arguments",
        metavar="ARG",
        nargs="+",
        help="binary calculation or 'sqrt VALUE'",
    )
    return parser


def build_parser(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return _create_parser().parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser(argv)
    arguments = args.arguments

    try:
        calculator = Calculator()
        if len(arguments) == 2 and arguments[0].lower() == "sqrt":
            result = calculator.square_root(arguments[1])
        elif len(arguments) == 3:
            result = calculator.calculate(*arguments)
        else:
            _create_parser().error("expected LEFT OPERATION RIGHT or sqrt VALUE")
        print(_format(result))
    except CalculationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
