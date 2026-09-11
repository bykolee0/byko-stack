# 복구·예외 처리

goal-run 드라이버의 비정상 경로. 정상 루프는 `../../shared/loop-protocol.md`.

## 크래시 복구 (세션이 중간에 죽음)

재개 시 `run-state.current_task`에 값이 남아 있으면, 직전 세션이 그 task 도중에 끊긴 것이다:

1. 회차·디스패치를 **디스크에서** 대조한다: `ls eval | grep -cE '^NN-[0-9]'`와 행의 디스패치 칸. 둘 중 하나라도 `per_task_attempt_limit` 이상이면 worker를 띄우지 않고 `BLOCKED:attempt-limit`/`no-progress`로 닫는다 — 한도 위에서 "이어서"를 넘기면 그 task가 무한히 재개된다.
2. 한도 안이면 같은 task로 **새 worker**를 "이어서 모드"로 띄운다(디스패치++). worker가 판단한다: **이어서**(부분 산출물 보존, 남은 조건만) vs **처음부터**(부분 산출물이 검증 불가·모순). 기본은 이어서.
3. 크래시로 잃은 활성 시간은 세지 않는다(과소 계상 허용). `last_tick`은 Step 0에서 이미 리셋됐다.

## worker 턴 소진 / 반환 없음

worker가 DONE/BLOCKED/BOUNCE 없이 끝났다(maxTurns 소진, 에이전트 오류). 크래시 복구와 같은 경로다 — 디스패치 칸이 한도 안이면 새 worker(이어서 모드), 아니면 `BLOCKED:no-progress`. `stall_streak++`. 환경이 같은 worker의 재개(resume)를 지원해도 **재개 1회 = 디스패치 1회**로 센다 — 재개는 공짜가 아니다.

## dispatch가 오래 돈다 (드라이버가 못 보는 구간)

횟수 캡(회차·디스패치·공회전)은 dispatch가 **끝나야** 센다. dispatch 안에서 worker가 evaluator를 부르지 않은 채 몇 시간을 돌면 — 대개 디스크에 남지 않는 자기 확인의 반복이다 — 드라이버는 반환이 올 때까지 아무것도 보지 못한다. 막는 순서:

1. **1차는 넘김 규칙이다** — 조건이 초록이면 즉시 evaluator, 그 뒤 자기 확인 금지(loop-protocol §검증의 경계, worker.md §3). 이것이 원인 제거다. 규칙은 agents/worker.md에 산다 — 드라이버가 dispatch 문구에 규칙을 즉흥으로 넣는 방식은 빠뜨리는 순간 새므로 쓰지 않는다. 규칙을 지키면 dispatch는 worker의 턴 한도 안에서 끝나고, 턴이 다하면 디스패치 한도까지 이어서 띄운 뒤 auditor가 나눈다.
2. **시간 경계는 작업 범위를 아는 에이전트가 정한다** — `per_dispatch_minutes`는 goal-design이 task 예상 소요 × 2로 시드하고, auditor가 체크포인트마다 이 목표의 실측(완료 task 분 중앙값 × 2)으로 갱신한다. 플러그인 상수도 사람 입력도 아니다 — 얼마나 걸리는 일인지는 목표마다 다르고, 그걸 아는 건 분해한 쪽과 실측을 보는 쪽이다. worker는 `dispatched_at`으로 스스로 지키고, 다 되면 evaluator로 가거나 `PARTIAL:time-budget`으로 상태를 남기고 돌아온다.
3. **드라이버의 백스톱** — 환경이 백그라운드 dispatch와 정지를 지원하면, 시간 예산의 2배가 지나도 반환이 없을 때 디스크(회차 파일 수·산출물 mtime)를 한 줄 명령으로 재고, 진전이 없으면 dispatch를 끊고 이어서 모드로 재디스패치한다(디스패치++).
4. **반환 뒤** — 소요가 예산을 넘긴 dispatch는 행에 `over-time`으로 남는다. 같은 유형의 task가 반복해서 넘기면 auditor D가 그 유형을 미리 나눈다(C). 감시는 탐지일 뿐이고, 원인 제거는 검증의 경계와 task 크기다.

