---
name: agent-harness-builder
description: 기존/신규 소프트웨어 프로젝트를 위한 agent-first harness를 설계하고 구축하는 스킬. "하네스 만들어줘", "AGENTS.md 구성", "프로젝트 온보딩 문서", "에이전트용 docs 구조", "guardrail 추가", "architecture/convention check", "spec/plan/eval workflow", "여러 프로젝트에서 재사용할 agent 운영 체계" 같은 요청에 사용한다. Existing/brownfield project에서는 repo를 먼저 분석하고, greenfield/new project에서는 intake 질문으로 제품·stack·확정 결정·open decision을 정리한 뒤 문서 구조와 가벼운 실행 guardrail을 만든다. 특정 언어나 프레임워크에 과적합하지 않고 프로젝트의 기존 test/lint/build 도구를 우선 사용한다.
---

# Agent Harness Builder

coding agent가 프로젝트를 이해하고, 필요한 질문을 하고, 결정을 보존하고, 반복되는 실수를 실행 가능한 feedback loop로 바꿀 수 있도록 repo-local harness를 구축한다.

핵심 규칙: **generic template을 무작정 생성하지 않는다.** 기존 프로젝트가 있으면 먼저 분석하고, 신규 프로젝트면 먼저 intake를 진행한다. open decision은 임의로 결정하지 않고 명시적으로 보존한다.

## Workflow

### 1. Project State 분류

먼저 어떤 경로인지 판단한다.

| State | Signal | Action |
|---|---|---|
| Brownfield | source, package file, docs, tests, CI 등이 이미 있음 | `references/existing-project.md`를 읽고, 넓은 질문 전에 repo를 먼저 분석한다. |
| Greenfield | 의미 있는 source/docs가 아직 없거나 새 프로젝트를 시작함 | `references/greenfield-project.md`와 `references/intake.md`를 읽고 intake 질문부터 한다. |
| Ambiguous | 파일은 있지만 목적, stack, convention이 불명확함 | 얕게 scan한 뒤 불확실성을 요약하고 targeted question을 한다. |

`rg --files`, package manifest, docs, tests, CI 파일로 stack과 기존 convention을 파악한다. language, framework, test runner, architecture를 추측으로 확정하지 않는다.

### 2. Decisions와 Open Decisions 분리

다음을 구분한다.

- **Confirmed decisions**: 사용자가 말했거나 문서에 명확히 있는 사실.
- **From-code facts**: 기존 파일과 command에서 확인한 사실.
- **Recommendations**: agent의 추천. 아직 확정이 아님을 명시한다.
- **Open decisions**: harness가 몰래 결정하면 안 되는 미결정 항목.

project shape, testing, security, deployment, data retention, public API behavior에 영향을 주는 결정은 encoding 전에 사용자에게 확인한다.

### 3. Harness를 Layer로 구축

가장 작은 유용한 harness부터 시작한다.

1. Entry map: `AGENTS.md` 또는 해당 프로젝트의 agent entry point.
2. Knowledge store: `docs/README.md`, `docs/references/`, `docs/design-docs/`, `docs/specs/`, 필요 시 `docs/exec-plans/`, `docs/generated/`.
3. Project-specific foundation ADR: `docs/design-docs/0001-agent-harness-foundation.md`.
4. Lightweight guardrails: 중요한 convention을 강제하는 tests/scripts/lint task.
5. Runbook: build, test, lint, server, DB, fixtures, agent-safe validation을 위한 local command.

문서 형태는 `references/harness-docs.md`, guardrail 후보는 `references/guardrail-catalog.md`를 읽는다.

### 4. Stack에 맞는 Guardrail 선택

Guardrail은 실행 가능하고 저렴해야 한다. 가능하면 프로젝트의 기존 toolchain을 사용한다.

- Python: 초기는 pytest-based architecture tests. import graph rule이 커지면 import-linter 고려.
- Node/TypeScript: `npm script` + eslint/vitest/jest/custom AST check.
- Go: `go test` 기반 package structure check 또는 작은 script.
- Rust: `cargo test` 또는 custom xtask.
- Polyglot: docs, imports/dependencies, commands, generated reference를 점검하는 repo-level script.

stack-specific check를 추가하기 전에 `references/language-adapters.md`를 읽는다.

### 5. Validate and Explain

수정 후:

1. 추가한 narrow harness check를 실행한다.
2. 가능한 경우 기존 lint/test command도 실행한다.
3. 단순 파일 목록이 아니라 “어떤 feedback loop가 생겼는지” 설명한다.
4. 남은 open decision과 다음 guardrail 후보를 나열한다.

실행 가능한 feedback loop가 없으면 harness가 “완성”됐다고 말하지 않는다. 문서만 있는 상태는 foundation일 뿐이다.

## Reference Map

- `references/intake.md`: product, stack, decisions, taste, validation, open decisions 질문지.
- `references/existing-project.md`: brownfield repo 분석 workflow.
- `references/greenfield-project.md`: 신규 프로젝트 시작 workflow.
- `references/harness-docs.md`: 권장 repo-local docs와 index.
- `references/guardrail-catalog.md`: language-neutral guardrail 후보.
- `references/language-adapters.md`: stack-specific implementation option.
- `references/source-notes.md`: 이 skill의 근거 자료와 rationale.
