---
name: goal-run
description: goal-design이 만든 목표 문서 세트를 읽어 fire-and-forget으로 자율 실행하는 드라이버 스킬. 마스터 체크리스트가 전부 완료되거나 캡(반복/시간)에 닿을 때까지, task마다 worker 서브에이전트를 띄우고 worker는 evaluator로 독립 검증을 받는다. 드라이버는 worker의 말이 아니라 디스크(eval 파일·회차 수)로 결과를 대조하고, task마다 실제 소요·토큰을 기록하며 공회전을 잰다. "목표 자율 실행", "자동으로 끝까지 돌려", "byko-goal 실행/재개", "체크리스트 자율로 완수", "goal-run" 같은 요청이나 /goal-run 으로 트리거. 중단됐던 목표를 이어서 재개할 때도 이 스킬을 쓴다 — 상태가 디스크에 있어 무손실로 이어진다. 무프롬프트 진행을 위해 권한 자동승인(bypassPermissions) 세션에서 실행하는 것을 전제로 한다.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, TaskStop
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
  - `run-state.md`에 캡(max_iterations, max_minutes)이 있는가 → 없으면 이 자리에서 한 번 입력받아 기록.
  - **구버전 문서 세트 이행** — 0.2 이전에 만든 목표는 `references/recovery.md` §이행 표대로 기계적으로 옮긴다(내용 판단 없음). 그 표가 정본이다.
  - `templates.md`의 run-state.md에 있는 노브·카운터·표(체크포인트 기록 포함)가 없으면 템플릿의 기본값으로 추가한다 — 드라이버가 값을 지어내지 않는다(`per_dispatch_minutes`는 없으면 `—`, 첫 체크포인트에서 auditor가 실측으로 채운다).
  - **`status: complete`면 여기서 끝낸다** — 현황(완료 N/M · 최종 eval 결과 · 산출물 위치)만 보고한다. 최종 패스·최종 eval을 다시 돌리지 않는다. 사람이 다시 돌리길 원하면(재오픈·추가 task) status를 `running`으로 바꾸라고 안내한다.
  - **`last_tick = now`(`date '+%F %T'`)로 리셋**(더하지 않는다 — 정지해 있던 시간은 활성 시간이 아니다). `status: running`. history.md에 `재개` 한 줄(첫 실행이면 `시작`). goal.md 헤더의 `last_updated`는 드라이버가 상태를 바꿀 때 갱신한다.
- **권한 안내**: 드라이버는 세션의 권한 모드를 스스로 확인할 수 없다. 시작 보고에 한 줄 적는다 — "무프롬프트 세션(bypassPermissions)이 아니면 권한 프롬프트가 fire-and-forget을 끊을 수 있습니다. `claude --dangerously-skip-permissions`로 재실행을 권장." 그리고 진행한다.
- `current_task`에 task ID가 남아 있으면 크래시 복구(`references/recovery.md`)부터 — 그 task의 마지막 회차가 APPROVED면 DONE으로 수락, 아니면 재디스패치 대기로.

### Step 1: 매크로 루프
순서와 의미의 정본은 `loop-protocol.md` §매크로 루프·§게이트다 — 여기는 그것을 **명령으로 옮긴 것**이고, 둘이 다르면 정본을 따르고 이 파일을 고친다. 무프롬프트로 반복하고 **매 반복 디스크를 재독한다** — 컨텍스트 기억에 의존하지 않는다(compaction 대비):

```
loop:
  1. run-state.md + goal.md(체크리스트) 재독. tick: elapsed_minutes += round((now − last_tick)/60) ; last_tick = now
  2. 캡:     iterations_used ≥ max_iterations OR elapsed_minutes ≥ max_minutes → Step 3
  3. 요청된 체크포인트: checkpoint_requested ≠ — → ▶ auditor(goal_dir + last_checkpoint + 사유) → 델타 적용
       → stall_streak=0 · checkpoint_requested=— · done_since_checkpoint=0 · last_checkpoint=<마지막 완료 task>
       → 체크포인트 기록에 한 행 → 1로
  4. 공회전: stall_streak ≥ stall_limit → Step 3 (사유: 공회전)
  5. 전부 [x] → ▶ auditor 최종 패스(사유: 최종 — 체크포인트 겸: 3과 같은 델타 적용·리셋·체크포인트 기록 행)
       → 재오픈·항목 추가가 있으면 1로, 없으면 Step 2(최종 eval)
  6. 주기 체크포인트: done_since_checkpoint ≥ checkpoint_every → 3과 같이 → 1로
  7. 선택: current_task가 재디스패치 대기(행 running, goal.md [~])면 그 task를 이어서 모드로;
     아니면 다음 [ ] task(의존 풀린 것 우선) → goal.md [~] · current_task=NN
     → dispatched_at=now · 행 running · 디스패치++  (재디스패치도 여기서 — 시계와 카운트를 갱신한다)
  8. ▶ Agent로 byko-goal:worker — 전달은 goal_dir + task ID 뿐 (이어서 모드면 그 말만 추가)
     백스톱(지원 환경): 백그라운드로 띄우고 per_dispatch_minutes×2 뒤 깨어난다(§백스톱 명령)
  9. 결과 수신(첫 줄만 해석) → §게이트 명령 → iterations_used++ → 재디스패치 대기가 아니면 current_task=— · dispatched_at=— → 1로
```

