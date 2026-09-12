# 복구·예외 처리

goal-run 드라이버의 비정상 경로. 정상 루프·게이트·델타 적용의 정본은 `../../shared/loop-protocol.md`, 명령은 `../SKILL.md` — 여기서는 되풀이하지 않고 **예외에서 무엇이 다른가**만 적는다.

## 크래시 복구 (세션이 중간에 죽음)

재개 시 `run-state.current_task`에 task ID가 남아 있으면, 직전 세션이 그 task 도중에 끊긴 것이다:

1. **먼저 디스크의 판정을 본다** — 그 task의 마지막 회차 파일이 APPROVED면 worker는 기록 마감 중에 죽은 것이다. DONE으로 수락한다(SKILL §게이트 명령의 DONE+APPROVED 처리, 마감 확인 포함). 완료된 task를 다시 돌리거나 BLOCKED로 뒤집지 않는다.
2. 아니면 회차·디스패치를 **디스크에서** 대조한다. 둘 중 하나라도 한도 이상이면 worker를 띄우지 않고 게이트의 "시도 ≥ 한도" 규칙대로 닫는다 — 한도 위에서 "이어서"를 넘기면 그 task가 무한히 재개된다.
3. 한도 안이면 재디스패치 대기로 둔다 — 7단계가 같은 task를 **새 worker**로 "이어서 모드" 띄운다(dispatched_at 갱신·디스패치++). worker가 판단한다: **이어서**(부분 산출물 보존, 남은 조건만) vs **처음부터**(부분 산출물이 검증 불가·모순). 기본은 이어서.
4. 크래시로 잃은 활성 시간은 세지 않는다(과소 계상 허용). `last_tick`은 Step 0에서 이미 리셋됐다. `current_task`가 ID가 아니라 문장이면(구버전) `—`로 본다.

## 재디스패치 대기 (PARTIAL · 턴 소진 · unverified-done · 백스톱으로 끊음)

worker가 끝났지만 task는 끝나지 않았고, 계획 문제도 아니다. 행은 running·goal.md는 `[~]`로 남고, 다음 반복 7단계가 같은 task를 이어서 모드로 다시 띄운다. 디스패치 한도에 닿으면 `BLOCKED:no-progress` — 이건 계획 문제(task가 이 크기로는 안 끝난다)라 `checkpoint_requested`가 되고 auditor가 나눈다. 환경이 같은 worker의 재개(resume)를 지원해도 **재개 1회 = 디스패치 1회**로 센다.

- **PARTIAL:time-budget**은 실패가 아니다 — stall_streak을 올리지 않는다. 진행 상태는 tasks/NN.md 작업 노트에 있다.
- **unverified-done**은 worker가 스스로 판정했거나(독립성 위반) evaluator 결과를 잘못 읽은 것이다. BLOCKED 로그에 남겨 패턴 감지에 넣되, task는 재디스패치 대기다 — 새 worker가 eval 파일을 보고 고친다.
- **턴 소진·끊음**은 stall_streak++.

## dispatch가 오래 돈다 (드라이버가 못 보는 구간)

횟수 캡(회차·디스패치·공회전)은 dispatch가 **끝나야** 센다. dispatch 안에서 worker가 evaluator를 부르지 않은 채 몇 시간을 돌면 — 대개 디스크에 남지 않는 자기 확인의 반복이다 — 드라이버는 반환이 올 때까지 아무것도 보지 못한다. 세 겹:

1. **원인 제거는 넘김 규칙이다** — 조건이 초록이면 즉시 evaluator, 그 뒤 자기 확인 금지(loop-protocol §검증의 경계, worker.md §3). 규칙은 agents/worker.md에 산다 — 드라이버가 dispatch 문구에 규칙을 즉흥으로 넣는 방식은 빠뜨리는 순간 새므로 쓰지 않는다.
2. **시간 경계는 작업 범위를 아는 에이전트가 정한다** — `per_dispatch_minutes`는 goal-design이 task 예상 소요 × 2로 시드하고, auditor가 체크포인트마다 이 목표의 실측(완료 task의 dispatch당 소요 중앙값 × 2)으로 갱신한다. worker는 `dispatched_at`으로 스스로 지키고, 다 되면 evaluator로 가거나 `PARTIAL:time-budget`으로 상태를 남기고 돌아온다.
3. **드라이버의 백스톱** — worker의 자기 신고에만 맡기지 않는다. 지원 환경(Claude Code: Agent `run_in_background` + `TaskStop`)에서는 기본으로 SKILL §백스톱 명령을 돌린다: 예산×2 뒤 회차 파일 수·산출물 mtime이 그대로면 끊고 "끊음"으로 게이트. 미지원 환경이면 worker maxTurns가 마지막 상한이고 인계 보고에 그 사실을 적는다.

반환 뒤 소요가 예산을 넘긴 dispatch는 행에 `over-time`으로 남는다. 같은 유형의 task가 반복해서 넘기면 auditor D가 그 유형을 미리 나눈다(C). 감시는 탐지일 뿐이고, 원인 제거는 검증의 경계와 task 크기다.

