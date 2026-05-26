# Intake

프로젝트가 신규이거나, 모호하거나, harness를 안전하게 만들 만큼 context가 부족할 때 사용한다.

한 번에 최대 3개만 질문한다. structure와 validation을 unblock하는 질문을 우선한다.

## Core Questions

1. product 또는 system은 무엇이고, 첫 useful milestone은 무엇인가?
2. 이미 결정된 stack은 무엇인가? language, framework, package manager, storage, deployment target 등.
3. 의도적으로 열어둔 open decision은 무엇이며, agent가 단독으로 결정하면 안 되는 항목은 무엇인가?

## Harness-Specific Questions

code에서 확인할 수 없을 때 질문한다.

- 모든 agent가 처음 읽어야 할 것은 무엇인가?
- correctness를 정의하는 command는 무엇인가? test, lint, format, build, type check, local server 등.
- 어떤 architectural boundary가 중요한가?
- agent 또는 human이 이미 반복한 실수는 무엇인가?
- 어떤 external knowledge를 repo-local docs로 옮겨야 하는가?
- 원하는 autonomy level은 무엇인가? docs only, guardrails, spec workflow, eval workflow, PR automation 등.

## Taste and Convention Questions

convention이 충돌하거나 없을 때 질문한다.

- 기존 style이 일관되지 않아도 보존할 것인가, 새 baseline을 정의할 것인가?
- docs 작성 언어 선호가 있는가?
- decision은 ADR, specs, execution plans, issue tracker links 중 어디에 남길 것인가?
- generated references를 repo에 포함해도 되는가?

## Classification Labels

notes와 docs에 이 label을 사용한다.

| Label | Meaning |
|---|---|
| `confirmed` | user가 확인함 |
| `from-code` | repo에서 path 근거로 확인함 |
| `recommended` | agent recommendation, 아직 accepted 아님 |
| `open` | unresolved, non-blocking |
| `blocking` | implementation 전 결정 필요 |