#### 게이트 명령 (goal_dir에서, NN = task ID)

```
시도   : ls eval | grep -cE "^NN-[0-9]"                                  → 행의 시도 칸에 덮어쓴다
판정   : grep -E '^## 판정' "$(ls eval/NN-[0-9]*.md | sort | tail -1)" | tail -1 | grep -c APPROVED   (1이면 APPROVED)
         (이름순 마지막 = 최신 회차. 파일이 없으면 APPROVED 아님)
마감   : test -f handoffs/NN.md && grep -qE "\|\s*NN\s*\||공유:[^|]*\bNN\b" ownership.md      (아니면 기록누락)
분·토큰k: Agent 결과에 붙은 소요·토큰 → 행에 누적. 소요 > per_dispatch_minutes → 결과 칸에 over-time

DONE + APPROVED    → goal.md [x] · 행 done/APPROVED · done_since_checkpoint++ · stall_streak=0 · (마감 실패면 결과 칸 "기록누락")
DONE + APPROVED 아님 → 결과 칸 "unverified-done" · BLOCKED 로그 한 줄 · stall_streak++ · 재디스패치 대기
BLOCKED:<사유>      → goal.md [!] · 행 blocked · BLOCKED 로그 한 줄 · stall_streak++ · current_task=—
                      사유가 task-too-big·eval-budget·no-progress 면 checkpoint_requested=<사유>
PARTIAL:<사유>      → 결과 칸 "PARTIAL:<사유>" · history.md 한 줄 · stall_streak 그대로 · 재디스패치 대기
BOUNCE:<사유>       → 즉시 Step 3 (사람 호출)
반환 없음·턴 소진·끊음 → stall_streak++ · 재디스패치 대기

재디스패치 대기     : 행의 디스패치 < per_task_attempt_limit 이면 current_task·[~] 유지(7단계가 다시 띄운다)
                      아니면 BLOCKED:no-progress → checkpoint_requested=no-progress
시도 ≥ per_task_attempt_limit 인데 APPROVED 아님
                    → worker가 계획 문제 사유(eval-budget·task-too-big)로 BLOCKED를 냈으면 그 사유 유지(체크포인트로),
                      아니면 BLOCKED:attempt-limit 로 닫는다
```

#### 백스톱 명령 (환경이 백그라운드 dispatch·타이머·정지를 지원할 때 — Claude Code면 Agent 백그라운드 + `Monitor`(persistent) 타이머 + `TaskStop`)

```
dispatch 직후: 기준값 = (ls eval | grep -cE "^NN-[0-9]") 와 산출물 경로의 최신 mtime. 예산×2 분 뒤 깨우는 타이머를 건다.
깨어나면:      worker가 이미 끝났으면 타이머를 끄고 평소대로 게이트. 아니면 같은 두 값을 다시 잰다.
               둘 다 그대로면 → 끊는다(TaskStop) → "끊음"으로 게이트.
               하나라도 변했으면 예산×1 만큼 더 기다린 뒤 한 번만 더 잰다.
```
타이머 수단은 환경에 있는 것을 쓴다(Claude Code: `Monitor`는 60분 넘는 대기에 `persistent: true`가 필요하다). 지원하지 않는 환경이면 worker maxTurns가 마지막 상한이고, 인계 보고에 그 사실을 적는다.

행의 결과 칸은 한 토막이다(`APPROVED` / `BLOCKED:attempt-limit` / `PARTIAL:time-budget` / `기록누락` / `over-time`). 경위는 history.md에 한 줄. 분·토큰k는 실제 값을 적는다 — auditor가 비용 추세와 시간 예산을 보는 유일한 근거다.

**패턴 감지**: BLOCKED 정규화 사유가 같은 값으로 K회(기본 2) 쌓이면 정지하고 사람을 부른다(목표 자체의 구조적 문제 가능). 계획 문제 사유(task-too-big·eval-budget·no-progress)는 체크포인트로 가고, 같은 task(또는 그 분할 자식)가 두 번째로 계획 문제로 막힐 때만 사람을 부른다. 상세는 `references/recovery.md`.

