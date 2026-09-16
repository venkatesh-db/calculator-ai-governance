# Calculator Agent Instructions

These instructions apply to this directory and all descendants.

## Project purpose

This repository contains a small, extensible Python calculator package. Preserve its simple architecture while making arithmetic behavior, public errors, CLI behavior, and calculation history explicit and testable.

The user is the final decision-maker for requirements and architectural tradeoffs. Do not treat assumptions about precision, accepted numeric values, history semantics, or CLI invocation as settled requirements.


## Agent write policy

- Codex agents may inspect, create, edit, rename, and move project files when required by the user’s task.
- Codex agents may run tests, formatters, and other validation commands that create ordinary development artifacts.
- Preserve unrelated user changes and keep edits focused on the requested outcome.
- Do not delete files or perform destructive operations unless explicitly authorized.
- Do not install dependencies, commit, push, publish, release, deploy, or modify external systems unless explicitly authorized.


## Repository map

- `application.py`: public `Calculator` facade, input conversion, execution, and history ownership
- `operations.py`: arithmetic strategies and operation registry
- `commands.py`: calculation command and history record value objects
- `errors.py`: public domain exception hierarchy
- `cli.py`: command-line adapter and result formatting
- `test_calculator.py`: behavior-level public API and CLI regression tests
- `__init__.py`: package exports
- `.codex/skills/calculator-engineering/`: reusable Codex guidance for extending and validating ordinary and precision-sensitive calculator behavior
- `.codex/hooks.json`: project hook configuration enforcing pre-edit CLI tests and post-edit change auditing
- `.codex/hooks/cli_test_gate.py`: focused unittest evidence recorder and pre-edit hook for `cli.py`
- `.codex/hooks/post_change_audit.py`: post-edit code-change evidence and ledger-verification hook
- `.codex/AI_CHANGELOG.jsonl`: append-only machine-readable evidence for AI code changes and ledger verification
- `plugins/ai-change-governance/`: reusable, vendor-neutral test-first gate and AI change-audit plugin with Codex, Claude Code, Gemini CLI, and generic adapters
- `CODE_REVIEW_EVIDENCE.md`: evidence from the initial code-quality and behavior review

Keep these responsibilities distinct. Domain behavior belongs in the package, while argument parsing, presentation, streams, and process exit codes belong in the CLI adapter.

## Mandatory `cli.py` test-first gate

Before modifying `cli.py`, agents must establish the requirement-specific behavior through a focused test:

1. State the requested CLI behavior and identify its observable stdout, stderr, exit-code, parsing, or formatting contract.
2. Add or update the focused behavior-level test without editing `cli.py`.
3. Run the test through the gate, replacing the requirement and unittest selector with the current task:

   ```sh
   python3 -B .codex/hooks/cli_test_gate.py authorize \
     --requirement "<requested CLI behavior>" \
     --test "calculator.test_calculator.<TestClass>.<test_method>"
   ```

4. The gate accepts a passing test for preserved behavior or an assertion-only failing test for new/fixed behavior. Import errors, setup errors, missing tests, and unfocused suite commands do not authorize an edit.
5. Only after authorization may `cli.py` be modified. Authorization expires after one hour and becomes invalid immediately when `cli.py` or any test file changes.
6. After editing, rerun the focused test, relevant neighboring tests, and the applicable suite. A pre-edit red test is not completion evidence.

Do not bypass, disable, weaken, or fabricate evidence for this gate. If a CLI requirement cannot be expressed as a deterministic test, stop and obtain direction before editing `cli.py`.

## AI change evidence

The `PostToolUse` hook records every AI-driven source, test, script, executable configuration, and skill-instruction change in `.codex/AI_CHANGELOG.jsonl`. Each code-change event contains the tool name, UTC timestamp, path, change type, resulting existence state, SHA-256 hash when present, and ledger status.

- Update `AGENTS.md` in the same tool call as code whenever practical; this produces `verified_same_tool` evidence.
- If a code change lacks a fresh ledger row, the hook records it as `pending` and tells the agent which paths require entries.
- A later `AGENTS.md` change resolves pending evidence only when the matching path's ledger-entry count increases; the hook appends a separate `ledger_verified` event and never rewrites earlier evidence.
- Do not edit, truncate, reorder, or delete existing `.codex/AI_CHANGELOG.jsonl` records. The audit hook is the sole writer except when bootstrapping the file itself.
- The evidence log is excluded from auditing itself to prevent recursion.

