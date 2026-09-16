---
name: change-governance
description: Add or operate portable test-first protected-file gates and append-only AI change-ledger auditing for Codex, Claude Code, Gemini CLI, or another command-hook agent.
---

# Change Governance

Use this skill when a project needs repeatable safeguards around AI-authored code changes.

## Workflow

1. Inspect the repository instructions, test command, code-file inventory, and the AI tool that will invoke hooks.
2. Run `python3 scripts/install.py --tool <codex|claude|gemini|generic> --project <repository>`. Use the same plugin directory for every host; do not fork the policy engine by vendor.
3. Adapt the installed `.ai-governance.json` protected paths, watched test globs, audited suffixes, and evidence paths. Keep policy decisions in the shared engine. Read [provider adapters](references/provider-adapters.md) for host-specific lifecycle details.
4. Before changing a protected file, establish focused test evidence with `authorize`. A passing preservation test or a configured assertion-only red test may authorize the edit; setup and infrastructure failures must not.
5. Make source and ledger changes together when practical. Never edit or truncate the append-only evidence file manually.
6. Run the plugin tests and the target repository's own acceptance checks.

## Organizational roles

Use `$principal-architecture-role` to frame and accept work, `$sse-role` to implement architecture-ready work, and `$tester-role` to verify behavior or request changes. For coordinated work, maintain the vendor-neutral JSON handoff with `.ai-governance/plugin/work_item.py`; the host-specific skill directories are installation details, not separate workflows.

## Boundaries

- A missing policy file means the reusable hook is inactive and returns an allow/no-op response.
- Hook guards are defense in depth, not a security sandbox or complete enforcement boundary.
- Do not install provider adapters or alter user-level settings without explicit authorization.
- Do not weaken test or ledger requirements merely to permit a change.
- Keep secrets and full source contents out of evidence logs; record paths, change types, existence, and hashes.
