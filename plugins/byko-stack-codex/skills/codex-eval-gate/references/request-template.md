# Codex eval request template

Use this shape for isolated evaluator requests.

```markdown
# Evaluation Request

## Meta
- id: eval-<YYYYMMDD>-<HHMMSS>
- created_at: <ISO8601>
- evaluator: codex-eval-gate
- mode: spec | plan | implementation | custom

## Neutral Context
- problem_definition: <from manifest, or "not available">
- key_decisions:
  - <decision + basis from manifest>

## Target Files
- <absolute or repo-relative path>

## Evaluation Criteria
<insert relevant checklist from checklists.md>

## Source Documents
<copy spec/plan/traceability/ledger contents where practical>

## Required Output
Return:
- verdict: APPROVED | NEEDS_REVISION | BLOCKED
- confidence: high | medium | low
- findings grouped as FAIL/WARN/PASS
- concrete file:line evidence for every FAIL
- improvement suggestions only when they satisfy the common rules
```

Subagent prompt:

```text
Use the evaluation request at <absolute request path>.
Read the target files listed in it and inspect the codebase as needed.
Evaluate according to the checklist.
Write a concise result with verdict, confidence, evidence-backed findings, and optional suggestions.
Do not assume the caller's implementation is correct.
```
