# Goal artifact contract

`docs/goals/<slug>/`는 session, compaction, subagent 사이의 durable interface다.

```text
docs/goals/<slug>/
├── goal.md                 # 고정 계약. 사용자 승인 없이 runtime이 변경하지 않음
├── plan.md                 # 가변 task graph와 plan revision history
├── state.json              # machine-readable runtime SSOT
├── knowledge.md            # 목표 전체에 유효한 압축 지식
├── journal.md              # append-only 실행 사건과 근거
├── tasks/T-NNN.md          # task 정의, acceptance, worker worklog
├── handoffs/T-NNN.md       # 다음 task가 알아야 할 일회성 정보
├── eval/T-NNN/<ts>.md      # fresh evaluator의 task 판정
└── audit/<ts>.md           # checkpoint/final audit와 plan delta 제안
```

## `goal.md`

```markdown
# Goal: <제목>

> slug: <slug>
> contract_version: 1
> created: <ISO-8601>

## Objective
<완성됐을 때 참인 상태와 이유>

## Definition of Done
- [ ] <검증 가능한 최종 조건> — 검증: <명령, rubric, 산출물 대조>

## Scope
- <허용된 대상과 변경>

## Non-goals
- <하지 않을 것>

## Required context
- <모든 task가 알아야 하는 안정적 사실과 source pointer>

## Authorization boundary
- 자율 허용: <가역적 local action>
- 사전 승인 필요: <외부 write, destructive, 비용, 공개 등>

## Evaluation strategy
- task gate: <deterministic check + 필요한 독립 판단>
- checkpoint: <회귀 범위>
- final: <end-to-end acceptance>

## Contract change history
- v1 <date> — initial, approved by user
```

Objective와 DoD가 loose backlog라면 goal로 만들지 않는다. 하나의 coherent objective와 verifiable stopping condition이 있어야 한다.

## `plan.md`

```markdown
# Plan — <slug>

> plan_revision: 1
> 상태 정본은 state.json. 이 문서는 task 의미와 dependency의 정본이다.

## Task graph
| ID | Task | Depends on | Expected write scope | Acceptance summary |
| --- | --- | --- | --- | --- |
| T-001 | ... | — | `src/...`, `tests/...` | ... |

## Revision history
- r1 <date> — initial plan
```

- ID는 `T-001`부터 단조 증가시키고 재사용하지 않는다.
- task를 제거하지 않는다. state에서 `superseded`로 바꾸고 replacement 또는 근거를 남긴다.
- task 추가/분할/정제 때 `plan_revision`을 올리고 journal에도 같은 revision을 기록한다.
- `Expected write scope`는 예상치다. worker가 벗어나야 하면 먼저 main에 보고한다.

## `state.json`

```json
{
  "schema_version": 1,
  "goal_slug": "example-goal",
  "contract_version": 1,
  "plan_revision": 1,
  "status": "designed",
  "active_tasks": [],
  "limits": {
    "worker_dispatch_limit": 18,
    "per_task_revision_limit": 3,
    "checkpoint_every": 4,
    "stall_limit": 3,
    "blocker_streak_limit": 3,
    "autonomous_plan_revision_limit": 8
  },
  "counters": {
    "worker_dispatches": 0,
    "completed_since_checkpoint": 0,
    "consecutive_no_progress": 0,
    "autonomous_plan_revisions": 0
  },
  "last_checkpoint": null,
  "blocker_streak": {
    "key": null,
    "count": 0
  },
  "tasks": {
    "T-001": {
      "status": "pending",
      "attempts": 0,
      "depends_on": [],
      "superseded_by": [],
      "last_result": null
    }
  },
  "artifact_owners": {},
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

허용 task status:

- `pending`
- `in_progress`
- `needs_revision`
- `done`
- `blocked`
- `waiting_user`
- `superseded`

허용 goal status:

- `designed`
- `running`
- `waiting_user`
- `stopped_cap`
- `blocked`
- `complete`

`worker_dispatch_limit`는 initial task 수와 예상 난이도를 바탕으로 제한값을 제안한다. 비용 민감도가 높거나 외부 비용이 있으면 사용자 확인을 받는다. native goal의 token budget은 사용자가 명시한 경우에만 별도로 설정한다.

`blocker_streak`은 blocked task 수가 아니라 **같은 blocker로 meaningful progress 없이 끝난 연속 native goal turn 수**다. 한 turn에서 여러 task가 같은 이유로 막혀도 한 번만 증가한다. 다른 progress가 생기거나 blocker key가 바뀌면 reset한다.

`artifact_owners`는 예상 write scope가 아니다. evaluator가 승인한 실제 산출물만 기록하므로 initial design에서는 비어 있어야 하고, owner task의 status는 `done` 또는 기존 산출물을 남긴 `superseded`여야 한다.

`last_checkpoint`는 `null` 또는 **그 checkpoint 시점의 마지막 완료 task ID**다. audit report path와 timestamp는 journal event에 기록한다. field에 audit path를 넣지 않는다.

## `tasks/T-NNN.md`

```markdown
# Task T-NNN: <제목>

## Requirement link
- DoD/Scope: <goal.md 항목>

## Acceptance criteria
- [ ] <관찰 가능한 조건> — 검증: <방법>

## Write scope
- <경로 또는 산출물>

## Worker log
- <시도별 변경, 명령, 결과>

## Discoveries for integration
- knowledge 후보: <항구적 사실 또는 없음>
- plan 후보: <추가/분할/정제 제안 또는 없음>
```

초기 acceptance criteria는 design 단계에서 작성한다. worker는 검증을 더 엄격하게 보강할 수 있지만 기존 조건을 약화하거나 삭제할 수 없다. 모순이나 누락을 발견하면 `BOUNCE`로 main에 올린다.

## `knowledge.md`

항구적이고 재사용할 사실, 결정, convention, source pointer, 함정만 유지한다. 오래된 내용을 교체하고 중복을 합쳐 context가 무한히 자라지 않게 한다. 직후 한 번만 필요한 내용은 handoff로 보낸다.

## `journal.md`

append-only다. 각 event는 timestamp, actor, event, task/plan revision, 한 줄 결과, evidence pointer를 가진다.

```markdown
## <ISO-8601> — <event>
- actor: main|worker|evaluator|auditor|user
- task: T-NNN|—
- result: <한 줄>
- evidence: <task/eval/audit/command pointer>
```

기존 event를 다시 쓰지 않는다. 잘못 기록한 경우 correction event를 추가한다.
