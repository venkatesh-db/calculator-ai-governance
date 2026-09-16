---
name: calculator-engineering
description: Build, extend, debug, or test this Python Decimal calculator for ordinary arithmetic and precision-sensitive or very large calculations. Use for calculator operations, numeric contracts, registry behavior, history, public errors, and CLI behavior; do not use for unrelated Python work or for merely solving a math problem.
---

# Calculator Engineering

Work inside the calculator project and obey its `AGENTS.md`, including code-file inventory and ledger updates. Preserve the existing split between the `Calculator` facade, operation strategies and registry, command/history values, domain errors, and CLI adapter.

## Select the numeric mode

- For ordinary arithmetic changes whose expected result is exact under the existing Decimal context, preserve the current context and public behavior.
- For very large values, very small values, long fractional results, powers, roots, scientific functions, or any request that depends on significant digits, read [references/numeric-contracts.md](references/numeric-contracts.md) before designing the change.
- If the requested behavior depends on unspecified precision, rounding, exponent limits, non-finite values, or output notation, present the relevant choices and obtain a decision before changing those contracts.

Never route input through binary floating point. Convert external operands with the project's established string-to-`Decimal` boundary unless an accepted contract requires another exact representation.

## Implement a calculator change

1. Inspect `application.py`, `operations.py`, `commands.py`, `errors.py`, `cli.py`, exports, and relevant tests together. Record existing behavior before editing.
2. State the observable result, accepted numeric contract, compatibility constraints, and checks that will prove completion.
3. Put arithmetic in the smallest `Operation` strategy. Keep parsing, resolution, execution, history ownership, formatting, streams, and exit codes in their current owning layers.
4. Register a new operation consistently by name, symbol, and approved aliases. Treat all registry keys as one case-insensitive namespace and define collision behavior rather than silently replacing entries.
5. Translate expected numeric or operation failures into the public `CalculationError` hierarchy with exception chaining. Do not hide programming defects behind a broad catch.
6. Append history only after successful execution and never expose the mutable internal history list.
7. Add behavior-level tests using the applicable cases in [references/validation-matrix.md](references/validation-matrix.md). Test through the public facade and CLI where the contract is externally visible.
8. Update the `AGENTS.md` inventory and append-only ledger in the same change for every added, modified, renamed, moved, or deleted code file.

## Large-calculation safeguards

Treat “large” as a contract question, not merely a long input string. Determine whether it means large magnitude, many digits, expensive exponentiation, a large operand collection, or strict high precision.

- Estimate computational and output growth before executing potentially explosive operations.
- Reject or bound operations whose time, memory, or output size would be unreasonable for the local CLI, using an explicit domain error and documented limit.
- Apply a local decimal context when a feature needs a chosen precision or rounding rule; do not mutate the process-wide context as a side effect.
- Distinguish exact operations from rounded operations in tests and documentation.
- Preserve `Decimal` exponent notation internally. Decide CLI fixed versus scientific notation deliberately for results that would otherwise create enormous output.
- Do not claim arbitrary precision: Decimal calculations are governed by context, operation semantics, exponent bounds, and available resources.

## Completion evidence

Run focused tests first, then the applicable project suite and baseline CLI command from `AGENTS.md`. Report exact commands, exit codes, relevant results, final diff scope, and remaining unverified numeric assumptions. A successful import or syntax check alone does not verify arithmetic behavior.