## evaluator 사망 (판정 없는 회차 파일)

worker의 몫이다(worker.md §5) — 드라이버는 개입하지 않는다. 드라이버가 볼 수 있는 흔적: 마지막 회차 판정이 `PENDING`인데 worker가 DONE을 반환했다 → `unverified-done`. worker가 `BLOCKED:eval-budget`을 반환하면 그 task의 검증이 한 evaluator에 안 들어온다는 뜻이다 — 계획 문제라 체크포인트에서 auditor가 분할(C)한다.

## BLOCKED 처리

worker가 `BLOCKED:<사유>`를 반환하면 게이트대로 `[!]`·blocked·로그·stall++ 하고:
1. 사유가 **계획 문제**(`task-too-big`·`eval-budget`·`no-progress`)면 `checkpoint_requested=<사유>` — 다음 반복 3단계에서 auditor가 뜬다(공회전 판정보다 먼저). 설계는 가설이고 task가 생각보다 큰 것은 결함이 아니라 정보다: auditor C가 부분 산출물이 살게 나눈다. 사람은 auditor도 못 풀 때 부른다.
2. **다음 독립 task로 진행한다** — 막힌 task에 의존하지 않는 다른 task가 있으면 그것부터. 목표 전체를 막지 않는다.
3. 독립 task가 더 없고 체크포인트도 요청되지 않았으면(남은 게 전부 막힌 task에 의존) 정지하고 사람을 부른다.

정규화 사유별 뜻: `attempt-limit`(회차 소진) · `eval-budget`(검증이 한 evaluator에 안 들어옴 → 분할) · `task-too-big`(worker가 조건을 한 evaluator 안으로 못 접음 → 분할) · `no-progress`(디스패치 소진 → 분할) · `spec-gap:<무엇>`(결정 누락) · `env:<도구>`(환경) · `dep:<task>`(선행 task 미완). `unverified-done`은 로그에만 남는 사유다(task는 재디스패치 대기).

## 패턴 감지 — 목표 결함의 조기 발견

드라이버는 eval 상세를 보지 않으므로(컨텍스트 절약), BLOCKED **정규화 사유**의 빈도로 구조적 문제를 감지한다:
- 같은 정규화 사유가 K회(기본 2) 누적 → "여러 task가 같은 이유로 막힘 = 목표/계획 자체의 결함 가능"으로 보고 정지 + 사람 호출.
- 서로 다른 task가 같은 누락된 결정(예: 반복되는 `spec-gap:인증 방식 미정`)을 가리키면, 그 결정을 history.md에 `제안`으로 모아 제시한다.
- **계획 문제 사유는 K에 세지 않는다** — 체크포인트가 처리한다. 대신 같은 task(또는 그 분할 자식 `NNa`…)가 두 번째로 계획 문제로 막히면 사람을 부른다: auditor가 나눠도 안 끝나는 task는 하네스 밖의 문제다.
- 상세 근거는 항상 `eval/`·`audit/`에 있으니, 사람은 디스크에서 확인한다.

## Stall 감지 (진전 없는 공회전)

`stall_streak`(연속 무진전 dispatch 수)가 `stall_limit`(기본 3)에 닿으면 정지하고 보고한다 — 캡을 태우기만 하는 공회전을 막는다. 무진전 = BLOCKED·unverified-done·턴 소진·끊음. PARTIAL은 진행 중이라 세지 않는다. DONE 수락과 체크포인트(auditor가 손을 댔다)에서 0으로. 요청된 체크포인트(3단계)가 공회전 판정(4단계)보다 앞이라, 계획 문제로 막힌 task는 정지되기 전에 auditor가 나눈다.

보고에 추정 원인을 적는다 — 흔한 원인: 완료조건이 모호(검증 불가), 환경 문제(빌드/도구 미설치), **기록만 도는 공회전**(산출물은 안 바뀌고 문서만 갱신되는 것 — `git status`/최근 변경 파일 수로 확인 가능). 사람이 원인을 고친 뒤 `stall_streak`를 0으로 되돌리고 재개한다.

## 비용 추세 악화 (auditor D가 보고)

auditor가 "task당 비용이 오르고 있다"고 델타에 적으면 처방(정리·정제)은 auditor가 이미 적용했거나 C 델타로 왔다. 드라이버는 Step 3 인계 보고에 원인 한 토막을 포함한다. 같은 원인이 두 체크포인트 연속 보고되면 사람 호출(하네스가 못 고치는 원인일 수 있다 — 예: task 유형 자체가 무거움, 도구 환경).

## 체크포인트와 델타 적용

트리거(요청·주기·최종)와 델타 적용은 SKILL §Step 1이 명령으로, loop-protocol §회귀 방지가 의미로 정한다. 여기서 되풀이하지 않는다. 예외만:
- auditor가 `BOUNCE:<목표결함>`을 올리면 즉시 정지+사람 호출. **목표·완수조건은 어떤 경우에도 드라이버/auditor가 바꾸지 않는다 — 고정 계약이다.**
- 델타에 체크리스트 변경의 완전한 문안이 없으면 적용하지 않고 history.md에 `제안`으로만 남긴다(auditor에게 되묻지 않는다 — 다음 체크포인트가 다시 낸다).

