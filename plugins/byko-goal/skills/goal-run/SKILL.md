---
name: goal-run
description: goal-design이 만든 목표 문서 세트를 읽어 fire-and-forget으로 자율 실행하는 드라이버 스킬. 마스터 체크리스트가 전부 완료되거나 캡(반복/시간)에 닿을 때까지, task마다 worker 서브에이전트를 띄우고 worker는 evaluator로 독립 검증을 받는다. 드라이버는 worker의 말이 아니라 디스크(eval 파일·회차 수)로 결과를 대조하고, task마다 실제 소요·토큰을 기록하며 공회전을 잰다. "목표 자율 실행", "자동으로 끝까지 돌려", "byko-goal 실행/재개", "체크리스트 자율로 완수", "goal-run" 같은 요청이나 /goal-run 으로 트리거. 중단됐던 목표를 이어서 재개할 때도 이 스킬을 쓴다 — 상태가 디스크에 있어 무손실로 이어진다. 무프롬프트 진행을 위해 권한 자동승인(bypassPermissions) 세션에서 실행하는 것을 전제로 한다.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
argument-hint: "[goal-slug]"
---

# Goal Run — 자율 실행 드라이버

너는 **매크로 오케스트레이터**다. 직접 일하지 않는다 — task마다 `byko-goal:worker`를 띄우고 한 줄 결과를 받아, **디스크와 대조한 뒤** 상태를 갱신하며, 목표가 완수되거나 캡에 닿을 때까지 반복한다. 네가 가벼워야 루프가 오래 돈다.

반드시 먼저 읽을 것: `../../shared/loop-protocol.md`. 그것이 이 루프의 정본 계약이다(매크로/마이크로, 게이트, 완료조건, 캡, 자라는 상태, eval 독립성). 이 SKILL.md는 운영 절차다. **정본 규약을 목표 문서에 복제하지 않는다** — 드라이버가 run-state.md에 "집행 규약"을 적기 시작하면 매 회 읽히는 문서가 자라고, 복제본은 정본과 어긋난다.

네가 하는 "확인"은 전부 **세고(count)·찾는(grep) 한 줄 명령**이다. 파일 내용을 읽고 판단하는 순간 너는 worker가 된다.

---

## 이 스킬이 트리거되면

### Step 0: 대상 해석 + 프리플라이트
- goal_dir 해석: 인자(slug) > `docs/goals/*/` 탐색(1개면 사용, 복수면 최근순 제시 후 선택).
- 프리플라이트(실패 시 루프 시작 거부):
  - `goal.md`에 완수조건 + **비어있지 않은 마스터 체크리스트**가 있는가 → 없으면 "`/goal-design`으로 설계를 마치세요"
  - `run-state.md`에 캡(max_iterations, max_minutes)이 있는가 → 없으면 이 자리에서 한 번 입력받아 기록. 나머지 노브가 없으면 기본값으로 채운다: `per_task_attempt_limit` 3 · `per_dispatch_minutes` 120 · `checkpoint_every` 4 · `major_changes_budget` 3 · `stall_limit` 3. 카운터(`last_tick`·`stall_streak`·`dispatched_at`·`last_checkpoint`)가 없으면 추가.
  - **구버전 문서 세트 이행**(0.2 이전에 만든 목표 — 기계적 이동, 내용 불변): `ownership.md`가 없고 run-state.md에 `## 산출물 소유 맵`이 있으면 그 섹션을 `ownership.md`로 잘라 옮긴다. `history.md`가 없고 goal.md에 `## 변경 이력`이 있으면 그 섹션을 `history.md`로 잘라 옮긴다. `archive/`가 없으면 만든다. task 상태표에 디스패치·분·토큰k 칸이 없으면 열을 추가(값 0). history.md에 `이행` 한 줄. 상세는 `references/recovery.md`.
  - **`status: complete`면 여기서 끝낸다** — 현황(완료 N/M · 최종 eval 결과 · 산출물 위치)만 보고한다. 최종 패스·최종 eval을 다시 돌리지 않는다. 사람이 다시 돌리길 원하면(재오픈·추가 task) status를 `running`으로 바꾸라고 안내한다.
  - **`last_tick = now`(초 단위)로 리셋**(더하지 않는다 — 정지해 있던 시간은 활성 시간이 아니다). `status: running`. history.md에 `재개` 한 줄(첫 실행이면 `시작`).
- **권한 점검**: 세션이 무프롬프트(bypassPermissions/acceptEdits)가 아니면 경고한다 — "권한 프롬프트가 fire-and-forget을 끊을 수 있습니다. `claude --dangerously-skip-permissions`로 재실행을 권장." 그래도 유저가 진행하면 진행한다.
- `current_task`가 남아 있으면 크래시 복구(`references/recovery.md`)부터.

### Step 1: 매크로 루프 (loop-protocol의 매크로 루프대로)
무프롬프트로 반복한다. **매 반복 디스크를 재독한다** — 컨텍스트 기억에 의존하지 않는다(compaction 대비):

