---
name: codex-goal-run
description: codex-goal-design이 만든 docs/goals 상태를 읽어 Codex native goal과 worker, evaluator, auditor subagent로 장기 목표를 실행·재개한다. "goal 실행", "끝까지 계속", "subagent로 orchestration", "중단한 목표 재개", "Ralph loop로 반복" 요청에서 사용한다. 목표 계약이 없거나 단발 작업이면 먼저 codex-goal-design 또는 일반 workflow를 사용한다.
---

# Codex Goal Run

main Codex session이 authoritative orchestrator다. task work, independent eval, checkpoint audit를 fresh subagent에 맡기고, 상태는 항상 disk에 먼저 기록한다.

시작하기 전에 다음을 모두 읽는다.

- `../../shared/operating-model.md`
- `../../shared/artifact-contract.md`
- `../../shared/question-policy.md`
- `references/orchestration.md`
- 장애나 재개 상황이면 `references/recovery.md`

worker, evaluator, auditor를 dispatch하는 시점에 해당 role reference를 먼저 읽는다. role instruction은 이 skill이 명시적으로 요청하는 subagent delegation의 일부다.

## 1. target과 state 복원

goal path 해석 순서:

1. 사용자가 지정한 `goal_dir` 또는 slug
2. 현재 native goal objective와 연결된 `docs/goals/*/goal.md`
3. candidate가 하나면 사용
4. 여러 개면 상태와 최근 update를 제시하고 사용자에게 선택 요청

`goal.md`, `plan.md`, `state.json`, `knowledge.md`, `journal.md`, 관련 task/handoff/eval을 읽는다. plugin root의 `../../scripts/validate_goal.py <goal_dir>`를 실행한다. 현재 위치가 skill directory가 아니면 먼저 이 skill의 설치 경로를 기준으로 script의 절대 경로를 resolve한다. schema drift가 있으면 worker를 띄우지 말고 `references/recovery.md`의 state repair를 적용한다.

repo `AGENTS.md`와 current worktree의 user changes도 확인한다. 다른 작업의 변경을 되돌리지 않는다.

## 2. native goal lifecycle

native goal 도구가 있으면 현재 goal을 조회한다.

- active goal이 없고 사용자가 이 run/start를 명시적으로 요청했다면 `goal.md`의 Objective와 DoD를 합친 durable objective로 새 goal을 만든다.
- 사용자가 명시적으로 token budget을 지정한 경우에만 `token_budget`을 전달한다.
- 같은 objective의 active goal이면 새로 만들지 않고 이어간다.
- 다른 unfinished goal이 있으면 교체하지 않는다. 현재 goal을 pause/clear할지 사용자 결정을 받는다.
- native goal 도구가 없는 client에서는 disk state로 재개하되, background persistence가 host에 의해 보장된다고 주장하지 않는다.

native plan UI가 있으면 가까운 checkpoint 3~6개만 mirror한다. durable source of truth는 `plan.md`와 `state.json`이다.

## 3. preflight gate

다음이면 dispatch 전에 멈춘다.

- Objective 또는 DoD에 검증 방법이 없다.
- contract 의미를 바꾸는 blocking/TBD가 남았다.
- 이번 task가 authorization boundary 밖 action을 요구한다.
- dependency 또는 write scope가 현재 user change와 충돌한다.
- subagent 기능이 없는데 independent evaluation이 DoD의 필수 조건이다.

마지막 경우 degraded single-agent mode로 조용히 대체하지 않는다. 사용자가 독립 eval 생략을 명시적으로 승인하면 journal에 contract exception을 남길 수 있지만, DoD 자체를 충족했다고 가장하지 않는다.

## 4. orchestration loop

`references/orchestration.md`의 state transition과 dispatch contract를 그대로 따른다.

각 round의 핵심 순서:

1. disk state 재독과 cap/stall/approval/checkpoint 확인
2. dependency가 풀린 task 중 conflict 없는 batch 선택
3. main이 task를 claim하고 `state.json`과 `journal.md`를 먼저 갱신
4. fresh worker dispatch
5. worker 종료 후 fresh evaluator를 neutral pointer만으로 dispatch
6. `APPROVED`만 main이 `done` 처리; `NEEDS_REVISION`은 같은 worker에 eval path로 follow-up
7. artifact ownership, knowledge 후보, plan 후보를 main이 실제 diff와 대조해 통합
8. checkpoint마다 fresh auditor 실행, routine plan delta는 기록 후 적용
9. state validator 실행 후 다음 round

병렬 writer는 `operating-model.md`의 조건을 모두 만족할 때만 사용한다. available slot을 전부 채우는 것이 목표가 아니다. write conflict를 피하는 것이 우선이다.

subagent가 작업하는 동안 main은 겹치지 않는 state 확인, 다음 read-only 준비, 사용자 progress update를 수행할 수 있다. 60초 이상 조용히 있지 말고 현재 task, 검증 단계, blocker 여부를 짧게 알린다.

## 5. checkpoint와 dynamic replanning

`completed_since_checkpoint >= checkpoint_every`이거나 final acceptance 직전이면 auditor를 띄운다. auditor는 report만 쓰고 plan을 직접 바꾸지 않는다.

main은 auditor delta를 실제 evidence와 대조한다.

- routine change: add, split, refine, reorder pending, evidence-backed supersede
- material change: goal/DoD/scope/authorization/coverage/new external dependency 변경

routine change는 `plan_revision`과 `autonomous_plan_revisions`를 증가시키고 plan/state/task/journal을 함께 갱신한다. `autonomous_plan_revision_limit`에 닿으면 cap stop으로 사용자에게 plan review를 요청한다. material change는 적용하지 말고 `waiting_user`로 전환한다.

## 6. final acceptance

required task가 모두 `done` 또는 evidence-backed `superseded`이면 final auditor와 end-to-end evaluator를 fresh context로 실행한다. DoD의 deterministic command와 실제 artifact inspection도 main이 확인한다.

미충족이면 관련 task를 재오픈하거나 in-scope missing task를 추가하고 cap이 남아 있으면 loop를 계속한다. 모든 DoD가 통과하고 남은 required work가 없을 때만:

1. `state.json`을 `complete`로 전환
2. `journal.md`에 final evidence 기록
3. native goal을 `complete`로 전환
4. 사용자에게 결과, verification, 주요 artifact path, plan revision history를 요약

## 7. 정지와 인계

cap, approval, repeated blocker, stall, environment 문제로 멈추면 실패처럼 뭉뚱그리지 않는다. `state.json`과 journal에 정확한 stop reason, 마지막 verified point, next safe action을 기록한다.

native goal을 `blocked`로 바꾸는 것은 같은 blocker가 세 번 연속 goal turn에서 반복되고 다른 meaningful progress가 불가능할 때뿐이다. cap 도달이나 첫 blocker는 disk state만 멈추고 재개 방법을 제공한다.

항상 다음을 보고한다.

- 완료/전체 task와 current plan revision
- 마지막으로 검증된 evidence
- blocked/waiting task와 정확한 이유
- goal directory
- 재개 command: `$byko-goal-codex:codex-goal-run <slug>`
