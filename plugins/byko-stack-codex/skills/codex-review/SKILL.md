---
name: codex-review
description: 문제 정의에서 출발하는 Codex fresh-eyes 리뷰 스킬. 스펙이나 구현이 (1) 애초의 문제에 맞는 답인지, (2) 현재 코드베이스 컨벤션과 구조를 제대로 반영했는지, (3) 기능만 되게 때운 구현이 아닌지, (4) 확장성과 유지보수성을 해치지 않는지 별도 subagent 컨텍스트로 검토한다. "$byko-stack-codex:codex-review spec ...", "$byko-stack-codex:codex-review implementation ...", "리뷰해줘", "이 방향이 맞는지 봐줘", "제대로 구현됐는지 검토해줘" 요청에서 사용한다. eval-gate와 달리 기준점은 스펙 준수가 아니라 manifest의 원본 문제 정의다.
---

# Codex Review

산출물을 문제 정의에서 다시 본다. `codex-eval-gate`가 "상위 산출물/코드베이스와 정합한가"를 본다면, 이 스킬은 "맞는 문제를 성실하고 코드베이스에 어울리게 풀었는가"를 본다.

먼저 `../../shared/workflow.md`를 읽고 따른다.

## Rules

- Do not use the current session's implementation narrative as evidence.
- Use an isolated reviewer when current Codex policy permits subagents.
- If isolated review cannot run, return `BLOCKED`; do not replace it with same-context approval.
- The review anchor is manifest `Problem Definition`, not the final spec summary.
- Recheck reviewer concerns before accepting or rejecting them.

## Modes

```text
$byko-stack-codex:codex-review spec <manifest-or-spec>
$byko-stack-codex:codex-review implementation <manifest-or-spec> [changed paths]
$byko-stack-codex:codex-review custom <target files>
```

If mode is omitted, infer it from target paths and manifest state.

## Workflow

### 1. Resolve target and problem definition

Resolve target by explicit path, manifest, or user confirmation.

Problem definition priority:

1. manifest `Problem Definition`
2. original user request from the current conversation, summarized in 2-5 lines and confirmed if it changes the review basis
3. `BLOCKED` if no reliable problem definition exists

Do not substitute a spec goal list for the original problem. A flawed spec must be reviewable as flawed.

### 2. Prepare review request

Use:

- `references/review-request-template.md`
- `references/review-checklist.md`

Save under:

```text
<work-dir>/review-results/<mode>-codex-review-<timestamp>.request.md
```

Include:

- problem definition
- target artifact paths
- spec/plan/traceability/manifest content where practical
- changed code paths for implementation review
- review checklist

Do not include eval verdicts, current-session confidence, or "known good" framing.

### 3. Run isolated reviewer

If multi-agent tools are not loaded, use `tool_search` for multi-agent/subagent tools. When available and allowed by current Codex policy, spawn a reviewer with a minimal prompt:

```text
Use the review request at <absolute request path>.
Start from the Problem Definition before reading the proposed solution.
Inspect target artifacts and relevant codebase conventions.
Judge whether this is the right, durable solution to the original problem.
Return SOUND, CONCERNS, RETHINK, or BLOCKED with concrete evidence.
```

If subagent execution is unavailable or not permitted, write a `BLOCKED` review result and explain that same-context review would not satisfy this skill.

### 4. Recheck concerns

Classify reviewer findings:

- `accepted`: concrete evidence is valid and action is needed
- `rejected`: false positive or contradicted by code/docs
- `needs_followup`: plausible concern but user/product decision needed

Verdict handling:

| Reviewer verdict | Meaning | Main-session action |
|------------------|---------|---------------------|
| `SOUND` | right problem, durable solution | update manifest and suggest next stage |
| `CONCERNS` | direction is right but material issues exist | route accepted items to spec/dev work |
| `RETHINK` | wrong problem or wrong approach | present evidence and route to spec redesign unless user rejects |
| `BLOCKED` | review basis or isolated context missing | report missing input/tool condition |

### 5. Write result and update manifest

Save:

```text
<work-dir>/review-results/<mode>-review-<timestamp>.result.md
```

Result shape:

```markdown
# Review Result: <mode>

## Verdict: SOUND | CONCERNS | RETHINK | BLOCKED
- confidence: high | medium | low
- review_context: codex-subagent | none
- problem_definition_source: manifest | conversation | missing

## Accepted Concerns
...

## Rejected Concerns
...

## Needs Follow-up
...

## Next Step
...
```

Update manifest review status when available.

### 6. Report

Report enough for the user to decide without opening files:

- verdict and confidence
- review anchor used
- accepted concerns with evidence and fix direction
- rejected concerns only when useful
- result file path
- next step

Next steps:

- `SOUND` spec: `codex-eval-gate spec` for consistency or `codex-spec-dev`
- `SOUND` implementation: complete, or run `codex-eval-gate implementation` if consistency gate has not run
- `CONCERNS`: return to `codex-spec-designer` or `codex-spec-dev`
- `RETHINK`: return to `codex-spec-designer` with the original problem definition

## References

- `../../shared/workflow.md`
- `references/review-checklist.md`
- `references/review-request-template.md`