## Codebase change tracking

`AGENTS.md` is the authoritative inventory and change ledger for code files in this project. Every change that adds, modifies, renames, moves, or deletes a code file must update this section in the same change. A code file is any source, test, script, build, or executable configuration file that affects application behavior or validation.

Agents must:

- Add every new code file to the current inventory with a concise description of its responsibility.
- Update an existing inventory entry when a code file's responsibility changes.
- Remove a renamed, moved, or deleted code file from the current inventory, add its replacement when applicable, and preserve the event in the change ledger.
- Append one change-ledger entry for every added, modified, renamed, moved, or deleted code file. Never rewrite or remove earlier ledger entries merely because a file was later changed or deleted.
- Record the date, change type, file path, and a concise reason or behavioral summary. Use ISO `YYYY-MM-DD` dates and the change types `ADDED`, `MODIFIED`, `RENAMED`, `MOVED`, or `DELETED`.
- Verify before completion that the inventory matches the code files present in the working tree and that all code-file changes in the final diff have ledger entries.

Documentation-only changes do not require ledger entries unless they add, modify, rename, move, or delete a code file. Changes to this tracking policy itself should be recorded in the policy history below rather than in the code-file ledger.

### Current code-file inventory

- `__init__.py`: calculator package exports
- `application.py`: public `Calculator` facade, input conversion, execution, and history ownership
- `cli.py`: command-line adapter, result formatting, streams, and process exit behavior
- `commands.py`: calculation command and history record value objects
- `errors.py`: public domain exception hierarchy
- `operations.py`: arithmetic strategies and operation registry
- `test_calculator.py`: public API and CLI behavior-level tests
- `.codex/skills/calculator-engineering/SKILL.md`: reusable calculator implementation workflow and routing for ordinary versus precision-sensitive work
- `.codex/skills/calculator-engineering/agents/openai.yaml`: skill discovery metadata and default invocation prompt
- `.codex/skills/calculator-engineering/references/numeric-contracts.md`: precision, rounding, magnitude, non-finite-value, and resource-contract guidance
- `.codex/skills/calculator-engineering/references/validation-matrix.md`: reusable behavioral and compatibility test coverage guide
- `.codex/hooks.json`: Codex `PreToolUse` CLI gate and `PostToolUse` AI change-audit registrations
- `.codex/hooks/cli_test_gate.py`: test execution, evidence hashing, expiry, and pre-edit authorization logic
- `.codex/hooks/post_change_audit.py`: `PostToolUse` change detection, evidence hashing, and ledger reconciliation
- `.codex/AI_CHANGELOG.jsonl`: append-only AI change and ledger-verification evidence
- `plugins/ai-change-governance/.codex-plugin/plugin.json`: Codex plugin manifest and discovery metadata
- `plugins/ai-change-governance/hooks/hooks.json`: Codex lifecycle adapter for the portable governance engine
- `plugins/ai-change-governance/scripts/governance_hook.py`: provider-neutral protected-file authorization and append-only ledger-audit engine
- `plugins/ai-change-governance/scripts/install.py`: idempotent cross-tool project installer and hook-config merger
- `plugins/ai-change-governance/scripts/work_item.py`: deterministic role-authorized work-item and evidence-handoff state machine
- `plugins/ai-change-governance/tests/test_governance_hook.py`: isolated behavior tests for authorization, denial, evidence, and Gemini translation
- `plugins/ai-change-governance/tests/test_installer.py`: isolated cross-host installation, preservation, and idempotency tests
- `plugins/ai-change-governance/tests/test_role_workflow.py`: role-transition, evidence, packaging, and authorization tests
- `plugins/ai-change-governance/skills/change-governance/SKILL.md`: reusable workflow for installing and operating governance safeguards
- `plugins/ai-change-governance/skills/change-governance/agents/openai.yaml`: skill discovery metadata and invocation prompt
- `plugins/ai-change-governance/skills/change-governance/references/provider-adapters.md`: Codex, Claude Code, Gemini CLI, and generic integration guidance
- `plugins/ai-change-governance/adapters/claude-code/settings.fragment.json`: Claude Code project-hook configuration example
- `plugins/ai-change-governance/adapters/gemini-cli/settings.fragment.json`: Gemini CLI project-hook configuration example
- `plugins/ai-change-governance/examples/policy.json`: portable project policy template
- `plugins/ai-change-governance/portable-plugin.json`: vendor-neutral package identity, runtime, supported hosts, and capabilities
- `plugins/ai-change-governance/workflow/role-workflow.json`: machine-readable organizational roles, transitions, and evidence requirements
- `plugins/ai-change-governance/skills/principal-architecture-role/SKILL.md`: architecture framing, decision, handoff, and final-acceptance guidance
- `plugins/ai-change-governance/skills/principal-architecture-role/agents/openai.yaml`: principal-architecture skill discovery metadata
- `plugins/ai-change-governance/skills/sse-role/SKILL.md`: senior-engineering implementation, validation, and tester-handoff guidance
- `plugins/ai-change-governance/skills/sse-role/agents/openai.yaml`: SSE skill discovery metadata
- `plugins/ai-change-governance/skills/tester-role/SKILL.md`: independent behavioral verification and change-request guidance
- `plugins/ai-change-governance/skills/tester-role/agents/openai.yaml`: tester skill discovery metadata
- `plugins/ai-change-governance/skills/references/organizational-workflow.md`: shared role lifecycle, work-item contract, commands, and operating boundaries

