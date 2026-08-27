# Recovery and stop rules

## interrupted active task

`active_tasks`가 비어 있지 않은데 해당 subagent thread가 없으면 crash residue다.

1. task file, handoff, 최신 eval, actual worktree를 읽는다.
2. partial artifact를 버리지 않는다.
3. 검증 가능한 진전이면 fresh recovery worker에 같은 task를 주고 남은 acceptance부터 이어간다.
4. 변경이 없거나 artifact가 모순이면 새 attempt로 다시 실행한다.
5. recovery 결정과 evidence를 journal에 남긴다.

destructive cleanup은 자동으로 하지 않는다. user 또는 다른 agent 변경과 구분되지 않으면 멈춘다.

## state drift

validator failure가 나면 새 work를 dispatch하지 않는다.

- `goal.md`와 user-approved contract history
- `plan.md` revision history
- task/eval/audit files
- append-only journal
- actual worktree

순서로 state를 복원한다. 추측으로 `done`을 만들지 않는다. 확실하지 않은 task는 `pending` 또는 `waiting_user`로 보수적으로 복원하고 `state-repair` event를 추가한다.

## blocker

blocker key는 `category:short-reason` 형태로 정규화한다. 예:

- `spec-gap:refund-policy`
- `env:missing-test-service`
- `permission:production-write`
- `conflict:user-owned-file`

같은 blocker가 세 번 연속 goal turn에서 반복되고 다른 독립 task도 없을 때만 native goal을 `blocked`로 전환한다. 첫 두 번은 대체 경로, read-only 조사, independent task로 의미 있는 progress가 가능한지 확인한다.

## stall

worker dispatch가 끝났는데 새 verified task, 새 evidence, blocker 해소, justified plan improvement가 하나도 없으면 no-progress round다. `consecutive_no_progress >= stall_limit`이면 멈춘다. 단순히 task가 어렵거나 eval이 실패했다는 이유만으로 stall로 세지 않는다. 수정과 새 evidence가 있으면 progress다.

## cap

다음 cap은 예정된 stop이다.

- worker dispatch limit
- per-task revision limit
- autonomous plan revision limit

cap 도달 시 state를 `stopped_cap`으로 만들고 cap을 소진한 work, last verified point, 추천 상향값과 trade-off를 보고한다. 사용자가 승인한 뒤에만 cap을 바꾼다. native goal을 complete/blocked로 바꾸지 않는다.

## waiting for user

다음은 `waiting_user`다.

- material contract change
- external write, destructive action, purchase, credential, publication
- user-owned worktree와 충돌
- 여러 타당한 방향이 결과를 materially 바꿈

정확한 decision/action, 추천, trade-off, 안전하게 계속할 수 있는 범위를 제시한다. 승인 전에는 해당 action을 수행하지 않는다.

## evaluator disagreement

worker와 evaluator가 충돌하면 main이 concrete evidence를 재확인한다. finding이 사실이면 worker에 수정한다. false positive면 evaluator report를 지우지 말고 journal correction과 근거를 남긴 뒤 fresh evaluator로 다시 본다.

## unavailable subagents

independent eval이 contract에 포함됐는데 subagent 기능이 없으면 `waiting_user`다. main self-review를 independent eval이라고 부르지 않는다. 가능한 client에서 재개하거나 사용자가 명시적으로 contract를 수정하도록 안내한다.
