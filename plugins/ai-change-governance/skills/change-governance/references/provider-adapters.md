# Provider adapters

The distribution has one installer and one core engine. The core reads one JSON object from stdin and emits one JSON object to stdout. Run hooks from the repository root so they discover `.ai-governance.json`.

## Codex

Run `python3 scripts/install.py --tool codex --project <repository>`. This merges the hook into `.codex/hooks.json`. Review and trust the hook definition in Codex before relying on it.

## Claude Code

Run `python3 scripts/install.py --tool claude --project <repository>`. This merges the hook into `.claude/settings.json`. Claude's events are `PreToolUse` and `PostToolUse`.

## Gemini CLI

Run `python3 scripts/install.py --tool gemini --project <repository>`. This merges the hook into `.gemini/settings.json`. Gemini's equivalent events are `BeforeTool` and `AfterTool`; stdout must remain valid JSON.

## Other agent harnesses

Run `python3 scripts/install.py --tool generic --project <repository>`, then invoke the `pre` and `post` commands written to `.ai-governance/hooks.json`.

The underlying form is:

```sh
python3 /path/to/governance_hook.py hook --provider generic --event pre
python3 /path/to/governance_hook.py hook --provider generic --event post
```

Provide `cwd`, `tool_name`, and `tool_input` in stdin JSON. For edits, include a `file_path`/`path` field or an apply-patch-style `*** Add|Update|Delete|Move File:` marker. A pre-hook denial uses the common `hookSpecificOutput.permissionDecision` shape; a post hook returns additional context when ledger work remains.

## Authorization

The command after `--` is executed directly without a shell:

```sh
python3 /path/to/governance_hook.py authorize \
  --file cli.py \
  --requirement "Describe the observable behavior" \
  -- python3 -B -m unittest -v package.tests.CliTests.test_behavior
```