### Code-file change ledger

The ledger begins when this policy was introduced. Existing files are represented by the inventory; do not invent historical changes that were not observed.

| Date | Change type | File | Reason or behavioral summary |
| --- | --- | --- | --- |
| 2026-09-16 | ADDED | `.codex/skills/calculator-engineering/SKILL.md` | Added a reusable workflow for implementing and validating simple and precision-sensitive calculator changes. |
| 2026-09-16 | ADDED | `.codex/skills/calculator-engineering/agents/openai.yaml` | Added skill discovery metadata and a reusable invocation prompt. |
| 2026-09-16 | ADDED | `.codex/skills/calculator-engineering/references/numeric-contracts.md` | Added decision guidance for precision, rounding, extreme magnitude, special values, and computational limits. |
| 2026-09-16 | ADDED | `.codex/skills/calculator-engineering/references/validation-matrix.md` | Added a reusable behavior-level validation matrix for calculator changes. |
| 2026-09-16 | MODIFIED | `__init__.py` | Exported the new public invalid-operand domain error and corrected the export list. |
| 2026-09-16 | MODIFIED | `application.py` | Added the public unary square-root facade and success-only history recording. |
| 2026-09-16 | MODIFIED | `cli.py` | Added `sqrt VALUE` dispatch while preserving binary invocation and routing domain diagnostics to stderr. |
| 2026-09-16 | MODIFIED | `commands.py` | Added an immutable unary calculation command. |
| 2026-09-16 | MODIFIED | `errors.py` | Added a public invalid-operand error for operation-domain failures. |
| 2026-09-16 | MODIFIED | `operations.py` | Added the unary operation contract and context-aware square-root strategy. |
| 2026-09-16 | ADDED | `test_calculator.py` | Added square-root API, numeric-context, failure, history, and CLI regression coverage. |
| 2026-09-16 | ADDED | `.codex/hooks.json` | Registered a project `PreToolUse` hook that guards changes to `cli.py`. |
| 2026-09-16 | ADDED | `.codex/hooks/cli_test_gate.py` | Added a test-first authorization gate using focused unittest results and source hashes. |
| 2026-09-16 | MODIFIED | `test_calculator.py` | Added focused coverage for explicit argument parsing through `build_parser(argv)`. |
| 2026-09-16 | MODIFIED | `cli.py` | Changed `build_parser(argv=None)` to parse an optional argument sequence directly while preserving normal process invocation. |
| 2026-09-16 | MODIFIED | `.codex/hooks.json` | Registered post-tool auditing for AI-driven code-file changes. |
| 2026-09-16 | ADDED | `.codex/hooks/post_change_audit.py` | Added append-only change evidence and fresh-ledger verification after code edits. |
| 2026-09-16 | ADDED | `.codex/AI_CHANGELOG.jsonl` | Added the machine-readable append-only AI change evidence log. |
| 2026-09-16 | MODIFIED | `.codex/hooks/post_change_audit.py` | Extended evidence detection to common shell-based code-file mutations. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/.codex-plugin/plugin.json` | Added reusable plugin identity, capabilities, and discovery metadata. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/hooks/hooks.json` | Added the Codex lifecycle adapter for portable pre-change gates and post-change auditing. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/scripts/governance_hook.py` | Added the dependency-free provider-neutral policy engine, authorization evidence, hash audit, and ledger reconciliation. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/tests/test_governance_hook.py` | Added isolated regression tests for gate decisions, authorization, audit evidence, and Gemini output. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/skills/change-governance/SKILL.md` | Added reusable governance setup and operating guidance. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/skills/change-governance/agents/openai.yaml` | Added skill discovery metadata and default prompt. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/skills/change-governance/references/provider-adapters.md` | Documented adapter behavior for Codex, Claude Code, Gemini CLI, and custom harnesses. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/adapters/claude-code/settings.fragment.json` | Added a mergeable Claude Code hook configuration example. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/adapters/gemini-cli/settings.fragment.json` | Added a mergeable Gemini CLI hook configuration example. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/examples/policy.json` | Added a configurable protected-file and audit-policy template. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/scripts/governance_hook.py` | Added portable detection of common shell-based file mutations. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/tests/test_governance_hook.py` | Added regression coverage for protected-file mutation through a shell command. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/portable-plugin.json` | Added the vendor-neutral package manifest and supported-host capability contract. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/scripts/install.py` | Added one idempotent installer that preserves existing hooks and targets Codex, Claude Code, Gemini CLI, or a generic harness. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/tests/test_installer.py` | Added isolated validation that one package installs across all supported hosts without overwriting policy or existing hooks. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/skills/change-governance/SKILL.md` | Changed adoption guidance to the single cross-tool installer workflow. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/skills/change-governance/references/provider-adapters.md` | Documented installer-driven host selection and generic integration. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/.codex-plugin/plugin.json` | Updated the plugin release metadata for the single-source cross-tool installer. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/workflow/role-workflow.json` | Added the machine-readable architecture, SSE, tester, feedback-loop, and evidence transition contract. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/scripts/work_item.py` | Added deterministic work-item creation and role-authorized evidence handoffs. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/skills/principal-architecture-role/SKILL.md` | Added reusable architecture framing, decision, handoff, and final acceptance behavior. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/skills/principal-architecture-role/agents/openai.yaml` | Added principal-architecture role discovery metadata. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/skills/sse-role/SKILL.md` | Added reusable senior-engineering implementation and tester-handoff behavior. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/skills/sse-role/agents/openai.yaml` | Added SSE role discovery metadata. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/skills/tester-role/SKILL.md` | Added reusable independent verification and change-request behavior. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/skills/tester-role/agents/openai.yaml` | Added tester role discovery metadata. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/tests/test_role_workflow.py` | Added role lifecycle, authorization, evidence, and skill-packaging regression coverage. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/scripts/install.py` | Installed the work-item engine, workflow contract, and role skills into each host's discovery directory. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/tests/test_installer.py` | Verified that every supported host receives all organizational role skills and workflow tooling. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/portable-plugin.json` | Declared the organizational role and evidence-handoff capabilities in release 0.3.0. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/.codex-plugin/plugin.json` | Declared architecture, engineering, and testing capabilities in release 0.3.0. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/skills/principal-architecture-role/SKILL.md` | Corrected installed workflow-tool and shared-reference paths. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/skills/sse-role/SKILL.md` | Corrected installed workflow-tool and shared-reference paths. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/skills/tester-role/SKILL.md` | Corrected installed workflow-tool and shared-reference paths. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/scripts/install.py` | Installed the shared organizational workflow reference alongside all role skills. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/tests/test_installer.py` | Verified each host installation includes the shared role-workflow reference. |
| 2026-09-16 | ADDED | `plugins/ai-change-governance/skills/references/organizational-workflow.md` | Added the shared architecture-to-acceptance workflow, feedback loop, work-item examples, and role boundaries. |
| 2026-09-16 | MODIFIED | `plugins/ai-change-governance/skills/change-governance/SKILL.md` | Routed governance users to the principal architecture, SSE, and tester role workflow. |