## evaluator 사망 (판정 없는 회차 파일)

worker의 몫이다(worker.md §5) — 드라이버는 개입하지 않는다. 드라이버가 볼 수 있는 흔적: 최신 회차 파일의 판정이 `PENDING`인데 worker가 DONE을 반환했다 → `unverified-done`으로 거부된다(게이트). worker가 `BLOCKED:eval-budget`을 반환하면 그 task의 검증이 한 evaluator에 안 들어온다는 뜻이다 — 다음 체크포인트에서 auditor가 분할(C)한다. 같은 사유가 K회면 패턴 감지가 잡는다(조건 설계 전반의 문제 → 사람).

## unverified-done (worker가 DONE이라는데 디스크는 아니다)

최신 회차 파일이 없거나 판정이 APPROVED가 아닌데 worker가 DONE을 반환한 경우. worker가 스스로 판정했거나(독립성 위반) evaluator 결과를 잘못 읽은 것이다. **DONE을 거부한다**: 행 결과 `unverified-done`, BLOCKED 로그에 `unverified-done`, goal.md `[!]`. 회차·디스패치가 한도 안이면 다음 반복에서 다시 선택돼도 된다(blocked라도 독립 task가 없으면 재시도 가능 — 단 한도는 디스크가 센다). 같은 사유 K회면 사람 호출.

## BLOCKED 처리

worker가 `BLOCKED:<사유>`를 반환하면:
1. goal.md 항목을 `[!]`로, run-state 행을 blocked로, 사유를 BLOCKED 로그에 한 줄(`| NN | <사유> | <ts> |`).
2. 사유가 **계획 문제**(`task-too-big`·`eval-budget`·`no-progress`)면 `checkpoint_requested=<사유>` — 다음 반복에서 auditor가 뜬다. 설계는 가설이고 task가 생각보다 큰 것은 결함이 아니라 정보다: auditor C가 부분 산출물이 살게 나눈다. 사람은 auditor도 못 풀 때 부른다.
3. **다음 독립 task로 진행한다** — 막힌 task에 의존하지 않는 다른 task가 있으면 그것부터. 목표 전체를 막지 않는다.
4. 독립 task가 더 없고 체크포인트도 요청되지 않았으면(남은 게 전부 막힌 task에 의존) 정지하고 사람을 부른다.

정규화 사유별 뜻: `attempt-limit`(회차 소진) · `eval-budget`(검증이 한 evaluator에 안 들어옴 → auditor 분할) · `task-too-big`(worker가 조건을 한 evaluator 안으로 못 접음 → auditor 분할) · `no-progress`(디스패치 소진 — PARTIAL·턴 소진의 반복) · `unverified-done` · `spec-gap:<무엇>`(결정 누락) · `env:<도구>`(환경) · `dep:<task>`(선행 task 미완). `PARTIAL:time-budget`은 BLOCKED가 아니라 이어서 모드의 입력이다.

## 패턴 감지 — 목표 결함의 조기 발견

드라이버는 eval 상세를 보지 않으므로(컨텍스트 절약), BLOCKED **정규화 사유**의 빈도로 구조적 문제를 감지한다:
- 같은 정규화 사유가 K회(기본 2) 누적 → "여러 task가 같은 이유로 막힘 = 목표/계획 자체의 결함 가능"으로 보고 정지 + 사람 호출.
- 서로 다른 task가 같은 누락된 결정(예: 반복되는 `spec-gap:인증 방식 미정`)을 가리키면, 그 결정을 history.md에 `제안`으로 모아 제시한다.
- `attempt-limit`·`eval-budget`·`task-too-big`이 반복되면 문제는 개별 task가 아니라 **조건 설계 습관**이다 — 사람에게 "완료조건이 evaluator 하나에 안 들어오는 크기로 적히고 있다"고 보고한다.
- 상세 근거는 항상 `eval/`·`audit/`에 있으니, 사람은 디스크에서 확인한다.

## Stall 감지 (진전 없는 공회전)