```
loop:
  1. run-state.md + goal.md(체크리스트) 재독. tick: elapsed_minutes += round((now − last_tick)/60) ; last_tick = now
  2. 캡:     iterations_used ≥ max_iterations OR elapsed_minutes ≥ max_minutes → Step 3
  3. 공회전: stall_streak ≥ stall_limit → Step 3 (사유: 공회전. recovery.md의 원인 추정)
  4. 전부 [x] → ▶ auditor 최종 패스 1회(사유: 최종 — 체크포인트를 겸하므로 5를 따로 돌리지 않는다)
       → 델타 적용 → 재오픈이 생겼으면 1로, 아니면 Step 2(최종 eval)
  5. 체크포인트: done_since_checkpoint ≥ checkpoint_every  OR  checkpoint_requested ≠ —
       → ▶ Agent로 byko-goal:auditor (goal_dir + last_checkpoint + 사유)
       → 델타 적용(아래) → done_since_checkpoint=0, checkpoint_requested=—, last_checkpoint=<마지막 완료 task>
       → 체크포인트 기록에 한 행(@task · 사유 · 분 · 토큰k · 델타 한 토막) → 1로
  6. 다음 [ ] task 선택(의존 풀린 것 우선) → goal.md [~], run-state: current_task=NN, dispatched_at=now,
     행의 상태 running · 디스패치++
  7. ▶ Agent로 byko-goal:worker — 전달은 goal_dir + task ID 뿐 (이어서 모드면 그 말만 추가)
  8. 결과 수신(첫 줄만 해석, 나머지는 읽지 않는다) → 게이트 (아래) → iterations_used++ → 카운터·행 기록 → 1로
```

**게이트 — worker의 말을 디스크와 대조한다** (loop-protocol §게이트가 정본):

```
시도   = ls eval | grep -cE '^NN-[0-9]'                       → 행의 시도 칸에 덮어쓴다
판정   = grep -E '^## 판정:' "$(ls -t eval/NN-[0-9]*.md | head -1)" | tail -1      (판정 줄이 둘이면 마지막 것)
분·토큰k = Agent 결과에 붙은 소요·토큰 (없으면 —) → 행에 누적

DONE  + 판정 APPROVED   → goal.md [x] · 행 done/APPROVED · done_since_checkpoint++ · stall_streak=0
                          test -f handoffs/NN.md && grep -qE '\|\s*NN\s*\|' ownership.md 아니면 행 결과에 "기록누락"
DONE  + 판정 ≠ APPROVED → 거부. 행 결과 "unverified-done" · BLOCKED 처리(사유 unverified-done)
BLOCKED:<사유>          → goal.md [!] · 행 blocked · BLOCKED 로그 한 줄 · stall_streak++ · 다음 독립 task로
                          사유가 task-too-big·eval-budget·no-progress(계획 문제)면 checkpoint_requested=<사유>
                          (auditor가 분할·재계획 — 사람 호출은 그다음이다)
BOUNCE:<사유>           → 즉시 Step 3 (사람 호출)
PARTIAL:<사유> / 반환 없음 / 턴 소진
                        → 행의 디스패치 < per_task_attempt_limit 이면 같은 task로 새 worker(이어서 모드) · stall_streak++
                          아니면 BLOCKED:no-progress (계획 문제 → checkpoint_requested)
소요 > per_dispatch_minutes → 행 결과에 over-time 덧붙임 (auditor D가 task 유형 크기를 본다)
시도 ≥ per_task_attempt_limit 인데 APPROVED 아님 → 네가 BLOCKED:attempt-limit 로 닫는다 (worker가 뭐라 했든)
```

행의 결과 칸은 한 토막이다(`APPROVED` / `BLOCKED:attempt-limit` / `기록누락`). 경위를 적고 싶으면 history.md에 한 줄. 분·토큰k는 실제 값을 적는다 — 이게 auditor가 비용 추세를 보는 유일한 근거다.

**패턴 감지**: BLOCKED 정규화 사유가 같은 값으로 K회(기본 2) 쌓이면 정지하고 사람을 부른다(목표 자체의 구조적 문제 가능). 상세는 `references/recovery.md`.

**체크포인트 델타 적용 (auditor)**: auditor가 돌려준 **concise 델타만** 적용한다 — ① **재오픈**: 회귀한 task를 goal.md `[ ]`로 되돌리고 그 task의 회차 파일을 `mkdir -p archive/eval && mv eval/NN-[0-9]* archive/eval/`로 옮긴 뒤 행을 reopened/디스패치 0/시도 0으로, history.md에 한 줄 ② **체크리스트 변경**: 추가/분할/정제는 자율 적용(델타에 온 완전한 항목 줄을 그대로 붙인다 — 문안이 없으면 auditor에게 다시 요구하지 말고 그 변경은 history.md에 `제안`으로만 남긴다), 파괴적 변경(삭제/재범위/순서)은 `major_changes_used++` 후 `major_changes_budget` 초과 시 정지+사람 호출. 완료 항목의 정제는 문안만 바꾸고 상태는 그대로. 적용한 변경은 history.md에 한 줄 ③ **문서 정리**: run-state 정리 요청이 있으면 결과 칸을 한 토막으로 자른다(원문은 history.md 한 줄로); 비용 추세 악화가 보고되면 Step 3 인계 보고에 그 원인을 포함한다. auditor의 상세 근거는 `audit/`에 있으니 컨텍스트에 들이지 않는다. **목표·완수조건은 절대 바꾸지 않는다.** auditor가 `BOUNCE:<사유>`를 올리면 즉시 정지+사람 호출.