### Tracking-policy history

| Date | Change | Reason |
| --- | --- | --- |
| 2026-09-16 | Added the code-file inventory and append-only change-ledger requirement. | Ensure future code additions, modifications, renames, moves, and deletions remain explicitly tracked in `AGENTS.md`. |

## Business and compatibility invariants

- Addition, subtraction, multiplication, and division must operate on `Decimal` values.
- The default operation names and symbols are `add`/`+`, `subtract`/`-`, `multiply`/`*`, and `divide`/`/`.
- Square root is exposed as `Calculator.square_root(value)` and the CLI form `sqrt VALUE`.
- Square root accepts finite, non-negative Decimal values including signed zero, uses the active Decimal precision and rounding mode without mutating the caller's context, and rejects negative or non-finite operands through `InvalidOperandError`.
- `build_parser(argv=None)` returns parsed arguments; an explicit sequence supports direct callers and omission preserves parsing from the process command line.
- Existing aliases `plus`, `minus`, `times`, and `x` are public behavior unless the user explicitly approves a breaking change.
- Division by numeric zero, including signed zero, must not return a result.
- Unknown operations must fail through the calculator's public domain-error contract.
- A failed calculation must not appear as a successful history record.
- Callers must not receive a directly mutable reference to the calculator's internal history list.
- Do not silently change decimal precision, rounding, non-finite-number support, registry collision behavior, or audit semantics. These are product decisions; present the options and obtain direction when the requested task depends on them.