루프가 도는데 완료가 늘지 않는 상황. `stall_streak`(연속 무진전 dispatch 수)가 `stall_limit`(기본 3)에 닿으면 정지하고 보고한다 — 캡을 태우기만 하는 공회전을 막는다. 무진전 = DONE이 수락되지 않은 dispatch(BLOCKED·unverified-done·턴 소진). DONE 수락 시 0으로.

보고에 추정 원인을 적는다 — 흔한 원인: task가 너무 큼(분할 필요), 완료조건이 evaluator 하나에 안 들어옴(조건 과분할), 완료조건이 모호(검증 불가), 환경 문제(빌드/도구 미설치), **기록만 도는 공회전**(산출물은 안 바뀌고 문서만 갱신되는 것 — `git status`/최근 변경 파일 수로 확인 가능). 사람이 원인을 고친 뒤 `stall_streak`를 0으로 되돌리고 재개한다.

## 비용 추세 악화 (auditor D가 보고)

auditor가 "task당 비용이 오르고 있다"고 델타에 적으면 드라이버가 할 일은 없다 — 처방(정리·정제)은 auditor가 이미 적용했거나 C 델타로 왔다. 드라이버는 Step 3 인계 보고에 원인 한 토막을 포함해 사람이 볼 수 있게 한다. 같은 원인이 두 체크포인트 연속 보고되면 사람 호출(하네스가 못 고치는 원인일 수 있다 — 예: task 유형 자체가 무거움, 도구 환경).

## 체크포인트 (B 회귀 + C 재검증 + D 문서 정리) 처리

`done_since_checkpoint ≥ checkpoint_every`(또는 최종 eval 직전)이면 드라이버가 `byko-goal:auditor`를 띄운다. 전달은 `goal_dir` + `last_checkpoint` + 호출 사유뿐 — auditor가 전체 상태를 디스크에서 추적한다. 드라이버는 돌려받은 **concise 델타만** 적용한다:

- **재오픈**: auditor가 회귀로 지목한 완료 task를 goal.md `[ ]`로 되돌리고, `mkdir -p archive/eval && mv eval/NN-[0-9]* archive/eval/`(새 라운드 — 시도·디스패치 0, 상태 reopened), history.md에 한 줄. 재오픈된 task는 일반 task처럼 다시 루프에 들어간다.
- **체크리스트 추가/분할/정제**: 자율 적용 — 델타의 완전한 항목 줄을 마스터 체크리스트에 붙이고 history.md에 한 줄. 분할로 생긴 새 task는 `[ ]`로, 원래 task는 분할 뒤 남는 것이 없으면 정제(문안 교체)로 처리한다. 완료 항목의 정제는 문안만.
- **체크리스트 파괴적 변경(삭제/재범위/순서)**: `major_changes_used++` 후 `major_changes_budget`(기본 3) 초과 시 **정지+사람 호출**(목표 표류 방지). 초과 안 하면 적용하고 history.md에 `major`로 표시.
- **문서 정리**: run-state 결과 칸 정리 요청 → 칸을 한 토막으로 자른다(원문은 history.md 한 줄로).
- 적용 후 `done_since_checkpoint=0`, `checkpoint_requested=—`, `last_checkpoint=<마지막 완료 task>`, 체크포인트 기록에 한 행(@task · 사유 · 분 · 토큰k · 델타 한 토막). auditor 상세는 `audit/NN-<ts>.md`에 있으니 드라이버 컨텍스트에 들이지 않는다. 최종 패스는 체크포인트를 겸한다 — 마지막 task 완료와 주기가 겹쳐도 auditor는 한 번이다.

auditor가 `BOUNCE:<목표결함>`을 올리면 BOUNCE 처리와 동일하게 즉시 정지+사람 호출한다. **목표·완수조건은 어떤 경우에도 드라이버/auditor가 바꾸지 않는다 — 고정 계약이다.**

## 표적 회귀 (A) — per-task

체크포인트(B)는 주기적 안전망이고, 1차 방어는 매 task의 evaluator다: task N의 evaluator가 `ownership.md`를 보고 N이 건드린 이전 task의 영향 조건을 함께 검증한다. 회귀가 나오면 worker가 **이번 task 안에서** 고친다 — 그래서 대부분의 회귀는 체크포인트까지 가기 전에 잡힌다. 소유 맵이 비거나 부정확하면 A가 약해지므로, 게이트가 `기록누락`을 표시하고 auditor D-5가 보정한다.

