# 자율 루프 계약

byko-goal의 실행 모델. `goal-run`(드라이버), `worker`, `evaluator`, `auditor`가 공유한다. 한 번 읽고 따른다.

**이 파일이 규약의 정본이다.** 목표 문서(goal.md·run-state.md·knowledge.md)에 이 규약을 복제하거나 "집행 규약"을 새로 적지 않는다 — 복제본은 반드시 한쪽만 고쳐져 서로 반대를 지시하게 된다(실측). 목표 문서에는 목표·상태·지식만 산다.

## 왜 이 구조인가

장기 목표는 한 세션의 컨텍스트에 다 들어가지 않는다. 그래서 **무상태 드라이버 + 일회용 worker + 디스크 상태**로 분리한다:

- **드라이버는 오래 산다 → 비대해지면 안 된다.** 직접 일하지 않는다. task 1개당 worker 1개를 띄우고 한 줄 결과만 받는다. 드라이버가 하는 "확인"은 전부 **세고(count)·찾는(grep) 한 줄 명령**이다 — 내용을 읽어 판단하지 않는다.
- **worker는 task 1개 쓰고 죽는 일회용 → 부풀어도 무해하다.** 구현·평가·수정의 무거운 사이클을 전부 worker 안에서 끝낸다.
- **유일한 기억은 디스크의 문서다.** 매 반복 디스크를 재독한다 — compaction·세션 종료·재개에 무손실이다.

여기에 둘이 더 있어야 오래 돈다. 없으면 정확성은 지켜져도 비용이 진행에 비례해 오르고 한도가 집행되지 않는다 — 이 둘은 도메인·세션과 무관하게 같은 모양으로 재현된다:

- **디스크는 자란다.** 매 회 읽히는 문서가 진행에 비례해 커지면 task당 비용도 진행에 비례해 오른다. 크기는 증상이고 원인은 **위치·형태·관련성**이다 — 로그가 계약 파일에, 산문이 표 칸에, 다음 worker에게 필요 없는 것이 knowledge에 들어가고 아무도 빼지 않았다. 그래서 **읽기 계약·쓰기 기준·주기적 정리·비용 신호**가 있다(§자라는 상태).
- **자기 신고는 집행이 아니다.** 한도를 받는 쪽이 스스로 세는 값은 아무도 대조하지 않으므로 틀려도 아무 일이 안 일어난다. 그래서 **회차는 디스크 파일 수로 세고, 판정은 파일에서 읽고, 드라이버가 대조**한다(§게이트·§캡).

## 두 층의 루프

### 매크로 루프 — 드라이버(goal-run)

매 반복(정본 — goal-run/SKILL.md는 이 순서를 그대로 명령으로 옮긴 것이다):

```
1. 재독 + tick: run-state.md·goal.md(체크리스트) 재독.
   elapsed_minutes += round((now − last_tick)/60) ; last_tick = now
2. 캡:        iterations_used ≥ max_iterations  OR  elapsed_minutes ≥ max_minutes → 정지·인계
3. 요청된 체크포인트: checkpoint_requested ≠ — → ▶ auditor (goal_dir + last_checkpoint + 사유)
              → 델타 적용 → stall_streak=0 · checkpoint_requested=— · done_since_checkpoint=0 → 1로
              (계획 문제로 막힌 task는 공회전 판정보다 먼저 auditor가 나눈다 — 이 순서가 적응 경로다)
4. 공회전:    stall_streak ≥ stall_limit → 정지·보고 (recovery.md)
5. 완료:      체크리스트 전부 [x] → ▶ auditor 최종 패스(체크포인트를 겸한다 — 따로 또 띄우지 않는다)
              → 델타에 재오픈·항목 추가가 있으면 적용하고 1로. 없으면 최종 eval → eval/final-<ts>.md
              → 통과: status=complete → 보고·정지 / 실패: 재오픈 또는 추가 → 1로
6. 주기 체크포인트: done_since_checkpoint ≥ checkpoint_every → 3과 같이 → 1로
7. 선택:      current_task가 재디스패치 대기(PARTIAL·턴 소진·unverified-done, 행 상태 running)면 그 task를
              이어서 모드로; 아니면 다음 [ ] task(의존 풀린 것 우선) → goal.md [~], run-state: current_task=NN,
              dispatched_at=now, 행 running · 디스패치++
8. ▶ worker dispatch (byko-goal:worker). goal_dir + task ID만 (+ "이어서 모드").
   환경이 백그라운드 dispatch·정지를 지원하면 백그라운드로 띄우고 per_dispatch_minutes×2 뒤 깨어나
   진전(회차 파일 수·산출물 mtime)을 한 줄로 잰다 — 없으면 끊고 턴 소진으로 처리(recovery.md).
9. 결과 수신 → 게이트(아래) → iterations_used++ → 재디스패치 대기가 아니면 current_task=— · dispatched_at=— → 1로
```

