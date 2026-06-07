# Codex evaluator checklists

## Common rules

Evaluate in an isolated context. Do not use the main session's confidence, conclusions, or progress report as evidence. Read the target artifacts and inspect the codebase directly.

Before writing any FAIL, reread the exact file/code evidence. Findings without concrete evidence are WARN at most.

Improvement suggestions are optional. Include one only when it improves completeness, correctness, or safety, stays inside the requested scope, and has concrete evidence. Do not suggest style preferences or scope expansion.

## mode: spec

### Implementation readiness
- Can an implementer start without more questions?
- Is the implementation direction specific enough to avoid competing interpretations?

### AC quality
- Are all ACs observable and testable?
- Does every AC include a verification method?
- Are ACs mutually consistent?

### Requirement completeness
- Are error, empty, boundary, and exceptional cases covered where relevant?
- Are concurrency, authorization, migration, and operational concerns covered where relevant?

### Codebase consistency
- Verify codebase claims with `rg`/file reads.
- Search nearby modules and caller/callee paths for missing impact.
- Check that referenced APIs, data shapes, and tests exist and match current code.
- Identify copied assumptions that are not backed by code or docs.

### Ambiguity
- Ledger `blocking` items must be zero.
- `assumed` items must not be presented as confirmed facts.
- `[TBD]` items must not affect implementation direction, public API, data model, security, or AC meaning.

## mode: plan

### AC coverage
- Every AC maps to at least one implementation step.
- Traceability, if present, has no empty critical cells.

### Ordering and ownership
- Dependencies are ordered correctly.
- Parallelizable work is identified only when file/module ownership is disjoint.
- No circular or hidden dependency is introduced.

### Verification
- Each step has a verification method.
- Tests are based on spec behavior, not on implementation details alone.

### Codebase consistency
- Planned files exist or their creation is justified.
- Search caller/callee paths for omitted related files.
- Check API names, signatures, data structures, and dependencies against real code.

## mode: implementation

### Spec compliance
- Every AC is implemented.
- The implementation does not add unrelated behavior.
- Spec constraints and non-goals are respected.

### Tests and verification
- ACs have automated tests or explicit manual/static verification.
- Tests assert user-visible or contract behavior rather than mirroring internals.
- Relevant existing tests pass, or failures are explained with evidence.

### Code quality
- Read changed files and nearby patterns.
- Check error handling, null/empty/boundary behavior, state transitions, and rollback paths.
- Check security-sensitive assumptions, data exposure, and injection surfaces.
- Look for dead code, duplicated branches, incorrect identifiers, or type assertions that hide real mismatches.

### Operations
- Required migrations/backfills/logging/observability are present.
- Rollback/fallback requirements are handled where relevant.

## mode: custom

Use the evaluation criteria provided by the caller. If criteria are missing, return `BLOCKED` and ask the caller to define them.
