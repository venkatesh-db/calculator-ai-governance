# Numeric contracts for precision-sensitive work

Read this reference when a change involves very large or small magnitudes, many significant digits, repeating fractions, powers, roots, scientific functions, non-finite values, or a requested precision/rounding guarantee.

## Decisions to make before implementation

| Concern | Questions the contract must answer |
| --- | --- |
| Operand domain | Decimal literals only, or are exponent notation and other exact forms accepted? |
| Precision | How many significant digits are required, and is the default context sufficient? |
| Rounding | Which Decimal rounding mode applies, and at which operation boundary? |
| Exactness | Must the result be exact, correctly rounded, or within a stated tolerance? |
| Magnitude | What maximum digits, exponent, operand count, or output length is acceptable? |
| Non-finite values | Are `NaN`, signaling NaN, positive infinity, and negative infinity rejected or supported? |
| Zero | How are `0`, `-0`, and equivalent decimal forms handled and displayed? |
| Presentation | Should the CLI use fixed, engineering, or scientific notation for extreme results? |
| Failure | Which public domain error represents overflow, invalid operations, or exceeded limits? |

Do not choose these silently when they affect visible results or compatibility.

## Decimal rules for this project

- Construct a `Decimal` from the original textual representation, not from a binary float.
- Remember that addition, subtraction, multiplication, and division are governed by the active Decimal context; Decimal does not imply unlimited precision.
- Use `decimal.localcontext()` when a calculation needs a feature-specific context. Set its precision, rounding, traps, and exponent behavior explicitly from the accepted contract.
- Quantize only when the contract specifies a scale or rounding boundary. Avoid quantizing merely to make tests convenient.
- Catch only the Decimal signals expected by the operation and translate them to an appropriate `CalculationError` subtype while preserving the cause.
- Decide whether signed zero is semantically significant. Division must reject every numeric zero representation even if display normalizes it.

## Growth and resource review

Before adding factorials, exponentiation, combinatorics, roots, or aggregate calculations, evaluate:

- Input-size validation before expensive work begins.
- Worst-case digits and output size.
- Algorithmic time and memory growth.
- Decimal context limits and trapped signals.
- Whether cancellation or an explicit limit is needed at the public boundary.

Prefer a small, explicit product limit over an unbounded calculation that can exhaust memory or monopolize the process. A limit is public behavior and requires tests and documentation.