드라이버는 절대 직접 파일을 읽어 분석하거나 구현하지 않는다. 드라이버의 컨텍스트는 "dispatch 기록 + 한 줄 명령의 결과"만 쌓여야 한다.

### 마이크로 루프 — worker (task 1개 내부)

```
a. 읽기 세트 복원: goal.md + knowledge.md(색인이면 이 task에 걸리는 영역 파일만) + 최신 handoff 1-2개.
   run-state.md는 per_task_attempt_limit · per_dispatch_minutes · dispatched_at 값만 grep.
   (run-state.md·goal.md는 쓰지 않는다 — 드라이버 소유)
b. tasks/NN.md에 완료조건 작성 — §완료조건의 규칙대로. 산출물 술어만, 필요한 만큼만, 검증 방법 동반.
c. 작업 수행. 팬아웃은 조사(explorer)·독립 구현 조각(일반 서브에이전트)에만.
   하위 byko-goal:worker는 띄우지 않는다 — NN의 기록(tasks/·handoffs/·eval/)과 회차를 오염시킨다.
   넘기는 시점: 조건의 검증 방법을 한 번씩 돌려 초록이면 **바로 d로**. 그 뒤 새 자기 확인을 시작하지 않는다(§검증의 경계).
   시간: 긴 활동 전에 `now − dispatched_at`을 본다. per_dispatch_minutes가 다 되면 — 산출물이 검증 가능한 상태면 d로,
   아니면 진행 상태를 tasks/NN.md 작업 노트에 남기고 "PARTIAL:time-budget" 반환(다음 dispatch가 이어서 한다).
d. 회차 대조: n = `ls eval | grep -cE '^NN-[0-9]'`. n ≥ per_task_attempt_limit → "BLOCKED:attempt-limit" 반환.
   ▶ evaluator 1개 dispatch (byko-goal:evaluator). goal_dir + task ID만 (독립성).
   조건별로 쪼개 여러 evaluator를 띄우지 않는다 (§eval 독립성 4).
e. 판정은 evaluator의 반환 메시지가 아니라 최신 eval/NN-<ts>.md의 마지막 `## 판정:` 줄에서 읽는다:
   - APPROVED       → 기록 마감(knowledge 갱신 · handoffs/NN.md · ownership.md 행) → "DONE" 반환
   - NEEDS_REVISION → 피드백대로 수정 → d
   - PENDING / 파일 없음 (evaluator가 판정 전에 죽음) → 그 회차도 센다. 검증 무게를 줄여(조건·명령 묶기) → d.
                      두 번째면 "BLOCKED:eval-budget" 반환
```

## 게이트 — 드라이버가 worker 결과를 디스크와 대조한다

worker의 말은 주장이다. 반환의 **첫 줄만** 해석하고 나머지(결론·권고·다음 task에 대한 의견)는 읽지 않는다 — 드라이버 컨텍스트와 독립성을 지킨다.

먼저 세 값을 디스크에서 읽는다(명령의 정본은 goal-run/SKILL.md §게이트 명령):
- **시도** = 회차 파일 수 `eval/NN-<digits>…` — 행의 시도 칸에 **덮어쓴다**(worker가 뭐라 했든)
- **판정** = 이름순 마지막 회차 파일의 마지막 `## 판정` 줄에 `APPROVED`가 있는가 (mtime이 아니라 `<ts>` 이름 정렬 — 재현 가능해야 한다)
- **소요·토큰** = Agent 결과에 붙은 값(worker가 띄운 evaluator까지 포함된 dispatch 전체 비용) → 행의 분·토큰k에 **누적**, 소요가 per_dispatch_minutes를 넘겼으면 결과 칸에 `over-time`

