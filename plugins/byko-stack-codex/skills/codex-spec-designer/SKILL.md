---
name: codex-spec-designer
description: Codex에 최적화된 구현 스펙 작성 스킬. 사용자의 기능 개발, 변경 설계, 구현 명세, "스펙 작성", "설계 문서", "spec 만들어줘", "기능 설계", "구현 전에 정리" 요청에서 사용한다. 코드베이스를 먼저 분석하고, 질문은 조사 기반 선택지로 제한하며, manifest.md를 중심으로 spec/ledger/analysis 산출물을 작성한 뒤 eval-gate, review, 구현으로 이어지는 다음 단계를 제안한다.
---

# Codex Spec Designer

구현자가 추가 맥락 없이 시작할 수 있는 스펙과, 다른 스킬이 이어받을 수 있는 작업 매니페스트를 만든다. 먼저 `../../shared/workflow.md`와 `../../shared/question-policy.md`를 읽고 따른다.

## Purpose

- Main session stays as orchestrator: decisions, concise summaries, artifact writing, and handoff.
- Codebase facts are discovered before questions are asked.
- Work state is shared through `manifest.md`, not through fixed filenames alone.
- Review needs the original problem, so write a clear manifest `Problem Definition` before the spec solution hardens.

## Workflow

### 1. Resolve work directory

Use the shared target resolution order:

1. explicit user path or project name
2. existing `docs/specs/*/manifest.md`
3. new `docs/specs/<project-name>/manifest.md`

If creating a new work directory, choose a short stable project name from the request and create:

```text
docs/specs/<project>/
├── manifest.md
├── spec.md
├── ambiguity-ledger.md
└── analysis/
```

If the request is too broad to choose a project name or target area, ask 1-3 narrowing questions. Otherwise proceed.

### 2. Investigate before asking

Search with `rg`, `rg --files`, `git grep`, and focused file reads. Confirm:

- existing implementation and analogous patterns
- relevant tests, fixtures, and commands
- callers/callees and shared data structures
- error handling, auth, persistence, migration, logging, and observability patterns
- project conventions that affect the requested change

For broad analysis, use subagents only when the current Codex tool policy permits it. If multi-agent tools are not visible and delegation is allowed by the user's request/current policy, discover them with `tool_search`. Save detailed findings under `analysis/<topic>.md`; keep the main context to conclusions and file paths.

### 3. Apply the question policy

Use `../../shared/question-policy.md`.

Classify every ambiguity into:

- `from-code`: resolved by code/docs with file:line evidence
- `confirmed`: answered by the user or existing artifact
- `assumed`: adopted recommendation with basis and alternatives
- `open`: non-blocking unknown
- `blocking`: user decision required before a valid spec exists

Ask only for blocking decisions. Questions must include 2-3 options, a recommendation, and a tradeoff. Never ask for codebase facts that can be searched.

Maintain the ambiguity gate:

- `blocking`: 0 before final spec
- `assumed`: 2 or fewer
- `open`: 3 or fewer

Use `references/ambiguity-ledger.md` for the ledger shape.

### 4. Write artifacts

Update or create `manifest.md` first:

- `Problem Definition`: 2-5 lines describing the original problem, not the chosen solution
- `Artifacts`: relative paths and current status
- `Key Decisions`: only durable decisions with basis
- `Open Items`: blocking/open/assumed items

Write:

- `spec.md` using `references/spec-templates.md`
- `ambiguity-ledger.md`
- `analysis/<topic>.md` for substantial codebase findings

The spec must include:

- goals and non-goals
- current-state analysis with file:line evidence
- requirements and domain rules
- implementation guidance matched to current code conventions
- failure/edge cases
- acceptance criteria with verification method for every AC
- test strategy
- implementation order
- remaining non-blocking decisions

Do not mark assumptions as confirmed. Do not let `[TBD]` affect implementation direction, public API, data model, security, migration, or AC meaning.

### 5. Self-check before completion

Before saying the spec is complete, verify:

- manifest exists and references the spec/ledger/analysis artifacts
- ledger gate passes
- every AC is testable and has a verification method
- codebase claims cite concrete files
- the spec can be implemented without hidden product or architecture decisions

If the gate fails, report "not complete", list the blocking decisions, and give the resume point.

### 6. Handoff

Finish with enough context that the user does not need to open files:

```markdown
스펙 초안을 완료했습니다.
- manifest: docs/specs/<project>/manifest.md
- spec: docs/specs/<project>/spec.md
- ledger: docs/specs/<project>/ambiguity-ledger.md
- gate: blocking 0, assumed N, open N

다음 단계:
1. `$byko-stack-codex:codex-eval-gate spec docs/specs/<project>/manifest.md`
2. `$byko-stack-codex:codex-review spec docs/specs/<project>/manifest.md`
3. `$byko-stack-codex:codex-spec-dev docs/specs/<project>/manifest.md`
```

Suggest only the most relevant one or two next steps unless the user asked for the full cycle.

## References

- `../../shared/workflow.md`
- `../../shared/question-policy.md`
- `references/ambiguity-ledger.md`
- `references/spec-templates.md`
