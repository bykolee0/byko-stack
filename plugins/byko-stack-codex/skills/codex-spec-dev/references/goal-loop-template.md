# Codex implementation loop template

Use this for long or resumable implementations. The main Codex session remains the orchestrator; durable state lives in files.

## progress.md

```markdown
# Implementation Progress

> manifest: manifest.md
> spec: spec.md
> plan: implementation-plan.md
> traceability: traceability.md
> last_updated: YYYY-MM-DD HH:MM

## Overall Status
- status: in_progress
- AC complete: 0/M
- current round: 1

## AC Tracking
| AC ID | Implementation | Verification | Status | Notes |
|-------|----------------|--------------|--------|-------|
| AC-1 | pending | pending | pending | |
| AC-2 | pending | pending | pending | |

## Round Log
### Round 1 - YYYY-MM-DD HH:MM
- selected ACs:
- files touched:
- tests run:
- result:

## Decisions and Assumptions
- [assumed] ...

## Issues
- [bounce-back] ...
- [blocked] ...
```

## implementation-plan.md

```markdown
# Implementation Plan

## Inputs
- manifest: manifest.md
- spec/source requirements: spec.md

## Strategy
<direct | staged | subagent-loop>

## Steps
| Step | ACs | Files/Modules | Owner | Verification | Status |
|------|-----|---------------|-------|--------------|--------|
| 1 | AC-1 | src/... | main | npm test ... | pending |

## Dependency Notes
- ...

## Risk Notes
- ...
```

## traceability.md

```markdown
# Traceability

| AC ID | AC | Implementation Step | Files | Verification | Status |
|-------|----|---------------------|-------|--------------|--------|
| AC-1 | ... | Step 1 | src/... | ... | pending |
```

## goal-loop-prompt.md

```markdown
You are Codex continuing a spec/requirements-based implementation.

Read first:
- manifest.md
- progress.md
- traceability.md
- implementation-plan.md
- spec.md or the source requirements listed in the manifest

Loop:
1. Identify incomplete ACs and blockers.
2. Select the next unblocked AC or implementation slice.
3. Re-read related code and local conventions before editing.
4. Implement the smallest coherent slice.
5. Run focused verification for the touched ACs.
6. Re-run affected previous verification when there is shared behavior.
7. Update progress.md, traceability.md, and manifest.md.
8. Stop and record bounce-back if requirements, data model, public API, migration, security, or AC meaning is unclear.

Rules:
- Do not revert user or other-agent changes.
- Tests should assert AC behavior, not mirror implementation internals.
- Keep scope inside the spec/problem definition.
- If using subagents, assign disjoint file/module ownership and verify their diffs before accepting them.
- Do not call the work complete until every AC is implemented and verified or explicitly blocked.

Final report:
- changed files
- AC verification summary
- tests/commands run
- unresolved assumptions or blockers
- next eval/review command
```

## Subagent round pattern

Use only when current Codex policy permits subagents.

1. Main session chooses unblocked slices with disjoint write ownership.
2. Each worker receives:
   - manifest path
   - owned files/modules
   - AC IDs
   - verification command
   - warning not to revert others' edits
3. Main session continues non-overlapping work.
4. Main session reviews each diff and AC evidence.
5. Main session updates `progress.md`, `traceability.md`, and `manifest.md`.

Every 3 rounds, run broader tests if feasible and summarize direction, remaining ACs, risks, and next slices in `progress.md`.