| worker 반환 | 판정 | 처리 |
|---|---|---|
| `DONE` | APPROVED | goal.md [x] · 행 done/APPROVED · done_since_checkpoint++ · stall_streak=0. 기록 마감 확인: `handoffs/NN.md` 존재 + ownership.md에 NN이 소유 칸 또는 공유 칸에 있음 — 빠졌으면 done은 유지하되 결과 칸에 `기록누락`(auditor D가 보정) |
| `DONE` | ≠ APPROVED | **거부** — worker가 스스로 판정했거나 잘못 읽었다. 결과 칸 `unverified-done`, BLOCKED 로그에 한 줄(패턴 감지용), stall_streak++, **재디스패치 대기**(goal.md [~] 유지) |
| `BLOCKED:<사유>` | — | goal.md [!] + 사유 · 행 blocked · BLOCKED 로그 한 줄 · stall_streak++ · 다음 독립 task로. 사유가 **계획 문제**(`task-too-big`·`eval-budget`·`no-progress`)면 `checkpoint_requested=<사유>` — 다음 반복 3단계에서 auditor가 나눈다 |
| `PARTIAL:<사유>` | — | 진행 중이다(실패가 아니다). 결과 칸 `PARTIAL:<사유>`, **stall_streak 변화 없음**, 재디스패치 대기. history.md에 한 줄 |
| `BOUNCE:<목표결함>` | — | 즉시 정지, 사람 호출 — 자율 루프가 풀 수 없다 |
| 반환 없음 · 턴 소진 · 백스톱으로 끊음 | — | stall_streak++, 재디스패치 대기 |

**재디스패치 대기**: 행의 디스패치 < per_task_attempt_limit이면 7단계에서 같은 task를 이어서 모드로 다시 띄운다(dispatched_at 갱신·디스패치++). 한도면 `BLOCKED:no-progress` — 계획 문제이므로 `checkpoint_requested`.

**시도 ≥ per_task_attempt_limit인데 APPROVED가 아니면** 드라이버가 닫는다: worker가 계획 문제 사유(`eval-budget`·`task-too-big`)로 BLOCKED를 반환했으면 그 사유를 유지하고(→ 체크포인트), 그 외에는 `BLOCKED:attempt-limit`.

**패턴 감지 (드라이버가 잃은 시야의 보완책):** 드라이버는 eval 상세를 보지 않는다. 대신 BLOCKED 정규화 사유를 누적해, **같은 사유가 K회(기본 2) 누적되면** "목표 자체의 구조적 문제 가능" 신호로 정지+사람 호출한다. 계획 문제 사유는 예외다 — 체크포인트로 가고, **같은 task(또는 그 분할 자식)가 두 번째로 계획 문제로 막힐 때** 사람을 부른다. 근거는 `eval/`·`audit/`에 있다.

## 완료조건 — evaluator 하나가 한 번에 닫을 수 있어야 한다

완료조건은 task의 **산출물**에 대한 술어다. 조건이 evaluator 하나의 예산을 넘는 순간 검증이 쪼개지고, 쪼개지면 회차를 셀 수 없고, 셀 수 없으면 한도가 없다 — task 비대화는 여기서 시작된다. 규칙:

1. **양** — 필요한 만큼만. 하한은 없다(테스트 러너 하나가 전부를 덮으면 조건 1개가 정상이다). 상한은 evaluator의 턴 예산에서 온다 — 30턴에서 읽기·보고서를 빼면 조건마다 명령 하나로도 열 개 남짓이 한계라, 10개를 넘으면 task가 크거나 조건이 과분할된 신호다.
2. **진입점 하나로 접는다** — 여러 검사를 한 번에 돌리는 진입점(테스트 러너·검사 스크립트·루브릭 체크리스트)이 있으면 **그 하나가 조건 하나**다. 하위 검사를 따로 세지 않는다 — 검사 강도는 같고 회차만 준다. 목표 초반 task에서 이런 진입점을 만들어 두면 이후 모든 task가 싸진다.
3. **고정점** — 술어는 평가 전에 값이 확정된 것만: 파일 존재·내용·명령 종료코드·출처 원문 대조. **평가 행위나 기록 갱신이 판정 대상을 바꾸는 조건은 금지** ("기록이 자기 상태를 옳게 말하는가", "검증에서 배운 것이 기록에 반영됐는가"). 통과시키는 행위가 대상을 바꾸면 고정점이 없어 영원히 닫히지 않는다.
4. **하네스 기록은 조건이 아니다** — handoffs·knowledge·ownership·run-state 갱신은 하네스가 구조로 강제한다(드라이버 게이트·auditor 보정). evaluator는 그것을 채점하지 않는다.
5. **검증 방법은 명령·대조 대상으로** — "적절한가"가 아니라 "`<명령>` 종료코드 0" / "`<파일>`에 X가 N개" / "<출처> 원문과 일치".

## 검증의 경계 — worker는 만들고, evaluator가 반증한다

worker가 자기 손으로 하는 확인은 디스크에 남지 않아 **아무도 셀 수 없고, 끝도 없다** — 고칠 때마다 새 자리가 보이니 "언제 충분한가"가 정의되지 않는다. 한 dispatch가 evaluator를 한 번도 부르지 않은 채 몇 시간을 도는 사고는 전부 여기서 난다. 그래서 경계를 말로 못 박는다:

