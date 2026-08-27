# Harness Docs

repo-local docs를 system of record로 사용한다. 목표는 progressive disclosure다. 작은 entry point에서 시작해 agent가 필요한 deep context로 이동할 수 있어야 한다.

## Entry Point

`AGENTS.md`에는 보통 다음을 포함한다.

- project summary
- 알려진 runtime/storage/deployment summary
- document index
- ground rules
- required commands
- agent가 단독으로 결정하면 안 되는 open decisions

짧게 유지한다. 자세한 내용은 `docs/`로 이동한다.

## Docs Structure

권장 기본 구조:

```text
docs/
├── README.md
├── references/
├── design-docs/
├── specs/
├── exec-plans/
└── generated/
```

기존 프로젝트 convention에 맞춰 이름은 조정한다.

| Path | Purpose |
|---|---|
| `docs/README.md` | docs system의 map |
| `docs/references/` | external/vendor/domain docs의 local summary |
| `docs/design-docs/` | ADR과 오래 유지되는 decisions |
| `docs/specs/` | feature specs, ambiguity ledgers, traceability |
| `docs/exec-plans/` | long-running plans와 progress logs |
| `docs/generated/` | DB schema 같은 machine-generated references |

## ADR Rules

task보다 오래 유지되어야 하는 결정은 ADR로 남긴다.

- architecture boundaries
- harness design
- testing strategy
- deployment 또는 infra policy
- data retention
- public API conventions

권장 metadata:

```yaml
---
status: proposed
date: YYYY-MM-DD
---
```

허용 status: `proposed`, `accepted`, `superseded`.

## Spec Workflow

큰 변경에는 다음 구조를 만든다.

```text
docs/specs/<feature>/
├── index.html               # 사람용 현황 (manifest.md에서 생성)
├── spec.html                # 사람이 승인하는 문서
├── implementation-plan.html # 사람이 승인하는 문서
├── manifest.md
├── ambiguity-ledger.md
├── traceability.md
└── eval-results/
```

사람이 열어서 결정을 내리는 문서만 HTML로 두고, 상태·근거·대조표는 마크다운으로 둔다 (byko-stack의 `shared/doc-system.md`). 프로젝트가 byko-stack을 쓰지 않는다면 전부 마크다운으로 해도 된다 — 중요한 것은 **독자에 따라 형식을 나눈다**는 원칙이다.

작업이 충분히 클 때만 사용한다. 작은 변경은 대화 안의 lightweight plan과 tests로 충분할 수 있다.
