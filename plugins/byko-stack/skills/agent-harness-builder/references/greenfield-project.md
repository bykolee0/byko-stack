# Greenfield Project Workflow

새 프로젝트이거나 의미 있는 기존 구조가 없을 때 사용한다.

## First Move

full harness를 바로 만들지 않는다. 먼저 intake를 진행한다.

1. product/system goal
2. first milestone
3. stack decisions
4. open decisions
5. validation commands 또는 원하는 toolchain
6. documentation language와 team convention

현재 session에서 이미 논의한 내용이 있으면 모든 질문을 반복하지 말고 요약 후 확인받는다.

## Initial Harness

미래 agent에게 도움이 되는 가장 작은 구조를 만든다.

```text
AGENTS.md
README.md
docs/
├── README.md
├── references/
│   └── index.md
├── design-docs/
│   └── index.md
└── specs/
```

long-running plan이나 generated reference가 필요할 때만 `docs/exec-plans/`, `docs/generated/`를 추가한다.

## Foundation ADR

`docs/design-docs/0001-agent-harness-foundation.md`를 만들고 다음 내용을 포함한다.

- context
- confirmed decisions
- open decisions
- proposed docs structure
- first guardrail candidates
- validation commands
- follow-up questions

사용자가 명시적으로 accept하지 않았다면 status는 `proposed`로 둔다.

## First Guardrails

현재 stack이 지원하는 것만 선택한다.

예:

- docs structure check
- architecture boundary check
- forbidden dependency/import check
- time/date convention check
- generated docs freshness check
- test fixture contract check

사용자가 결정했거나 프로젝트가 이미 쓰고 있지 않은 type checker, linter, framework, dependency를 임의로 추가하지 않는다.
