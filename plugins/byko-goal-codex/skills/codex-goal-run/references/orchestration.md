# Orchestration protocol

## main-only state ownership

`goal.md`, `plan.md`, `state.json`, `knowledge.md`, `journal.md`는 main만 수정한다. subagent는 role별 report와 assigned workspace artifact만 수정한다. 이 경계가 shared-state race와 worker self-approval을 막는다.

## round preflight

매 round에서 context 기억보다 disk를 다시 읽는다.

1. `state.json` validation
2. native goal status와 사용자 steer 확인
3. dispatch, plan revision, stall, blocker cap 확인
4. checkpoint 필요 여부 확인
5. `active_tasks` crash residue 확인
6. dependency가 풀린 `pending`/`needs_revision` task 계산
7. authorization과 worktree conflict 확인

`worker_dispatches >= worker_dispatch_limit`이면 새 worker를 띄우지 않고 `stopped_cap`으로 기록한다. cap을 임의 상향하지 않는다.

## task selection

우선순위:

1. final DoD를 막는 critical path
2. 이미 `needs_revision`인 task
3. 다른 task의 dependency를 많이 푸는 task
4. 동일하면 낮은 task ID

parallel batch는 dependency와 write scope가 완전히 분리된 task만 포함한다. plan의 write scope가 넓거나 불명확하면 sequential로 실행한다.

## claim

worker spawn 전에 main이 다음을 한 update로 반영한다.

- task status `in_progress`
- task ID를 `active_tasks`에 추가
- `attempts`와 `worker_dispatches` 증가
- `updated_at` 갱신
- journal에 claim event와 dispatch 직전 worktree changed-path snapshot을 append

spawn 실패도 dispatch로 센다. 실패 이유와 retry 여부를 journal에 남긴다.

## worker dispatch

dispatch 전에 `worker-role.md`를 읽는다. worker prompt에는 다음만 포함한다.

- resolved `goal_dir`
- `task ID`
- resolved worker role reference path 또는 그 원문
- explicit write ownership
- 다른 agent/user change를 되돌리지 말라는 경계

예상 결론이나 evaluator 기준의 해석을 주입하지 않는다. worker가 `READY_FOR_EVAL`을 반환하면 완료로 취급하지 않는다.

worker 종료 후 main은 evaluator를 띄우기 전에 changed path를 한 번 확인한다. pre-dispatch snapshot에 없고 assigned write scope나 허용된 task/handoff report 밖에 생긴 path가 있으면 worker가 만든 것인지 확인해 같은 task에서 정리하게 한다. generated file도 예외가 아니다.

## evaluator gate

worker 종료 후 fresh evaluator를 띄운다. `evaluator-role.md`를 읽고, evaluator에는 다음만 준다.

- `goal_dir`
- `task ID`
- resolved evaluator role reference path 또는 그 원문

worker response나 "잘 구현됐다"는 문맥을 주지 않는다.

### `APPROVED`

main이 eval report와 actual diff를 확인한 뒤:

- task status `done`
- `active_tasks`에서 제거
- `completed_since_checkpoint` 증가
- `consecutive_no_progress` 0
- changed artifact를 `artifact_owners`에 반영
- task의 knowledge 후보를 검증해 `knowledge.md`에 통합
- handoff와 journal 갱신

### `NEEDS_REVISION`

- task status `needs_revision`
- fresh eval report path를 같은 worker thread에 follow-up
- worker에게 evaluator finding을 바꾸라고 하지 말고 실제 finding을 수정하게 한다.
- 수정 후에는 같은 evaluator를 재사용하지 않고 fresh evaluator를 새로 띄운다.
- `per_task_revision_limit`을 넘으면 normalized blocker로 전환한다.

### `BOUNCE`

acceptance나 contract에 모순, 방향을 바꾸는 누락, authorization 문제라면 main이 evidence를 확인하고 `waiting_user`로 전환한다. 코드나 문장으로 우회하지 않는다.

### agent crash 또는 `BLOCKED:<key>`

`active_tasks`에서 제거하고 task를 `blocked`로 만든다. 독립 pending task가 있으면 계속한다. task 하나가 blocked됐다는 이유만으로 root `blocker_streak`을 늘리지 않는다.

goal turn이 끝날 때 meaningful progress가 전혀 없고 같은 normalized blocker가 goal 전체를 계속 막는 경우에만 streak를 한 번 늘린다. 한 turn에서 여러 task가 같은 이유로 막혀도 1회다. 다른 progress가 생기거나 blocker key가 바뀌면 reset한다.

## auditor checkpoint

`auditor-role.md`를 읽고 fresh auditor에 `goal_dir`, `last_checkpoint`, role reference만 준다. auditor는 다음을 report한다.

- 변경된 artifact와 owner 기준 targeted regression
- done/superseded task의 acceptance 보존 여부
- pending graph의 누락, 중복, 잘못된 dependency
- routine plan delta
- material change 또는 authorization 필요 여부

auditor는 plan/state를 직접 수정하지 않는다. main이 evidence를 재확인하고 적용한다.

checkpoint를 수용하면 main은 `last_checkpoint`를 audit path가 아니라 그 시점의 마지막 완료 task ID로 갱신하고 `completed_since_checkpoint`를 0으로 reset한다. audit path와 timestamp는 journal의 checkpoint event에 둔다.

plan 변경을 적용할 때:

1. 새 monotonic task ID와 task file 생성
2. 기존 task는 삭제하지 않고 필요하면 `superseded`와 replacement 기록
3. plan revision 증가와 revision history append
4. state task/dependency 동기화
5. autonomous revision counter 증가
6. journal event append
7. validator 실행

## final gate

final evaluator에는 task ID 대신 `mode=final`과 `goal_dir`만 준다. 다음을 모두 본다.

- 모든 DoD
- task 사이 integration
- regression과 non-goals 침범
- unresolved warnings, blocked/waiting task
- 실제 command/artifact evidence

task가 전부 done이라는 사실만으로 final approval하지 않는다.