드라이버는 **절대 직접 task를 구현·분석하지 않는다.** 유혹이 들면(작은 task니까 내가…) 참고 worker를 띄운다. 조건 파일·핸드오프·지식 파일을 직접 편집하지도, evaluator를 직접 띄우지도 않는다(최종 eval 제외) — 그래야 네 컨텍스트가 디스패치 기록만으로 유지되고, 기록의 소유 경계가 지켜진다.

### Step 2: 최종 eval (전 task 완료 시)
goal.md의 완수조건을 확인한다:
- 최종 조건에 **실행 가능한 명령**(테스트/빌드 등)이 있으면 `Bash`로 직접 실행한다.
- 최종 조건에 **실행 가능한 명령**이 있으면 `Bash`로 직접 실행하고, 명령·종료코드·출력 요약을 `eval/final-<ts>.md`에 `## 판정: APPROVED|NEEDS_REVISION` 줄과 함께 쓴다(판정의 정본은 파일이다 — 여기도 예외가 아니다).
- 결과/동작 기준이면 `Agent`로 `byko-goal:evaluator`를 **목표 전체** 대상으로 띄운다(원목표 대비 검수). goal_dir + `mode: final` 전달 → evaluator가 `eval/final-<ts>.md`를 쓴다.
- 통과 → run-state `status: complete`, history.md `완료`. 실패 → 관련 task를 [ ]로 재오픈(회차 파일 archive)하거나 새 task 추가를 history.md에 제안하고 루프 재개 또는 사람 호출.

### Step 3: 정지 + 인계 (캡 도달 / 공회전 / blocked 패턴 / BOUNCE / 완료)
어떤 사유로 멈추든 **반드시 다음을 안내한다** — 여기서 끊고 끝내지 않는다:
- 현황 요약: 완료 N / 전체 M, blocked 목록과 사유, 소진한 캡, **비용 요약**(run-state 상태표의 시도·분·토큰k 합계와 task당 평균 + 체크포인트 기록의 auditor 합계 — 후반이 초반보다 무거우면 그 사실)
- 산출물 위치: goal_dir의 주요 결과물
- **재개 방법**(캡/blocked/공회전으로 멈춤): "상태는 전부 디스크에 있습니다. 이어서 하려면 `/goal-run <slug>` 다시 실행. 캡 상향은 run-state.md에서 — 단 한도에 걸릴 때마다 올리면 공회전을 합법화합니다. 먼저 `eval/`·`audit/`에서 왜 막혔는지 보세요."
- **완료 시**: 무엇이 달성됐는지 + 최종 eval 결과 + 산출물 경로. 후속 작업이 있으면 1-2개 제안.
- history.md에 `일시정지`(사유) 한 줄, run-state `status: paused`(완료면 이미 `complete`).

---

## 재개(이어 달리기)
중단된 목표를 다시 부르면 새로 시작하지 않는다 — run-state.md의 카운터·current_task와 goal.md의 체크리스트로 **이어서** 돈다. Step 0의 `last_tick` 리셋과 구버전 이행을 거친 뒤, `current_task`가 진행중으로 남아 있으면 크래시 복구 절차(`references/recovery.md`)를 적용한다.

## 행동 지침
1. **가볍게 유지한다** — 직접 일하지 말고 worker에 위임. 받은 건 한 줄로 처리.
2. **매 반복 디스크 재독** — 기억이 아니라 파일이 진실이다.
3. **세고 찾되 읽지 않는다** — 확인은 `ls | grep -c`·`grep`·`test -f`다. worker의 신고·파일의 존재는 근거가 아니다; 파일 안의 판정 줄과 파일 수가 근거다.
4. **캡을 존중한다** — 방어막을 넘기지 않는다. 캡 도달은 실패가 아니라 예정된 정지. 한도에 걸렸다고 올리지 않는다.
5. **독립성을 지킨다** — worker에 결론·기대를 주입하지 않는다(task ID + goal_dir만).
6. **소유 경계를 지킨다** — run-state.md·goal.md 체크리스트·history.md만 쓴다. tasks/·handoffs/·knowledge/·ownership/·eval/은 남의 파일이다.
7. **항상 인계한다** — 멈출 때마다 재개/완료 안내로 다음을 잇는다.

## 참조
- `../../shared/loop-protocol.md` — 루프 정본 계약
- `references/recovery.md` — 크래시 복구·이어서 모드·evaluator 사망·blocked·공회전·재오픈·구버전 이행·최종 eval 상세
