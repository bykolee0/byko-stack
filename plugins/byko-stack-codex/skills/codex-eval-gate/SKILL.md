---
name: codex-eval-gate
description: Codex에 최적화된 스펙, 구현 계획, 구현 결과 품질 게이트. "$byko-stack-codex:codex-eval-gate spec docs/specs/project/manifest.md", "$byko-stack-codex:codex-eval-gate plan implementation-plan.md", "$byko-stack-codex:codex-eval-gate implementation docs/specs/project/manifest.md src/" 요청에서 사용한다. 현재 세션의 자기 평가가 아니라 Codex subagent 격리 컨텍스트와 선택적 Claude 교차검증으로 상위 산출물·코드베이스 정합성을 평가하고 APPROVED/NEEDS_REVISION/BLOCKED를 판정한다.
---

# Codex Eval Gate

스펙/계획/구현이 다음 단계로 넘어갈 만큼 정합한지 평가한다. 먼저 `../../shared/workflow.md`를 읽고 따른다.

이 스킬은 문제 해결 방향의 fresh-eyes 리뷰가 아니다. "애초의 문제를 제대로 풀었는가"는 `$byko-stack-codex:codex-review`가 담당한다.

## Rules

- Do not perform the evaluation body in the current session.
- The main session may run self-gate checks, prepare requests, spawn/coordinate isolated evaluators, recheck findings, write result files, and report.
- Do not ask the user to choose an evaluation method by default.
- If isolated evaluation cannot run, return `BLOCKED` or `NEEDS_REVISION`; never produce `APPROVED` from same-context review.
- Use `codex-claude-eval` only as optional cross-check: user requested it, evaluator result is disputed/low confidence, or the change is hard to reverse.

## Modes

```text
$byko-stack-codex:codex-eval-gate spec <manifest-or-spec>
$byko-stack-codex:codex-eval-gate plan <manifest-or-plan>
$byko-stack-codex:codex-eval-gate implementation <manifest-or-spec> [changed paths]
$byko-stack-codex:codex-eval-gate custom <target files> --criteria <criteria>
```

Path omission follows the manifest resolution rules in `../../shared/workflow.md`.

## Workflow

### 1. Resolve target

Determine mode and target files from:

1. explicit arguments
2. `manifest.md` artifacts and stage state
3. user confirmation when multiple candidates remain

Extract neutral context only:

- manifest `Problem Definition`
- manifest `Key Decisions`
- artifact paths
- changed paths and test results for implementation mode

Do not include the main session's expected verdict.

### 2. Self-gate

Run cheap mechanical checks before independent evaluation.

Spec:

- spec exists
- ledger exists when the manifest lists one
- ledger `blocking` is zero
- `assumed <= 2`, `open <= 3`
- AC table exists
- every AC has a verification method

Plan:

- plan exists
- spec or AC source exists
- traceability covers every AC when present
- plan has verification steps

Implementation:

- spec or AC source exists
- changed paths are known
- relevant tests or explicit manual/static verification are recorded
- runnable focused tests have been run when feasible

If self-gate fails, do not spawn an evaluator. Write a gate result with `NEEDS_REVISION`, update the manifest if available, and report the exact fixes.

### 3. Prepare evaluator request

Use:

- `references/request-template.md`
- `references/checklists.md`

Save under:

```text
<work-dir>/eval-results/<mode>-codex-evaluator-<timestamp>.request.md
```

If no work directory exists, use `.myagents/eval-results/`.

Copy relevant source documents into the request where practical. For implementation mode, copy the spec/traceability and list changed code paths for direct inspection.

### 4. Run isolated evaluation

If multi-agent tools are not currently loaded, use `tool_search` for multi-agent/subagent tools. When available and allowed by current Codex policy, spawn an isolated evaluator with a minimal prompt:

```text
Use the evaluation request at <absolute request path>.
Read the target files listed in it and inspect the codebase as needed.
Evaluate according to the checklist.
Return APPROVED, NEEDS_REVISION, or BLOCKED with concrete evidence.
Do not assume the caller's work is correct.
```

If subagent execution is unavailable or not permitted, do not substitute current-session analysis. Use `codex-claude-eval` only when requested or when it is an acceptable fallback for this invocation. Otherwise write `BLOCKED` with `evaluation_context: none`.

### 5. Optional Claude cross-check

Run `$byko-stack-codex:codex-claude-eval` when:

- the user explicitly asks for Claude/cross evaluation
- the evaluator result is low confidence or disputed
- the artifact changes schema, public API, security policy, data deletion, or migration behavior

Claude failure does not invalidate a successful Codex evaluator result by itself. Record the failure and decide from the successful independent evidence, unless the user requested Claude-only evaluation.

### 6. Recheck findings and decide

The main session verifies evaluator FAILs against files before accepting them:

- `accepted`: evidence is correct and revision is needed
- `rejected`: false positive, with file evidence
- `needs_followup`: plausible but requires user/product decision

Verdict:

- `APPROVED`: isolated evaluation ran and there are no accepted structural/semantic FAILs
- `NEEDS_REVISION`: accepted FAILs affect correctness, completeness, safety, traceability, or implementation readiness
- `BLOCKED`: no independent evaluation ran, required target is missing, or criteria are undefined

### 7. Write result and update manifest

Save:

```text
<work-dir>/eval-results/<mode>-gate-<timestamp>.result.md
```

Result shape:

```markdown
# Eval-Gate Result: <mode>

## Verdict: APPROVED | NEEDS_REVISION | BLOCKED
- confidence: high | medium | low
- self_gate: pass | fail
- evaluation_context: codex-subagent | claude-process | codex-subagent+claude-process | none

## Detail Files
- evaluator: ...
- claude-eval: ... | not-run

## Accepted Findings
...

## Rejected Findings
...

## Needs Follow-up
...

## Next Step
...
```

Update manifest `Artifacts` and `Stage Status` when a manifest is available.

### 8. Report

The user report must be enough without opening result files:

- verdict and confidence
- independent context used
- accepted findings and concrete fix direction
- rejected/needs-followup summary when present
- result file path
- next step

Next steps:

- spec APPROVED: `codex-spec-dev` or `codex-review spec`
- plan APPROVED: continue implementation
- implementation APPROVED: `codex-review implementation` if fresh-eyes review is desired, otherwise complete
- NEEDS_REVISION: route to `codex-spec-designer` for spec/AC issues or `codex-spec-dev` for plan/code fixes

## References

- `../../shared/workflow.md`
- `references/checklists.md`
- `references/request-template.md`
