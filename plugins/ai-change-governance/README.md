# AI Change Governance

A dependency-free, single-source plugin distribution for test-first protected-file changes and append-only AI change evidence.

The policy engine is vendor-neutral. One installer maps Codex and Claude Code `PreToolUse`/`PostToolUse` events and Gemini CLI `BeforeTool`/`AfterTool` events onto the same implementation. Other agent harnesses receive a documented stdin/stdout JSON configuration.

Install the same package for any supported host:

```sh
python3 scripts/install.py --tool codex --project /path/to/repository
python3 scripts/install.py --tool claude --project /path/to/repository
python3 scripts/install.py --tool gemini --project /path/to/repository
python3 scripts/install.py --tool generic --project /path/to/repository
```

The installer copies the shared engine into `.ai-governance/plugin/`, creates `.ai-governance.json` only when absent, and merges the chosen hook into the host configuration without deleting existing hooks. The installed files can be committed so every teammate receives the same policy regardless of which supported AI tool they use.

## Organizational workflow

The same installation provides three reusable roles:

- `principal-architecture-role`: defines outcomes, invariants, boundaries, decisions, and final acceptance.
- `sse-role`: implements architecture-ready work with focused tests and reviewable evidence.
- `tester-role`: independently verifies acceptance behavior or issues reproducible change requests.

Role handoffs use a vendor-neutral JSON work item managed by `.ai-governance/plugin/work_item.py`. The enforced lifecycle is `intake → architecture-ready → implementation-complete → verified → accepted`, with a `changes-requested` feedback loop. This preserves the same daily workflow when a team member switches among supported AI tools.

Run `python3 -m unittest discover -s tests -p 'test*.py' -v` from this plugin directory to validate the engine and installer.

Native enforcement depends on the host exposing synchronous command hooks. For tools without hooks, use `--tool generic` and call the generated pre/post commands from CI or a wrapper; prompt instructions alone are advisory.