1. **넘기는 시점은 "조건이 초록"이다.** tasks/NN.md 조건의 검증 방법을 한 번씩 돌려 통과하면 즉시 evaluator를 띄운다. 그 뒤로 새 자기 확인을 시작하지 않는다.
2. **결함 찾기는 evaluator의 일이다.** worker의 자기 확인은 조건을 정직하게 적을 수 있을 만큼이지, 결함을 다 찾기 위한 것이 아니다. evaluator가 지적하면 그것만 고치고 다시 넘긴다 — 검증의 끝은 evaluator의 판정이고, evaluator는 반드시 끝난다(30턴 · 선기록).
3. **더 확신이 필요하면 확인을 검사기로 만든다.** 손으로 대조한 것은 사라지지만 스크립트·체크리스트로 만든 것은 조건이 되어 evaluator가 돌리고 다음 task도 쓴다(§완료조건 2의 진입점).
4. **한 dispatch는 유한하다 — 세 겹으로.** ① worker의 턴 한도(도구 단위). ② `per_dispatch_minutes`(§캡) — 이 목표의 범위와 실측에서 나온 값을 worker가 `dispatched_at`으로 스스로 지킨다: 다 되면 검증 가능한 상태면 evaluator로, 아니면 `PARTIAL:time-budget`으로 상태를 남기고 넘긴다. ③ worker의 자기 신고에만 맡기지 않는다 — 드라이버가 백그라운드 dispatch 뒤 예산의 2배에 깨어나 진전(회차 파일 수·산출물 mtime)을 한 줄로 재고, 없으면 끊고 턴 소진으로 처리한다(지원 환경에서 기본, 미지원이면 ①만 남는다는 것을 인계 보고에 적는다). 턴이 다하거나 끊긴 dispatch는 디스패치 한도까지 이어서 띄운 뒤 auditor가 나눈다. 플러그인은 시간값을 정하지 않는다(얼마나 걸리는 일인지는 목표마다 다르다).

## 회귀 방지 (A 표적 · B 전역 체크포인트 · C 체크리스트 재검증 · D 문서 정리)

장기 목표는 뒤 task가 앞 task 산출물을 깨거나(회귀), 진행하며 처음 계획이 틀려질 수 있다(드리프트). 세 겹으로 막되 **무거운 추적은 전부 서브에이전트가 하고, 드라이버는 concise 델타만 적용**한다.

**고정/가변 경계 (절대 원칙):** **목표 + 완수조건 = 고정 계약**(사람/goal-design만 변경). **마스터 체크리스트 = 가변 경로**(auditor가 목표를 향해 재계획 가능). 적응형 체크리스트를 주되 목표 자체의 표류는 차단한다.

**적응 — 설계는 가설이다.** 설계 시점에는 안 보이는 것이 많다. 구현이 계획을 반증하면 계획이 바뀌는 것이 정상이고, 바뀌는 경로가 정해져 있다 — 막힌 것은 사람에게 올리기 전에 이 경로로 먼저 푼다:

| 층 | 누가 | 무엇을 바꿀 수 있나 | 어떻게 |
|---|---|---|---|
| 목표·완수조건 | 사람 (goal-design) | 전부 | 루프 밖에서. 루프 안에서는 `BOUNCE`로 올린다 |
| 마스터 체크리스트 | auditor (체크포인트) | 추가·분할·정제: 자율 / 삭제·재범위·순서 뒤집기: major 예산 | 델타 → 드라이버 적용 → history.md |
| task 하나의 "끝" | worker | tasks/NN.md 완료조건 — 수용 힌트의 **의도**를 지키는 범위에서 구체화·재해석 | 작업 전 작성, evaluator가 적정성 검토 |
| 실행 방법 | worker | 접근·도구·순서·팬아웃 | 자유 |
| 계획 수준 변경 | worker → auditor | 제안만 — "이 task는 둘로 나눠야", "task N이 빠졌다", "07은 불필요해졌다" | history.md에 `제안` 한 줄(+ 바로 다음 worker가 알아야 하면 handoff에도). 다음 체크포인트에서 auditor C가 처리. 지금 당장 진행이 불가하면 `BLOCKED:task-too-big` → 체크포인트가 앞당겨진다 |

worker가 goal.md의 체크리스트를 직접 고치지 않는 이유는 권한이 아니라 시야다 — worker는 task 하나만 보고, 체크리스트 전체와 회귀·의존을 보는 건 auditor다. 대신 worker의 제안은 반드시 다음 체크포인트에서 읽힌다.

