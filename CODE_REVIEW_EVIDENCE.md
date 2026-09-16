# Calculator Code Review Evidence

## Review scope

- Review type: read-only code-quality, error-handling, and functionality diagnosis
- Source reviewed: `__init__.py`, `application.py`, `commands.py`, `errors.py`, `operations.py`, and `cli.py`
- Runtime used for reproductions: Python 3.14.4
- Review date: 2026-09-15
- Exclusions: no fixes, migrations, dependency changes, or source-code modifications
- Overall assessment: **6/10**. The implementation is compact and readable, but automated coverage, input validation, decimal semantics, and CLI failure handling are incomplete.

## Evidence summary

| ID | Area | Finding | Risk | Evidence status |
| --- | --- | --- | --- | --- |
| Q1 | Code quality | No automated tests | High | Verified by repository inspection |
| Q2 | Code quality | Precision behavior is unspecified and can silently round | High | Reproduced |
| Q3 | Code quality | Registry collisions and invalid registrations are not rejected | Medium | Verified by code inspection |
| Q4 | Code quality | History is insufficient for a complete audit trail | Low/Medium | Verified by code inspection and behavior |
| E1 | Error handling | Decimal arithmetic errors escape the domain error boundary | High | Reproduced |
| E2 | Error handling | Invalid operation types leak `AttributeError` | Medium | Reproduced |
| E3 | Error handling | CLI domain errors are written to stdout | Medium | Reproduced |
| F1 | Functionality | Non-finite operands can produce successful results | High | Reproduced |
| F2 | Functionality | Operation names do not tolerate surrounding whitespace | Low | Reproduced |
| F3 | Functionality | Direct execution of `cli.py` fails | Medium | Reproduced |

## Verified baseline behavior

- `2 add 3` returns `5` and the CLI exits with status `0`.
- Operation lookup is case-insensitive.
- The registry defines `plus`, `minus`, `times`, and `x` aliases.
- Division by zero raises `DivisionByZeroError`.
- Unknown operations raise `UnknownOperationError`.
- Ordinary invalid numeric strings raise `CalculationError`.
- Failed calculations are not appended to history.
- `Calculator.history` returns a tuple, preventing direct mutation of the internal list.
- All source modules compiled successfully under Python 3.14.4 during the original review.

## Code-quality findings

### Q1 — No automated tests

**ROOT CAUSE**

The repository has no unit, integration, or CLI test suite and no test configuration.

**EVIDENCE**

Repository enumeration found only the six implementation modules and cached bytecode. No test files or test configuration were present.

**REPRO**

```sh
rg --files -g '!__pycache__'
```

Observed source files:

```text
commands.py
errors.py
cli.py
operations.py
application.py
__init__.py
```

**PROPOSED TEST**

Create automated coverage for every operation and alias, invalid operands, invalid operation keys, zero division, non-finite decimals, precision boundaries, history behavior, registry collisions, and CLI exit/output behavior.

**RISK**

**High** — regressions and edge-case failures currently have no automated detection.

### Q2 — “Precise arithmetic” is not defined or consistently met

**ROOT CAUSE**

Arithmetic runs under the process-wide `decimal` context, normally limited to 28 significant digits. Results exceeding that precision can be rounded silently.

**EVIDENCE**

- `operations.py:25-49` performs decimal arithmetic directly under the active context.
- `cli.py:16` describes the program as performing “precise arithmetic.”
- No local precision, rounding, or trap policy is defined.

**REPRO**

```python
Calculator().calculate("9999999999999999999999999999", "+", "0.1")
```

Observed result:

```text
Decimal('9999999999999999999999999999')
```

The fractional `0.1` is absent from the returned and recorded result.

**PROPOSED TEST**

Assert the agreed behavior for inputs and results exceeding 28 significant digits: an exact result, documented rounding, or an explicit precision error.

**RISK**

**High** for financial or scientific consumers; **Medium** for a teaching/demo calculator.

### Q3 — Registry integrity is not enforced

**ROOT CAUSE**

Registration writes directly to the internal dictionary. Duplicate names, symbols, and aliases silently replace existing entries. Names and operation implementations are not validated.

**EVIDENCE**

`operations.py:58-60` assigns each registration key directly to `_operations` without collision or contract checks.

**REPRO**

```python
registry = OperationRegistry.with_defaults()
registry.register("custom", custom_operation, "add")
```

By inspection, the assignment for alias `add` replaces the default addition mapping without warning.

**PROPOSED TEST**

Register duplicate names, symbols, and aliases and assert the intended collision policy. Also test empty names, missing symbols, and objects that do not implement the operation contract.

**RISK**

**Medium** — extensions can unexpectedly alter established calculations.

### Q4 — Calculation history is limited as an audit record

**ROOT CAUSE**

`CalculationRecord` stores only a rendered expression and result. Records are created only after successful execution.

**EVIDENCE**

- `commands.py:19-22` stores only `expression` and `result`.
- `application.py:25-31` appends history only after execution succeeds.
- The module description in `commands.py:1` calls these records an audit mechanism.

**REPRO**

Perform one successful calculation and then divide by zero. The successful calculation is present in history, while the failed attempt is absent.

**PROPOSED TEST**

First define whether history means successful-result history or an audit of all attempts. Then assert the required metadata and treatment of failures.

**RISK**

**Low** if this is user-facing history; **Medium** if it is expected to support auditing.

