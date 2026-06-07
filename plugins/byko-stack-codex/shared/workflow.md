# byko-stack-codex workflow convention

All byko-stack-codex skills follow this document when triggered.

## Main session as orchestrator

The main Codex session owns conversation, decisions, tool orchestration, final integration, and user reporting. Keep large analysis, independent evaluation, and parallel implementation in isolated contexts when current tool policy allows it.

| Work | Preferred owner |
|------|-----------------|
| User conversation and final decisions | main session |
| Small checks over 1-2 files | main session |
| Broad codebase exploration | isolated explorer subagent, or file-backed local analysis if subagents are unavailable |
| Consistency evaluation for spec/plan/implementation | isolated evaluator subagent |
| Fresh-eyes problem review | isolated reviewer subagent |
| Independent implementation slices | worker subagents with disjoint file ownership |

Subagent rules:

1. Exchange through files. Save detailed output under `analysis/`, `eval-results/`, `review-results/`, or progress files. Keep only decisions and short summaries in the main context.
2. Inject minimal neutral context: problem definition, key decisions from the manifest, target paths, and output path. Do not leak expected conclusions to evaluator or reviewer agents.
3. Spawn only when the active Codex tool policy permits it. If multi-agent tools are not loaded, use `tool_search` to discover them. If policy blocks delegation, continue with scoped local work where safe, or mark eval/review as `BLOCKED` rather than pretending it was independent.
4. Never trust subagent findings blindly. The main session rechecks concrete FAIL/CONCERN evidence before accepting, rejecting, or routing follow-up.

## Work manifest

Each work unit should have a `manifest.md` as the shared interface between skills. Do not hard-code a single required spec filename as the workflow contract.

Default location: `docs/specs/<project-name>/manifest.md`.

Target resolution order:

1. Use an explicit user path first. It may be a manifest, spec, plan, result file, or changed path.
2. If no path is given, search `docs/specs/*/manifest.md`. Use the only match; if there are several, present the most relevant/recent candidates and ask the user to choose.
3. If no manifest exists, artifact-producing skills create one. Evaluation/review skills may run from explicit paths and update a manifest only if one can be found or safely created next to the target.

Template:

```markdown
# Work Manifest: <project-name>

> work_dir: docs/specs/<project-name>/
> last_updated: YYYY-MM-DD HH:MM (<skill-name>)

## Problem Definition
<2-5 lines describing the original problem before the spec solution. Review uses this as its anchor.>

## Artifacts
| Artifact | Path | Status |
|----------|------|--------|
| spec | spec.md | draft |
| ambiguity ledger | ambiguity-ledger.md | blocking 0 / assumed N / open N |
| code analysis | analysis/ | partial |
| implementation plan | implementation-plan.md | - |
| traceability | traceability.md | - |
| progress | progress.md | - |
| eval results | eval-results/ | - |
| review results | review-results/ | - |

## Stage Status
- [ ] spec design
- [ ] spec eval
- [ ] spec review
- [ ] implementation
- [ ] implementation eval
- [ ] implementation review

## Key Decisions
<Decision + basis, one per line. Keep this suitable for subagent context injection.>

## Open Items
<blocking/open/assumed items and meaningful TBDs.>
```

Artifact paths are relative to the manifest directory. Stages are not a forced pipeline; record only what exists and what happened.

Update responsibility: any skill that creates an artifact or changes a stage result updates the manifest before finishing.

## Handoff

Each skill ends by suggesting one or two natural next steps from manifest state. Do not force the pipeline.

| Just completed | Natural next suggestions |
|----------------|--------------------------|
| Spec draft | `codex-eval-gate spec` or `codex-review spec`, then `codex-spec-dev` |
| Plan | `codex-eval-gate plan` or implementation |
| Implementation | `codex-eval-gate implementation` and/or `codex-review implementation` |
| Eval NEEDS_REVISION | return to `codex-spec-designer` or `codex-spec-dev`, depending on the finding |
| Review CONCERNS/RETHINK | return to the artifact-producing skill with accepted concerns |

## Question policy

Follow `shared/question-policy.md`: investigate first, propose options, and ask only for decisions that genuinely belong to the user.