**산출물 소유 맵 (`ownership.md`).** 회귀를 표적화하려면 "어느 task가 어느 산출물을 소유하는가"가 필요하다. worker는 완료 시 자기가 만들/바꾼 산출물을 한 행씩 기록한다(경로 | task | 단독/공유 — 한 낱말 칸, 설명 없음). evaluator·auditor가 이 맵으로 표적 회귀를 건다.

**A — 표적 회귀 (per-task, worker 마이크로루프 안).** task N의 evaluator는 N의 조건만 보지 않는다: N이 건드린 산출물을 소유한 *이전* task가 있으면 그 task의 영향받는 조건만 함께 재검증한다. 회귀 시 NEEDS_REVISION → worker가 **이번 task 안에서** 고친다("네가 깼으면 네가 고친다"). 못 고치면 BLOCKED/BOUNCE. 드라이버 부담 0.

**B+C+D — 체크포인트 (주기적, auditor).** 드라이버는 `checkpoint_every`(기본 4) task마다, 최종 eval 직전에 `byko-goal:auditor` 1개를 띄운다. auditor는 — **B**: 지난 체크포인트 이후 바뀐 산출물에 걸린 완료 task를 재검증(델타 기준, 전수 아님; 의심 task엔 `mode: regress`로 evaluator를 띄움), **C**: knowledge·산출물에 비춰 남은 task가 아직 맞는가(불필요/누락/순서/범위), **D**: 문서 정리 — 읽기 세트에서 있을 자리가 아닌 것을 옮기고, 운영 노트를 은퇴시키고, task당 비용 추세를 보고, 기록 누락을 보정한다(§자라는 상태). 상세는 `audit/NN-<ts>.md`에 남기고 드라이버엔 **concise 델타만** 반환한다: `{재오픈 task+사유, 체크리스트 변경(major 여부), 문서 정리 한 줄}`.

**드라이버의 델타 적용 (가벼움 유지).** 델타는 드라이버가 그대로 붙일 수 있는 완전한 항목 줄로 온다.
- **재오픈**: 회귀한 task를 goal.md `[ ]`로 되돌리고, 그 task의 회차 파일(`eval/NN-<digits>…`만)을 `archive/eval/`로 옮긴다(새 라운드 — 행 reopened, 디스패치·시도 0). history.md에 한 줄.
- **분할**: 원 항목을 하위 항목 `NNa`, `NNb`…로 **대체**한다(자율 — 목표가 받는 것이 줄지 않는다). 원 항목 줄은 체크리스트에서 빠지고 행 상태는 `split`(그 tasks/·eval/ 파일은 남는다 — 하위가 참고한다). 하위는 새 라운드로 `[ ]`·행 추가. **task ID는 절대 재번호하지 않는다** — ID가 tasks/·eval/·ownership의 키다. 하위 ID의 회차 파일은 `NNa-<ts>.md`, 회차 수는 `^NNa-[0-9]`로 센다.
- **추가/정제**: 자율 적용. 파괴적 변경(삭제/재범위/순서 뒤집기)은 **major로 카운트** — `major_changes_used`가 `major_changes_budget`(기본 3)을 넘으면 정지+사람 호출(목표 표류 방지). 적용한 변경은 history.md에 한 줄.
  - **major vs 자율 판정 기준(결정적):** task를 **삭제/순서변경**하거나, 산출물을 **목표 요구 이하로 축소·제거**하면 `major`. task **추가/분할**(목표가 받는 것이 줄지 않는다), 또는 산출물이 목표 요구를 *여전히 충족*한 채 접근·조건만 명료화(`정제`, 중복 제거 포함)하면 자율. 애매하면 `major`로 본다(보수적 — 예산을 지킨다).
  - **완료 항목의 정제**는 문안만 바꾼다(재검증 없음). 완료 항목이 만들어야 할 산출물을 바꾸는 것은 정제가 아니라 재오픈이다.
- auditor의 상세 분석은 컨텍스트에 들이지 않는다 — `audit/`에서 참조한다.

## 캡 = 방어막 (디스크 영속 — 드라이버가 잰다)

fire-and-forget의 안전핀. `run-state.md`에 산다 — 컨텍스트가 아니라 디스크에 있어야 compaction·재개에도 살아남는다. 캡은 **무엇을 세는지와 재는 방법**이 정의돼야 집행된다:

