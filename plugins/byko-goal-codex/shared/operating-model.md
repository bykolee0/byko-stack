# Codex goal 운영 모델

## 세 층

1. **Codex native goal**은 여러 turn에 걸친 지속 실행과 pause/resume/complete 상태를 담당한다.
2. **main orchestrator**는 사용자 대화, task 선택, subagent lifecycle, plan 변경, authoritative state 갱신을 담당한다.
3. **일회용 subagent**는 경계가 명확한 work, 독립 eval, checkpoint audit를 수행한다.

chat context는 편의를 위한 cache일 뿐이다. 재개에 필요한 정본은 `docs/goals/<slug>/`에 둔다.

## 역할

| 역할 | 책임 | authoritative goal state write |
| --- | --- | --- |
| main orchestrator | task claim, 상태 전이, plan revision, 사용자 보고, 최종 통합 | 허용 |
| worker | task 범위의 실제 산출물 변경과 focused verification | 금지 |
| evaluator | task 조건과 영향받은 과거 조건을 독립적으로 반증 | eval report만 허용 |
| auditor | 회귀와 남은 plan의 타당성을 checkpoint에서 검토 | audit report만 허용 |
| explorer | 넓은 read-only 조사 | 금지 |

worker가 자기 task를 `done`으로 만들 수 없다. main이 fresh evaluator의 `APPROVED`를 확인한 뒤에만 상태를 전이한다.

## 고정 계약과 가변 경로

- `goal.md`의 목표, scope, non-goals, Definition of Done, authorization boundary는 고정 계약이다.
- 계약 변경은 사용자 승인과 `contract_version` 증가가 필요하다.
- `plan.md`의 task graph는 실행 중 발견에 따라 바뀔 수 있다.
- 기존 task ID를 삭제하거나 재사용하지 않는다. 불필요해진 task는 `superseded`로 남겨 history를 보존한다.

### 자율 적용 가능한 plan 변경

- pending task의 조건을 더 명확하게 한다.
- 한 task를 scope 합이 같은 여러 task로 분할한다.
- dependency가 허용하는 범위에서 pending task 순서를 바꾼다.
- 현재 DoD를 충족하는 데 빠진 bounded task를 추가한다.
- 이미 다른 산출물로 충족된 pending task를 근거와 함께 `superseded` 처리한다.

### 사용자 승인이 필요한 변경

- 목표, DoD, scope, non-goals, authorization boundary를 바꾼다.
- acceptance coverage나 결과물을 줄인다.
- 새 외부 dependency, 비용, 공개 또는 destructive action을 도입한다.
- in-progress/done task의 의미를 소급 변경한다.

## 독립 eval

evaluator에게는 `goal_dir`, `task ID`, role instruction 위치만 준다. worker의 설명, 예상 verdict, 수정 제안은 주입하지 않는다. evaluator는 goal 문서와 실제 diff, 명령 결과, 산출물을 직접 읽는다.

## 병렬성

read-only 탐색은 적극적으로 병렬화할 수 있다. write worker는 다음 조건을 모두 만족할 때만 병렬화한다.

- dependency가 서로 독립이다.
- `write_scope`가 겹치지 않는다.
- shared generated file, schema, lockfile, migration, 전역 config를 함께 건드리지 않는다.
- main이 각 worker에게 소유 경계를 명시한다.

조건이 애매하면 writer는 하나씩 실행한다. evaluator와 auditor는 대상 write가 끝난 뒤 fresh context로 실행한다.

## 종료

native goal은 실제 DoD를 모두 통과하고 남은 required work가 없을 때만 `complete`로 만든다. 같은 blocker로 세 번 연속 진행하지 못했고 독립적으로 할 수 있는 work도 없을 때만 `blocked`로 만든다. cap 도달, 어려움, 미완료만으로 complete/blocked 처리하지 않는다.