## BOUNCE 처리 (목표 결함)

worker가 `BOUNCE:<목표결함>`을 반환하면(조건 모순, 결정 누락으로 방향 불가, 구조적 불가능):
- 즉시 정지한다. 자율 루프가 풀 수 없는 문제다.
- history.md에 `BOUNCE` 한 줄로 기록하고, 사람에게 "`/goal-design`으로 목표 보완이 필요"라고 안내한다.
- 계획을 드라이버가 마음대로 바꾸지 않는다 — 구조적 재계획은 사람의 몫이다.

## 캡 상향 후 재개

캡 도달로 멈춘 뒤 유저가 더 돌리길 원하면: `run-state.md`의 `max_iterations`/`max_minutes`를 올리고 `/goal-run <slug>`. 카운터는 보존되므로 누적 기준으로 이어진다(유저가 카운터를 리셋하지 않는 한). `per_task_attempt_limit`은 한도에 걸린 task가 있다고 올리지 않는다 — 그 task의 `eval/`을 먼저 보고, 조건 설계를 고치는 것이 맞다. 한도를 올리는 것은 공회전에 허가를 주는 것이다.

## 구버전 문서 세트 이행 (0.2 이하 → 0.3)

0.2 이하에서 만든 목표를 재개할 때 Step 0에서 한 번만, **기계적으로**(내용을 해석하지 않고 잘라 옮긴다). 이 표가 정본이다. 전부 이동이라 되돌릴 수 있다.

| 조건 | 동작 |
|---|---|
| run-state.md에 `## 산출물 소유 맵` 섹션이 있음 (ownership.md 존재 여부와 무관 — 혼합 버전으로 다시 생길 수 있다) | 그 표의 행을 `ownership.md`에 병합(없으면 생성)하고 섹션을 제거. 칸 형식은 손대지 않는다 — auditor D가 다음 체크포인트에 정리한다 |
| goal.md에 `## 변경 이력` 섹션이 있음 | `history.md`로 이동(없으면 생성) |
| run-state.md에 templates.md의 섹션(캡·노브 / 카운터 / task 상태 / 체크포인트 기록 / BLOCKED 사유 로그) 외의 `## ` 섹션이 있음 — "규약"·"집행 규칙"·"초과 기록"·"일시정지 기록" 등 | `archive/run-state-0.2-<ts>.md`로 통째로 이동하고 history.md에 포인터 한 줄. 매 회 읽히는 파일에 규약 복제를 남기지 않는다 |
| `archive/` 없음 | 생성 |
| 노브·카운터·표 누락 | templates.md 기본값으로 추가. `status`: 체크리스트에 `[ ]`·`[~]`·`[!]`가 없고(전부 [x]) 완료 흔적(`eval/final-*` 또는 최종 audit·완료 문구)이 있으면 `complete`, 아니면 `running`. `current_task`가 task ID가 아니면 `—`. `per_dispatch_minutes`는 `—`(첫 체크포인트에서 auditor가 실측으로 채운다) |
| task 상태표에 디스패치·분·토큰k 칸 없음 | 열 추가 — 값은 `—`(0이 아니다: 0은 실측이고 `—`는 결측이라 auditor가 표본에서 뺀다). `시도` 칸이 산문이면 회차 파일 수로 재계산 |
| `elapsed_minutes`가 벽시계 기준일 수 있음(0.2는 정의가 없었다) | `paused_minutes` 같은 정지 회계가 있으면 뺀다. 없으면 그대로 두고 history.md에 "0.2 elapsed는 벽시계 기준일 수 있음 — 캡이 일찍 닿으면 사람이 상향" 한 줄 |
| 미완 task(pending/blocked/running)에 0.2식 회차 파일이 있음 | 0.2의 쪼개기 이름(`NN-partA`·`NN-c1c4`·`06a-…`)은 셀 수 없다. 미완 task NN의 `eval/NN-*` 파일을 `archive/eval/`로 옮기고 라운드를 새로 시작한다(시도·디스패치 0). 글롭은 `NN-*`만 — `NNa-*`는 체크리스트에 있는 별도 task의 것이다. 완료 task의 파일은 그대로 둔다 |

history.md에 `이행 · 0.2→0.3 · <옮긴 것>` 한 줄. 이행 뒤 첫 체크포인트에서 auditor D가 ownership 칸·knowledge 정리와 `per_dispatch_minutes` 실측을 한다.

**혼합 버전 주의**: 0.2 플러그인 캐시가 남은 세션이 같은 goal_dir을 돌리면 run-state.md에 소유 맵을 다시 만든다. 그래서 이행 표의 첫 행은 ownership.md가 있어도 적용된다. 같은 goal_dir을 두 드라이버가 동시에 돌리는 것은 어떤 버전에서도 지원하지 않는다.