**체크포인트 델타 적용 (auditor)**: auditor가 돌려준 **concise 델타만** 적용한다 — 의미의 정본은 `loop-protocol.md` §회귀 방지 "드라이버의 델타 적용". 명령으로는:
- **재오픈**: goal.md 항목을 `[ ]`로, `mkdir -p archive/eval && mv eval/NN-[0-9]* archive/eval/`, 행 reopened/디스패치 0/시도 0, history.md 한 줄.
- **분할**: 원 항목 줄을 델타의 하위 항목 줄(`NNa`, `NNb`…)로 바꾼다. 원 행 상태 `split`, 하위 행 추가(pending/0/0). 재번호 금지. history.md 한 줄.
- **추가/정제**: 델타의 완전한 항목 줄을 그대로 붙인다/바꾼다. 문안이 없으면 그 변경은 history.md에 `제안`으로만 남긴다. 완료 항목의 정제는 문안만.
- **삭제/재범위/순서**: `major_changes_used++`, 초과면 정지+사람 호출. history.md에 `major` 표시.
- **문서 정리**: run-state 결과 칸 정리 요청 → 한 토막으로 자른다(원문은 history.md 한 줄로). `per_dispatch_minutes` 갱신값 → run-state에 적고 history.md `캡변경` 한 줄(드라이버만 쓴다 — auditor는 델타로 권고만. 이 노브는 정지 캡이 아니라 넘김 신호라 auditor 권고를 허용한다; max_iterations·max_minutes는 사람만). 비용 추세 악화 → Step 3 인계 보고에 원인 포함.
- auditor의 상세 근거는 `audit/`에 있으니 컨텍스트에 들이지 않는다. **목표·완수조건은 절대 바꾸지 않는다.** `BOUNCE:<사유>`면 즉시 정지+사람 호출.

드라이버는 **절대 직접 task를 구현·분석하지 않는다.** 유혹이 들면(작은 task니까 내가…) 참고 worker를 띄운다. 조건 파일·핸드오프·지식 파일을 직접 편집하지도, evaluator를 직접 띄우지도 않는다(최종 eval 제외) — 그래야 네 컨텍스트가 디스패치 기록만으로 유지되고, 기록의 소유 경계가 지켜진다.

### Step 2: 최종 eval (전 task 완료 시, 최종 패스 뒤)
goal.md의 완수조건을 확인한다. 판정은 반드시 파일에 남는다:
- 최종 조건이 **실행 가능한 명령**(테스트/빌드 등)이면 `Bash`로 직접 실행하고, 명령·종료코드·출력 요약을 `eval/final-<ts>.md`에 `## 판정: APPROVED|NEEDS_REVISION` 줄과 함께 쓴다.
- 결과/동작 기준이면 `Agent`로 `byko-goal:evaluator`를 **목표 전체** 대상으로 띄운다(원목표 대비 검수). goal_dir + `mode: final` 전달 → evaluator가 `eval/final-<ts>.md`를 쓴다.
- 통과 → run-state `status: complete`, history.md `완료`. 실패 → 관련 task를 재오픈(회차 파일 archive)하거나 부족분을 history.md에 `제안`으로 남기고 checkpoint_requested=final-gap → 1로(캡이 남았으면). 캡이 없으면 Step 3.

### Step 3: 정지 + 인계 (캡 도달 / 공회전 / blocked 패턴 / BOUNCE / 완료)
어떤 사유로 멈추든 **반드시 다음을 안내한다** — 여기서 끊고 끝내지 않는다:
- 현황 요약: 완료 N / 전체 M, blocked 목록과 사유, 소진한 캡, **비용 요약**(run-state 상태표의 시도·분·토큰k 합계와 task당 평균 + 체크포인트 기록의 auditor 합계 — 후반이 초반보다 무거우면 그 사실)
- 산출물 위치: goal_dir의 주요 결과물
- **재개 방법**(캡/blocked/공회전으로 멈춤): "상태는 전부 디스크에 있습니다. 이어서 하려면 `/goal-run <slug>` 다시 실행. 캡 상향은 run-state.md에서 — 단 한도에 걸릴 때마다 올리면 공회전을 합법화합니다. 먼저 `eval/`·`audit/`에서 왜 막혔는지 보세요."
- **완료 시**: 무엇이 달성됐는지 + 최종 eval 결과 + 산출물 경로. 후속 작업이 있으면 1-2개 제안.
- history.md에 `일시정지`(사유) 한 줄, run-state `status: paused`(완료면 이미 `complete`). 백스톱을 쓸 수 없는 환경이었으면 그 사실도 적는다.

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
