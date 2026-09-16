# Calculator validation matrix

Select the rows affected by the change; do not mechanically add irrelevant tests. New public behavior should have a success case, a domain-failure case where applicable, and a CLI case when users can invoke it there.

| Area | Representative checks |
| --- | --- |
| Default arithmetic | Add, subtract, multiply, and divide with positive, negative, zero, fractional, and large-magnitude operands |
| Lookup | Names, symbols, aliases, mixed case, unknown operation, and shared-namespace collisions |
| Parsing | Integer, decimal fraction, exponent notation if accepted, malformed text, and objects whose string form is invalid |
| Zero semantics | `0`, `-0`, `0.0`, and `-0.000`; every divisor form must follow the same zero rule |
| Precision | Values at and beyond context precision, repeating division, accepted rounding mode, and no float-conversion artifacts |
| Extreme values | Large positive/negative exponent, maximum accepted digit count, output-size limit, and one value beyond each limit |
| Non-finite values | `NaN`, `sNaN`, `Infinity`, and `-Infinity` according to the accepted policy |
| History | Successful record, failed calculation omitted, stable expression, immutable external view, and clear operation |
| Errors | Correct public subtype, useful message, preserved cause, and no raw expected implementation exception at the CLI |
| CLI | stdout result, stderr diagnostic, success/error exit codes, formatting, and documented module invocation |
| Compatibility | Existing exports, default aliases, case-insensitive lookup, and unchanged behavior outside the feature |

## Test design rules

- Compute expected values from an independently stated contract, not by duplicating the production algorithm.
- Compare Decimal values exactly when the operation is specified as exact.
- For approximate functions, use an accepted error bound and state whether it is absolute, relative, or units-in-last-place.
- Include a regression test that fails for the original defect before applying a bug fix when feasible.
- Verify that tests detect registry collisions, context leakage, history-on-failure, and CLI stream/exit-code regressions rather than only testing a private helper.
