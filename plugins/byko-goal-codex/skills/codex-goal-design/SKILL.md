---
name: codex-goal-design
description: 한 turn에 끝나지 않는 coherent objective를 Codex native goal과 subagent orchestration으로 실행할 수 있게 설계한다. "장기 목표를 세워줘", "여러 turn 동안 끝까지 진행", "Ralph loop처럼 반복", "byko-goal Codex 시작", "목표를 task로 나누고 문서화" 요청에서 사용한다. 단발 작업이나 서로 무관한 backlog 정리에는 사용하지 않는다.
---

# Codex Goal Design

장기 목표를 대화와 조사로 명료화하고 `docs/goals/<slug>/`에 durable contract, dynamic plan, runtime state를 만든다. 후속 실행은 `codex-goal-run`이 담당한다.

시작하기 전에 다음을 모두 읽는다.

- `../../shared/question-policy.md`
- `../../shared/operating-model.md`
- `../../shared/artifact-contract.md`
- `references/task-design.md`

## 1. 적합성 확인

먼저 `docs/goals/*/goal.md`를 찾아 같은 objective의 진행 중 goal이 있는지 확인한다. 있으면 새 goal을 만들지 말고 현재 상태와 설계 보완 필요 여부를 보고한다.

새 goal은 다음을 만족해야 한다.

- 한 normal turn보다 크다.
- 서로 무관한 backlog가 아니라 하나의 coherent objective다.
- 성공과 정지를 관찰 가능한 조건으로 정의할 수 있다.
- 승인 없이 실행해도 되는 local scope가 존재한다.

작업이 작으면 일반 구현 workflow를 권하고 이 skill을 종료한다.

## 2. 조사

repo의 `AGENTS.md`, 기존 docs, 관련 코드와 테스트, user change를 먼저 읽는다. 범위가 넓고 subagent 도구가 제공되면 이 skill의 지시에 따라 1~2개의 read-only explorer subagent를 병렬로 사용한다. 각 explorer에는 서로 겹치지 않는 조사 질문과 근거 형식을 주고, write를 금지한다. subagent를 쓸 수 없으면 main이 직접 조사한다.

확인한 사실은 `file:line`, 명령, URL 같은 source pointer와 함께 압축한다. 조사로 답할 수 있는 내용을 사용자에게 되묻지 않는다.

## 3. goal contract 합의

다음을 특정한다.

1. **Objective**: 완성됐을 때 참인 상태 한 가지
2. **Definition of Done**: 각 조건과 검증 방법
3. **Scope / Non-goals**
4. **Required context**: 모든 task가 알아야 하는 안정적 사실
5. **Authorization boundary**: 자율 local action과 사전 승인 action
6. **Evaluation strategy**: task gate, checkpoint regression, final end-to-end 검증

사용자가 정해야 하는 갈림길만 선택지와 추천으로 묻는다. blocking ambiguity가 없고, contract 의미를 바꾸는 `[TBD]`가 없을 때까지 실행 문서를 확정하지 않는다.

**readiness gate:** `[assumed]`가 3개 이상이거나 하나가 여러 task의 동작을 결정하면 묶어서 사용자 확인을 받는다. 사용자 응답을 받을 수 없는 환경에서는 draft artifact까지 만들 수 있지만 `state.status`를 `waiting_user`로 두고 journal에 `[decision-required]`와 필요한 선택지를 남긴다. 이 상태를 실행 준비 완료라고 보고하지 않는다.

native goal의 token budget은 사용자가 숫자를 명시적으로 요청한 경우에만 기록한다. 일반 시간·비용 선호를 임의의 token budget으로 바꾸지 않는다.

## 4. dynamic plan 설계

`references/task-design.md` 기준으로 task graph를 만든다.

- task ID는 `T-001`부터 단조 증가한다.
- task마다 requirement link, acceptance criteria, 검증 방법, 예상 write scope, dependency를 둔다.
- acceptance criteria는 worker에게 미루지 않고 design 시점에 작성한다.
- task graph는 실행 중 바뀔 수 있지만 goal contract는 사용자 승인 없이 바뀌지 않는다.
- 병렬 후보는 write scope와 dependency가 실제로 분리된 경우에만 표시한다.

안전 노브 기본값을 제안한다.

- `worker_dispatch_limit`: `max(12, initial_task_count * 3)`
- `per_task_revision_limit`: 3
- `checkpoint_every`: 4
- `stall_limit`: 3
- `blocker_streak_limit`: 3
- `autonomous_plan_revision_limit`: 8

비용 민감도, 외부 유료 operation, unusually large plan이 있으면 값을 사용자에게 확인받는다. 그 밖에는 `[assumed]`로 기록하고 한 번에 보여준다.

## 5. artifact 생성

`../../shared/artifact-contract.md`의 schema를 따라 다음을 만든다.

- `goal.md`
- `plan.md`
- `state.json`
- `knowledge.md`
- `journal.md`
- 모든 initial task의 `tasks/T-NNN.md`
- 빈 `handoffs/`, `eval/`, `audit/` directory

`knowledge.md`에는 조사에서 얻은 항구적 사실과 source pointer를 seed한다. `journal.md`에는 initial design event와 `[from-research]`, `[assumed]`, 사용자 결정을 기록한다.

initial `state.json.artifact_owners`는 비워 둔다. `plan.md`와 task file의 write scope는 예상치이고, 실제 ownership은 run 단계에서 evaluator 승인 후에만 기록한다.

plugin root의 `../../scripts/validate_goal.py <goal_dir>`를 실행하고 오류를 고친다. 현재 위치가 skill directory가 아니면 먼저 이 skill의 설치 경로를 기준으로 script의 절대 경로를 resolve한다. validator 통과는 schema 확인일 뿐이므로 task coverage와 DoD도 직접 대조한다.

## 6. handoff

다음을 한 번에 보여준다.

- Objective와 DoD
- task graph 요약과 병렬 가능 구간
- 자체 결정한 `[assumed]`
- 승인 경계와 stop knob
- goal directory와 validation 결과

사용자가 수정할 부분이 없다고 확인하거나 바로 실행을 요청하면 다음을 안내하거나 호출한다.

`$byko-goal-codex:codex-goal-run <slug>`

native `/goal` lifecycle이 사용 가능한 환경에서는 run skill이 이를 생성하거나 이어서 사용한다. 설계만 요청받은 경우 native goal을 먼저 시작하지 않는다.