## Error-handling contract

- Use `CalculationError` as the public base for expected calculator-domain failures.
- Use the existing specialized exceptions when their meanings apply.
- Do not expose raw implementation exceptions to CLI users for expected invalid input or arithmetic failures.
- Do not catch `Exception` broadly unless the boundary and translation policy are explicitly justified. Programming defects and unrelated system failures must remain distinguishable from expected calculation errors.
- Successful CLI results belong on stdout. User-facing diagnostics belong on stderr and require a nonzero exit status.
- Preserve exception chaining when translating a lower-level failure into a domain error.

## Decimal behavior

- Construct operands without passing through binary floating-point arithmetic. The current `Decimal(str(value))` approach intentionally avoids direct `Decimal(float)` conversion artifacts.
- Treat precision and rounding as externally visible behavior. If a task changes either, document the selected context and add boundary tests.
- Explicitly decide and test the treatment of `NaN`, signaling NaN, positive infinity, and negative infinity before changing their behavior.
- Test zero as `0`, `-0`, and equivalent decimal forms whenever division behavior changes.

## Operation registry

- Preserve case-insensitive operation lookup unless a requirement says otherwise.
- Treat names, symbols, and aliases as one shared key namespace.
- Any change to registration must define duplicate-key behavior and validate the operation contract.
- Avoid adding a new abstraction layer merely to add one operation. Implement the smallest strategy and register it consistently with the existing design.

## Working method

1. State the requested observable outcome, scope, assumptions, and completion checks.
2. Inspect the affected public entry point, implementation, error path, and relevant tests together.
3. For a bug, reproduce the failure when feasible before editing and distinguish confirmed cause from hypothesis.
4. Choose and implement the smallest cohesive change.
5. Add or update behavior-level tests for changed contracts and regression cases.
6. Run appropriate validation checks and report their actual results.




## Validation

Use the following command for baseline CLI validation:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. python3 -B -m calculator.cli 2 add 3
```

Expected baseline output:

```text
5
```

When a test suite exists, discover and use its documented command. Until then, do not claim that behavioral validation is comprehensive. At minimum, changes affecting calculator behavior should cover:

- Four default operations and every alias
- Square root for exact, fractional, context-rounded, signed-zero, large-magnitude, negative, and non-finite operands
- Positive, negative, zero, fractional, and large operands
- Invalid numeric input and unknown operations
- Division by positive and negative zero
- Decimal precision boundaries and the selected rounding policy
- The selected non-finite-number policy
- Successful and failed history behavior
- Registry collision and invalid-registration behavior
- CLI stdout, stderr, formatting, and exit codes
- The documented package invocation method

Do not weaken assertions or normalize unexpected failures merely to make checks pass. Syntax or import success is not evidence that calculator behavior is correct.

## Change constraints

- Do not add dependencies unless a concrete requirement justifies them.
- Do not introduce databases, migrations, services, networking, or concurrency infrastructure for this local calculator without an explicit requirement.
- Do not change package exports or public exception types casually.
- Do not commit, push, publish, deploy, or send external messages unless explicitly authorized.
- Do not modify `CODE_REVIEW_EVIDENCE.md` to imply a proposed test was executed. Add new observed evidence only after running the stated check against the relevant code version.

## Completion report

Lead with the delivered behavior. Summarize files changed, important decisions, validation commands with observed results, and remaining risks or unverified assumptions. Never claim independent review, production verification, or deployment unless it occurred.