| 노브 | 뜻 | 재는 법 |
|---|---|---|
| `max_iterations` | worker dispatch 총수 상한 (재개·재디스패치 포함; auditor는 세지 않고 체크포인트 기록에 따로 남긴다) | dispatch마다 `iterations_used++` |
| `max_minutes` | **활성** 시간 상한 — 정지·유휴 구간은 세지 않는다. auditor 시간도 포함된다(tick이 잡는다) | 매 반복 `elapsed += round((now − last_tick)/60); last_tick = now`(초 단위로 기록해 절삭 누적을 막는다). 재개(Step 0)에서는 `last_tick = now`로 리셋만 한다(더하지 않음). 크래시로 잃은 시간은 세지 않는다(과소 계상 허용) |
| `per_task_attempt_limit` | task 한 라운드에서 (a) evaluator 회차 (b) worker dispatch **각각**의 상한 (기본 3) | (a) `ls eval \| grep -cE '^NN-[0-9]'` (b) 행의 디스패치 칸. 재오픈 = 새 라운드 |
| `per_dispatch_minutes` | worker 한 번의 활성 시간 상한. 횟수 캡은 dispatch가 끝나야 세지만 이건 dispatch **안**을 막는다 — 드라이버가 못 보는 구간. **값은 플러그인 상수도 사람 입력도 아니다 — 작업 범위를 아는 에이전트가 정한다**: goal-design이 task 예상 소요 × 2로 시드하고, auditor D가 체크포인트마다 이 목표의 실측(완료 task의 **dispatch당** 소요 = 분 ÷ 디스패치, 값이 있는 것만, 3개 이상일 때 중앙값 × 2)으로 갱신한다 — 라운드 누적값을 쓰면 PARTIAL이 잦을수록 예산이 래칫된다 | 1차: worker가 `dispatched_at`을 읽어 스스로 지킨다(§검증의 경계 4). 2차: 드라이버가 백그라운드 dispatch 뒤 예산의 2배에 깨어나 진전(회차 파일 수·산출물 mtime)을 재고 없으면 끊는다(지원 환경 기본, recovery.md). 반환 시 Agent 소요로 대조해 넘긴 dispatch를 `over-time`으로 표시. 값이 없으면(구버전 목표) 첫 체크포인트까지 worker maxTurns·디스패치 한도가 상한 |
| `checkpoint_every` | auditor 주기 (기본 4 task) | `done_since_checkpoint` |
| `major_changes_budget` | 파괴적 체크리스트 변경 허용 횟수 (기본 3) | `major_changes_used` |
| `stall_limit` | 연속 dispatch에 새 [x]가 0이면 정지 (기본 3) | `stall_streak` (DONE 수락 시 0) |

캡 도달 = 실패가 아니라 **예정된 정지**다. 상태는 전부 디스크에 있으니 `/goal-run <slug>`로 이어서 진행한다. 캡을 올리는 것은 사람의 결정이다 — 한도에 걸릴 때마다 올리면 공회전을 합법화하는 것이다.

## 자라는 상태 — 읽기 계약·쓰기 기준·정리·비용 신호

장기 루프의 비용은 `읽기 세트 × dispatch 수`다. dispatch 수는 캡이 막지만 읽기 세트는 아무도 막지 않으면 진행에 비례해 자라 같은 성격의 task가 갈수록 무거워진다. 크기를 세는 것으로는 못 막는다(숫자를 맞추려 유용한 것을 버리게 된다) — **무엇이 어디에 있어야 하는가**로 막는다. 규칙:

**1. 계약 파일과 로그 파일을 섞지 않는다.** 매 회 읽히는 파일(goal.md·knowledge.md·ownership.md·run-state.md)은 작고 안정적이어야 한다. 시간순으로 쌓이는 것(체크리스트 변경 이력·재오픈 사유·정리 기록·제안·일시정지)은 `history.md`로 — 아무도 매 회 읽지 않는다. eval/·audit/·archive/도 로그다. "한 줄씩만 append"해도 task 수만큼 쌓인다 — 위치가 문제지 분량이 문제가 아니다.

**2. 읽기 계약 — 누가 매 회 무엇을 읽고, 무엇을 쓰는가.** 표 밖의 파일은 "필요할 때 하나만" 연다. 한 파일을 여러 역할이 쓰더라도 시점이 겹치지 않는다(드라이버는 한 번에 하나만 띄운다 — worker는 task 중에, auditor는 체크포인트에). 같은 시점에 두 역할이 쓰는 파일은 없다.

