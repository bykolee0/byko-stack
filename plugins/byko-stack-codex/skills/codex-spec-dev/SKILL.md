---
name: codex-spec-dev
description: Codex에 최적화된 스펙/요구사항 기반 구현 스킬. spec.md, manifest.md, docs/specs 폴더, implementation-plan.md, "스펙 구현", "spec 기반 개발", "구현 시작", "이 기능 개발해줘" 요청에서 사용한다. 스펙이 있으면 AC 추적성을 유지하고, 스펙이 없으면 합의된 요구사항으로 경량 manifest/AC를 만든 뒤 구현, 테스트, 검증까지 진행한다. 긴 작업에서는 파일 기반 progress와 Codex plan/goal/subagent-aware 구현 루프를 사용한다.
---

# Codex Spec Dev

요구사항을 실제 코드와 검증 결과로 완결한다. 먼저 `../../shared/workflow.md`와 `../../shared/question-policy.md`를 읽고 따른다.

## Purpose

- Do not stop at a plan when the user asked for implementation.
- Preserve traceability from problem/spec to AC to code/tests.
- Keep long-running state in files so a new Codex session can resume.
- Use subagents only when current Codex policy permits it and write scopes are disjoint.

## Workflow

### 1. Resolve inputs

Use shared target resolution:

1. explicit manifest/spec/plan/path from the user
2. existing `docs/specs/*/manifest.md`
3. conversation requirements

Read what exists:

- `manifest.md`
- `spec.md`
- `ambiguity-ledger.md`
- `analysis/`
- `implementation-plan.md`
- `traceability.md`
- `progress.md`

If no spec exists but the conversation has enough agreed requirements, create a lightweight work directory with `manifest.md`, `implementation-plan.md`, `traceability.md`, and `progress.md`. Include at least one verifiable AC. If the problem, target area, or expected behavior is still unclear after investigation, ask concise option-based blocking questions.

### 2. Implementation readiness gate

Stop and bounce back when:

- ledger has `blocking` items
- an AC has no verification method
- `[TBD]` affects implementation direction, public API, data model, security, migration, or AC meaning
- spec/requirements conflict with current architecture in a way that needs a product or design decision
- a required side effect is hard to reverse and not approved

Non-directional TBDs, naming details, and log wording may be assumed. Record them in `progress.md` and manifest `Open Items`.

### 3. Refresh codebase analysis

Before editing, re-check the current code even if analysis docs exist:

- target files and nearest local patterns
- tests and commands
- error handling, logging, auth, persistence, and migration conventions
- caller/callee impact and shared state
- user changes in the worktree

Do not revert user changes. If user changes affect the task, adapt to them.

### 4. Plan and traceability

For small changes, an in-response checklist is enough. For multi-step work or 3+ ACs, update/create:

```text
docs/specs/<project>/
├── implementation-plan.md
├── traceability.md
├── progress.md
└── goal-loop-prompt.md   # only for long resumable work
```

Traceability must map every AC:

| AC ID | AC | Implementation step | Files | Verification | Status |
|-------|----|---------------------|-------|--------------|--------|

If an AC cannot be mapped, improve the plan/spec before editing.

### 5. Implement

Choose the smallest strategy that finishes safely:

- Small: edit directly, run focused tests.
- Medium: maintain a plan/checklist and verify after each slice.
- Large/resumable: use `references/goal-loop-template.md`, `progress.md`, and the active Codex plan/goal if present.

Subagent implementation loop, when current policy permits:

1. Split by AC or module with disjoint file ownership.
2. Tell workers they are not alone in the codebase and must not revert others' edits.
3. Provide manifest path, ACs, owned files/modules, verification command, and output expectations.
4. Integrate only after reviewing diffs, tests, and AC evidence.
5. Never accept a worker report without checking changed files.

If subagents are unavailable or ownership overlaps, implement locally and keep state in `progress.md`.

### 6. Verify

Before completion, verify:

- every AC status is pass or explicitly blocked
- tests or manual/static verification cover each AC
- relevant existing tests pass, or failures are explained with evidence
- implementation does not add unrelated scope
- code follows local conventions and handles failure paths

Record verification in `progress.md` and update manifest stage status.

### 7. Bounce back

Return to spec design instead of coding around unclear requirements when:

- ACs have competing interpretations
- architecture/data/security decisions are missing
- the requested behavior conflicts with established conventions
- tests cannot be defined for the expected behavior

Report:

```markdown
스펙 보완이 필요합니다.
- 문제: ...
- 근거: <file:line or spec text>
- 돌아갈 단계: `$byko-stack-codex:codex-spec-designer <manifest-or-spec>`
```

### 8. Handoff

On completion, report:

```markdown
구현을 완료했습니다.
- manifest: docs/specs/<project>/manifest.md
- 변경 파일: ...
- AC 검증: AC-1 pass, AC-2 pass
- 테스트: ...

다음 단계:
`$byko-stack-codex:codex-eval-gate implementation docs/specs/<project>/manifest.md`
`$byko-stack-codex:codex-review implementation docs/specs/<project>/manifest.md`
```

If incomplete, say "미완료", list remaining ACs, blockers, current progress file, and exact resume command.

## References

- `../../shared/workflow.md`
- `../../shared/question-policy.md`
- `references/goal-loop-template.md`
