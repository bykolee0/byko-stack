# Fresh-eyes review request template

```markdown
# Review Request

## Meta
- id: review-<YYYYMMDD>-<HHMMSS>
- created_at: <ISO8601>
- reviewer: codex-review
- mode: spec | implementation | custom

## Problem Definition
<2-5 lines from manifest. This is the anchor; do not replace it with a spec summary.>

## Target Artifacts
- <path>

## Review Checklist
<insert review-checklist.md>

## Source Documents
<copy manifest/spec/plan/traceability where practical; code may be referenced by path>

## Required Output
Return:
- verdict: SOUND | CONCERNS | RETHINK | BLOCKED
- short rationale
- findings with file:line evidence
- suggested return point: codex-spec-designer, codex-spec-dev, or none
```

Subagent prompt:

```text
Use the review request at <absolute request path>.
Start from the Problem Definition before reading the proposed solution.
Inspect target artifacts and relevant codebase conventions.
Judge whether this is the right, durable solution to the original problem.
Return SOUND, CONCERNS, RETHINK, or BLOCKED with concrete evidence.
```