## Error-handling findings

### E1 — Decimal arithmetic errors escape the domain error model

**ROOT CAUSE**

Input conversion errors are translated to `CalculationError`, but exceptions raised during arithmetic are not translated. The CLI catches only `CalculationError`.

**EVIDENCE**

- `application.py:41-46` handles conversion errors.
- `application.py:25` executes the operation without an arithmetic-error boundary.
- `cli.py:25-29` catches only `CalculationError`.

**REPRO**

```sh
PYTHONPATH=.. python3 -B -m calculator.cli Infinity - Infinity
```

Observed behavior:

```text
exit status: 1
stderr: traceback ending in decimal.InvalidOperation
```

**PROPOSED TEST**

Exercise decimal invalid operations, configured overflow/underflow conditions, and failures from custom operations. Assert the documented public exception type, error message, CLI stream, and exit status.

**RISK**

**High** — inputs accepted by parsing can terminate the CLI with an internal traceback.

### E2 — Invalid operation types leak `AttributeError`

**ROOT CAUSE**

Operation lookup assumes its key is a string and calls `.lower()` before any validation capable of producing a domain error.

**EVIDENCE**

`operations.py:62-66` catches `KeyError`, but `key.lower()` can fail before dictionary lookup.

**REPRO**

```python
Calculator().calculate("2", None, "3")
```

Observed behavior:

```text
AttributeError: 'NoneType' object has no attribute 'lower'
```

**PROPOSED TEST**

Pass `None`, numbers, and custom objects as operation keys. Assert either a domain-specific error or a documented strict runtime contract.

**RISK**

**Medium** — the public facade exposes inconsistent failure types to callers.

### E3 — CLI domain errors are written to stdout

**ROOT CAUSE**

The CLI uses ordinary `print()` for diagnostics rather than the error stream.

**EVIDENCE**

`cli.py:27-29` prints `error: ...` without specifying `stderr`.

**REPRO**

```sh
PYTHONPATH=.. python3 -B -m calculator.cli 2 / 0
```

Observed behavior:

```text
exit status: 2
stdout: error: Cannot divide by zero
stderr: empty
```

**PROPOSED TEST**

Capture both streams and assert that successful results use stdout while diagnostics use stderr.

**RISK**

**Medium** — shell pipelines can mistake diagnostic text for a valid result unless they also inspect the exit status.

## Functionality findings

### F1 — Non-finite operands are accepted as successful calculations

**ROOT CAUSE**

`Decimal` accepts textual `NaN`, `sNaN`, and infinity values. Conversion checks only whether construction succeeds and does not require finite operands or results.

**EVIDENCE**

`application.py:42-46` performs conversion without an `is_finite()` validation or a documented non-finite-number policy.

**REPRO**

```python
calculator = Calculator()
calculator.calculate("NaN", "+", "3")
```

Observed behavior:

```text
result: Decimal('NaN')
history: CalculationRecord(expression='NaN + 3', result=Decimal('NaN'))
```

Other non-finite combinations can trigger the uncaught exception described in E1.

**PROPOSED TEST**

Cover `NaN`, `sNaN`, `Infinity`, and `-Infinity` as both operands for every operation. Assert whether they are rejected or supported consistently.

**RISK**

**High** — undefined values can be returned and stored as successful results.

### F2 — Operation whitespace is not normalized

**ROOT CAUSE**

Operation lookup lowercases keys but does not trim surrounding whitespace.

**EVIDENCE**

`operations.py:64` uses `key.lower()` directly.

**REPRO**

```text
operation "PLUS"  -> succeeds
operation " add " -> UnknownOperationError
```

**PROPOSED TEST**

Test leading and trailing whitespace for operation names, aliases, and symbols according to the intended input policy.

**RISK**

**Low** — interactive or externally sourced inputs can fail unexpectedly.

### F3 — Direct script execution fails

**ROOT CAUSE**

`cli.py` contains a `__main__` entry block but uses package-relative imports, so executing the file directly lacks the required package context.

**EVIDENCE**

- `cli.py:6-7` uses relative imports.
- `cli.py:33-34` executes `main()` when the file is run as a script.
- No packaging metadata or usage documentation defines the supported invocation.

**REPRO**

```sh
python3 -B cli.py 2 add 3
```

Observed behavior:

```text
exit status: 1
ImportError: attempted relative import with no known parent package
```

Package execution succeeds when the parent directory is importable:

```sh
PYTHONPATH=.. python3 -B -m calculator.cli 2 add 3
```

**PROPOSED TEST**

Define the supported launch mechanism and exercise it in a subprocess from a clean environment. If direct execution is intended, test that path independently.

**RISK**

**Medium** — the obvious direct invocation fails and no documented startup contract exists.

## Review limitations

- No product specification defines accepted numeric domains, precision requirements, whitespace policy, audit requirements, or supported CLI launch method. Findings involving these behaviors identify observable ambiguity or inconsistency rather than asserting an unstated business rule.
- No independent reviewer or automated suite corroborated this self-review.
- No concurrency, performance, or platform matrix testing was performed because the implementation and stated review scope did not establish those as requirements.
- Proposed tests are recommendations, not executed evidence.

## Reproduction environment note

Behavioral checks used `PYTHONDONTWRITEBYTECODE=1` and `python3 -B` where applicable. Temporary stream-capture files were created outside the repository and removed. No migrations or source-code changes were performed during the diagnosis.