## BOUNCE 처리 (목표 결함)

worker가 `BOUNCE:<목표결함>`을 반환하면(조건 모순, 결정 누락으로 방향 불가, 구조적 불가능):
- 즉시 정지한다. 자율 루프가 풀 수 없는 문제다.
- history.md에 `BOUNCE` 한 줄로 기록하고, 사람에게 "`/goal-design`으로 목표 보완이 필요"라고 안내한다.
- 계획을 드라이버가 마음대로 바꾸지 않는다 — 구조적 재계획은 사람의 몫이다.

## 최종 eval 상세

전 task [x] 후(auditor 최종 패스 뒤):
- 완수조건의 최종 조건이 **실행 가능 명령**이면 `Bash`로 실행하고, 명령·종료코드·출력 요약을 `eval/final-<ts>.md`에 `## 판정:` 줄과 함께 쓴다.
- **결과/동작 기준**이면 `byko-goal:evaluator`를 목표 전체 대상으로 1회 띄운다 — goal_dir + `mode: final` 전달, "원목표(goal.md) 대비 전체가 충족되는가"를 검수하게 한다 → evaluator가 `eval/final-<ts>.md`를 쓴다.
- 통과 → run-state `status: complete` + history.md `완료`. 이후 `/goal-run <slug>`는 보고만 한다(비멱등 재실행 방지).
- 부분 실패 시: 모든 task가 [x]여도 목표가 미충족일 수 있다. 부족분을 새 task로 추가 제안하거나 관련 task를 재오픈(회차 파일 archive)하고, 캡이 남았으면 루프를 재개한다.

## 캡 상향 후 재개

캡 도달로 멈춘 뒤 유저가 더 돌리길 원하면: `run-state.md`의 `max_iterations`/`max_minutes`를 올리고 `/goal-run <slug>`. 카운터는 보존되므로 누적 기준으로 이어진다(유저가 카운터를 리셋하지 않는 한). `per_task_attempt_limit`은 한도에 걸린 task가 있다고 올리지 않는다 — 그 task의 `eval/`을 먼저 보고, 조건 설계를 고치는 것이 맞다. 한도를 올리는 것은 공회전에 허가를 주는 것이다.

## 구버전 문서 세트 이행 (0.2 이하 → 0.3)

0.2 이하에서 만든 목표를 재개할 때 Step 0에서 한 번만, 기계적으로(내용을 해석하지 않고 잘라 옮긴다):

| 조건 | 동작 |
|---|---|
| `ownership.md` 없음 + run-state.md에 `## 산출물 소유 맵` | 그 섹션(표)을 `ownership.md`로 이동. 칸 형식은 손대지 않는다 — auditor D가 다음 체크포인트에 정리한다 |
| `history.md` 없음 + goal.md에 `## 변경 이력` | 그 섹션을 `history.md`로 이동 |
| run-state.md에 "규약"·"집행 규칙" 섹션 | 그대로 둔다(내용 판단은 auditor D-3). 델타로 정리된다 |
| `archive/` 없음 | 생성 |
| 노브·카운터 누락 | 기본값으로 추가 (`status: running` · `checkpoint_requested: —` · 체크포인트 기록 표 포함). `per_dispatch_minutes`는 `—`로 두고 첫 체크포인트에서 auditor가 실측으로 채운다 |
| task 상태표에 디스패치·분·토큰k 칸 없음 | 열 추가(0) |
| 미완 task(pending/blocked/running)에 0.2식 회차 파일이 있음 | 0.2의 쪼개기 이름(`NN-partA`·`NN-c1c4`·`06a-…`)은 셀 수 없다. 미완 task의 `eval/NN*` 전부를 `archive/eval/`로 옮기고 라운드를 새로 시작한다(시도·디스패치 0). 완료 task의 파일은 그대로 둔다 |

history.md에 `이행 · 0.2→0.3 · <옮긴 것>` 한 줄. 이행은 되돌릴 수 있다(옮긴 것뿐이다).