| 역할 | 매 회 읽는 것 | 쓰는 것(소유) |
|---|---|---|
| 드라이버 | run-state.md · goal.md 체크리스트 | run-state.md 전체 · goal.md 체크리스트(상태·auditor 델타)·헤더 last_updated · history.md · eval/final-<ts>.md(최종 조건이 실행 명령일 때만) |
| worker | goal.md · knowledge.md(색인이면 걸리는 영역만) · 최신 handoff 1-2 | tasks/NN.md · handoffs/NN.md · knowledge.md(갱신) · ownership.md(행 추가) · history.md(`제안` 줄 append만) |
| evaluator | goal.md(해당 항목·완수조건·공통 컨텍스트) · tasks/NN.md · ownership.md | eval/NN-<ts>.md |
| auditor | goal.md · run-state.md · ownership.md · knowledge.md · history.md(지난 체크포인트 이후) · 델타 구간의 tasks/·handoffs/ | audit/ · knowledge.md(정리) · ownership.md(정리·보정) · handoffs/NN.md(누락 보정만) · goal.md 공통 컨텍스트(있을 자리가 아닌 것을 옮기는 정리만 — 체크리스트·목표·완수조건은 델타 경유) · history.md · archive/ |

worker는 run-state.md·goal.md를 쓰지 않는다(캡 값·자기 항목을 읽기만). eval/의 회차 파일은 evaluator만 만들고 아무도 옮기거나 지우지 않는다(드라이버의 재오픈 archive 이동만 예외) — 회차의 증거다. `eval/final-<ts>.md`만 예외로 최종 조건이 실행 명령이면 드라이버가 쓴다. evaluator는 knowledge.md·handoffs·run-state.md를 열지 않는다 — 판정에 꼭 필요하면 조건이 가리키는 파일 하나만. auditor는 run-state.md를 쓰지 않는다 — 결과 칸 정리·예산 갱신은 델타로 드라이버에게.

**3. 형태 — 표의 칸에 산문을 쓰지 않는다.** "비고"·"마지막 결과" 같은 자유 칸은 반드시 문단이 된다. 표의 칸은 한 낱말 또는 한 줄. 설명이 필요하면 로그(history.md·eval/·audit/)에 쓰고 여기엔 포인터만.

**4. 쓰기 기준 — 매 회 읽히는 파일에 무엇을 넣는가.** 판정 질문 하나: **"다음 worker가 매번 읽어야 할 만큼 항구적인가, 아니면 필요할 때 찾으면 되는가?"** 항구적이면 knowledge.md(갱신 — 같은 항목이 있으면 덮어쓴다), 특정 영역에서만 필요하면 `knowledge/<영역>.md`(knowledge.md는 어느 영역을 언제 여는지 알려주는 색인), 한 번만 필요하면 handoff, 경위·원문이면 로그/archive. 사실은 원문 전사가 아니라 포인터(파일:라인 / URL / 명령)로 적는다 — 다음 worker는 사실이 어디 있는지만 알면 된다. "요약체"·"짧게"는 규칙이 아니었다 — 위치와 형태가 규칙이다.

**5. 정리 (auditor D — 매 체크포인트).** 더하기만 하는 루프에서 auditor가 유일하게 뺀다. 매 체크포인트마다 읽기 세트(goal.md 공통 컨텍스트·knowledge.md·ownership.md)를 4의 기준으로 훑어 있을 자리가 아닌 것을 옮긴다: 중복·구식은 갱신, 특정 영역 전용은 영역 파일로, 전사·경위는 archive로(삭제하지 않는다 — `archive/<파일>-<ts>.md`로 이동, 본문엔 포인터). 표 칸의 산문은 한 줄로 되돌린다. 정리는 history.md에 한 줄. 크기가 기준이 아니다 — 크기를 맞추려 유용한 것을 옮기지 않는다.

**6. 비용 신호 — 측정은 돈이 나가는 자리에서.** 드라이버는 task마다 실제 소요(분)·토큰을 run-state.md 행에 적는다(Agent 결과에 붙어 온다). auditor D는 이번 구간 평균을 직전 구간과 비교해 **task당 비용이 오르고 있으면 원인을 찾는다** — 읽기 세트에 무관한 것이 쌓였나, 조건이 과분할됐나, 검증 명령이 무거워졌나, 특정 task 유형인가 — 그리고 처방은 5(정리)나 C(체크리스트 정제)로 낸다. 문서 크기는 원인 후보 중 하나일 뿐이고, 캡이 아니다.

**7. 운영 노트.** 루프를 돌리며 얻은 절차적 교훈("이 검사는 X 순서로 돌려야 한다", "Y 도구는 Z 옵션이 필요하다")은 goal.md·run-state.md가 아니라 `knowledge.md`의 `## 운영 노트`에 **근거(eval/·audit/ 파일 포인터)와 함께** 쓴다. auditor D가 근거 없거나 반증된 항목을 은퇴시킨다(archive). 한 번 적힌 우회책이 영구 규칙이 되는 것을 막는다 — 반증된 가설이 규칙으로 남으면 이후 task가 그것을 따르느라 헛돈다.

