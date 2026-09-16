# Organizational role workflow

The workflow separates direction, implementation, and verification without assuming that separate humans or agents are always available.

```text
intake
  -> architecture-ready          principal-architecture-role
  -> implementation-complete     sse-role
  -> verified                    tester-role
  -> accepted                    principal-architecture-role

implementation-complete
  -> changes-requested           tester-role
  -> implementation-complete     sse-role
```

## Work-item contract

The JSON work item is the durable handoff record. It contains the outcome, acceptance criteria, constraints, assumptions, decisions, status, and append-only handoff evidence. Store work items in a team-selected repository directory such as `work-items/`.

Create one:

```sh
python3 .ai-governance/plugin/work_item.py new \
  --file work-items/CALC-123.json \
  --id CALC-123 \
  --title "Add percentage calculation" \
  --outcome "Users calculate percentages without manual conversion" \
  --criterion "The public API returns an exact Decimal result"
```

Transition it:

```sh
python3 .ai-governance/plugin/work_item.py transition \
  --file work-items/CALC-123.json \
  --to architecture-ready \
  --role principal-architecture-role \
  --summary "Contract and compatibility boundaries agreed"
```

Implementation, verification, change requests, and final acceptance require `--evidence`. Evidence should identify actual commands, results, or reviewable artifacts rather than conclusions alone.

## Operating rules

- One person or agent may perform multiple roles when staffing requires it, but must explicitly disclose that verification is not independent.
- Role transitions do not grant external mutation, merge, release, deployment, or production access.
- The work-item record complements repository issues and pull requests; it does not require replacing them.
- Hooks enforce protected-file tests and change tracking. Role skills guide judgment and handoff quality.