## eval 독립성 (절대 원칙)

평가의 가치는 **독립성**이다. worker가 evaluator를 띄우더라도(중첩) 독립성은 구조로 보존한다:

1. **worker는 evaluator에 포인터만 준다** — `goal_dir`, `task ID`. 자기가 한 일·결론·기대를 절대 주입하지 않는다.
2. **evaluator는 정본을 디스크에서 직접 읽는다** — task 서술은 goal.md, 완료조건은 tasks/NN.md. worker가 task를 재구성·미화할 여지가 없다.
3. **evaluator는 실측으로 반증한다** — 검증 방법대로 직접(명령 실행 / 출처 대조 / 산출물·`git diff` 실측). "됐어요"라는 주장이 아니라 ground truth로 판정한다.
4. **회차 1 = evaluator 1 = 보고서 1.** 판정의 정본은 `eval/NN-<ts>.md`이지 반환 메시지가 아니다 — 에이전트가 죽어도 파일은 남는다. evaluator는 파일을 `## 판정: PENDING`으로 먼저 만들고 조건을 잴 때마다 갱신한다. 조건별로 쪼개 evaluator 여럿을 띄우면 회차를 셀 수 없고 조건 간 교차 확인(회귀·적정성)이 사라진다 — 한 evaluator가 못 볼 만큼 조건이 많으면 조건을 접거나(§완료조건 2) task를 나눈다(BLOCKED:task-too-big → auditor 분할).

**모드 = 파일 이름.** worker가 띄우면 회차 `NN-<ts>.md`. auditor의 회귀 재검증은 `mode: regress` → `NN-regress-<ts>.md`. 드라이버의 최종 점검은 `mode: final` → `final-<ts>.md`. 회차 수는 `^NN-[0-9]`만 센다. 모드는 "무엇을 봐라"가 아니라 "어느 파일에 써라"라서 독립성과 무관하다.

worker가 eval *피드백*을 보는 것은 정상이다(그걸로 고친다). 금지되는 건 evaluator가 worker의 *추론*을 보는 것이다.

**디스패치**: 설치 환경에선 `Agent`로 `byko-goal:evaluator`를 이름으로 띄운다. 이름이 해석되지 않는 환경(미설치·CI·도그푸딩)에선 일반 서브에이전트를 띄우되 `agents/evaluator.md`를 읽고 따르게 하고 입력은 동일하게 포인터(`goal_dir` + `task ID`)만 준다 — 독립성은 디스패치 방식과 무관하게 유지된다. "플러그인 에이전트가 설치돼 있지 않으니 이 파일을 읽고 따르라"는 환경 안내는 포인터다(작업에 대한 주장이 아니다) — 드라이버가 worker에게, worker가 evaluator에게 그대로 전달해도 된다. worker의 explorer 위임, 드라이버의 worker·auditor 디스패치도 같은 폴백을 쓴다.

## 완료

체크리스트가 전부 [x]면 드라이버는 auditor 최종 패스(체크포인트 겸)를 돌리고, 델타에 재오픈이나 항목 추가가 있으면 적용하고 루프로 돌아간다. 없으면 완수조건을 점검한다. 결과는 반드시 디스크에 남는다: 결과/동작 기준이면 evaluator(`mode: final`)가 `eval/final-<ts>.md`를 쓰고, 실행 명령이면 드라이버가 명령·종료코드·출력 요약을 같은 이름의 파일에 `## 판정:` 줄과 함께 쓴다. 통과하면 run-state `status: complete` + history.md `완료`. 재실행(`/goal-run <slug>`)은 `status: complete`를 보고 현황만 보고한다 — 최종 패스를 다시 돌리지 않는다(사람이 재개를 원하면 status를 running으로 되돌린다).

## 크래시·예외

세션이 중간에 죽으면 `run-state.current_task`에 진행중 task가 남는다. 재개 시 드라이버는 `last_tick`을 리셋하고, 먼저 그 task의 마지막 회차 판정을 본다 — APPROVED면 worker가 기록 마감 중에 죽은 것이니 DONE으로 수락한다(기록 마감 확인 포함). 아니면 회차·디스패치 수를 디스크에서 대조한 뒤(한도 안이면) 새 worker를 "이어서 모드"로 띄운다 — worker가 산출물·tasks/NN.md·eval/ 상태를 보고 이어서 할지/처음부터 할지 판단한다(기본: 이어서). 진전이 전혀 없던 dispatch(파일 변경·회차 0)도 디스패치로 센다. 상세는 `skills/goal-run/references/recovery.md`.
