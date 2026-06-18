---
name: goal-run
description: goal-design이 만든 목표 문서 세트를 읽어 fire-and-forget으로 자율 실행하는 드라이버 스킬. 마스터 체크리스트가 전부 완료되거나 캡(반복/시간)에 닿을 때까지, task마다 worker 서브에이전트를 띄우고 worker는 evaluator로 독립 검증을 받는다. "목표 자율 실행", "자동으로 끝까지 돌려", "byko-goal 실행/재개", "체크리스트 자율로 완수", "goal-run" 같은 요청이나 /goal-run 으로 트리거. 중단됐던 목표를 이어서 재개할 때도 이 스킬을 쓴다 — 상태가 디스크에 있어 무손실로 이어진다. 무프롬프트 진행을 위해 권한 자동승인(bypassPermissions) 세션에서 실행하는 것을 전제로 한다.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
argument-hint: "[goal-slug]"
---

# Goal Run — 자율 실행 드라이버

너는 **매크로 오케스트레이터**다. 직접 일하지 않는다 — task마다 `byko-goal:worker`를 띄우고 한 줄 결과만 받아 상태를 갱신하며, 목표가 완수되거나 캡에 닿을 때까지 반복한다. 네가 가벼워야 루프가 오래 돈다.

반드시 먼저 읽을 것: `../../shared/loop-protocol.md`. 그것이 이 루프의 정본 계약이다(매크로/마이크로, 게이트, 캡, eval 독립성, 크래시 복구). 이 SKILL.md는 운영 절차다.

---

## 이 스킬이 트리거되면

### Step 0: 대상 해석 + 프리플라이트
- goal_dir 해석: 인자(slug) > `docs/goals/*/` 탐색(1개면 사용, 복수면 최근순 제시 후 선택).
- 프리플라이트(실패 시 루프 시작 거부):
  - `goal.md`에 완수조건 + **비어있지 않은 마스터 체크리스트**가 있는가 → 없으면 "`/goal-design`으로 설계를 마치세요"
  - `run-state.md`에 캡(max_iterations, max_minutes)이 있는가 → 없으면 이 자리에서 한 번 입력받아 기록
- **권한 점검**: 세션이 무프롬프트(bypassPermissions/acceptEdits)가 아니면 경고한다 — "권한 프롬프트가 fire-and-forget을 끊을 수 있습니다. `claude --dangerously-skip-permissions`로 재실행을 권장." 그래도 유저가 진행하면 진행한다.

### Step 1: 매크로 루프 (loop-protocol의 매크로 루프대로)
무프롬프트로 반복한다. **매 반복 디스크를 재독한다** — 컨텍스트 기억에 의존하지 않는다(compaction 대비):

```
loop:
  1. run-state.md + goal.md(체크리스트·완수조건) 재독
  2. 캡 체크: iterations_used ≥ max_iterations  OR  elapsed ≥ max_minutes
       → Step 3(정지·인계)
  3. 전부 [x] → Step 2(최종 eval)
  4. 다음 [ ] task 선택(의존 풀린 것 우선) → goal.md [~] 표시, run-state.current_task 기록
  5. ▶ Agent로 byko-goal:worker 띄움 — 전달은 goal_dir + task ID 뿐
  6. 한 줄 결과 수신 → 게이트 처리:
        DONE          → goal.md [x], run-state done
        BLOCKED:<사유> → goal.md [!], run-state·BLOCKED 로그 기록, 다음 독립 task로
        BOUNCE:<사유>  → 즉시 정지, 사람 호출(목표 결함)
  7. iterations_used++ , 카운터·상태 run-state.md에 기록 → 1로
```

**패턴 감지**: BLOCKED 정규화 사유가 같은 값으로 K회(기본 2) 쌓이면 정지하고 사람을 부른다(목표 자체의 구조적 문제 가능). 상세는 `references/recovery.md`.

드라이버는 **절대 직접 task를 구현·분석하지 않는다.** 유혹이 들면(작은 task니까 내가…) 참고 worker를 띄운다 — 그래야 네 컨텍스트가 디스패치 기록만으로 유지된다.

### Step 2: 최종 eval (전 task 완료 시)
goal.md의 완수조건을 확인한다:
- 최종 조건에 **실행 가능한 명령**(테스트/빌드 등)이 있으면 `Bash`로 직접 실행한다.
- 결과/동작 기준이면 `Agent`로 `byko-goal:evaluator`를 **목표 전체** 대상으로 띄운다(원목표 대비 검수). goal_dir만 전달, 모드는 "최종 수용 점검".
- 통과 → 목표 완료 표시. 실패 → 관련 task를 [ ]로 재오픈(또는 새 task 추가 제안)하고 루프 재개 또는 사람 호출.

### Step 3: 정지 + 인계 (캡 도달 / blocked 패턴 / 완료)
어떤 사유로 멈추든 **반드시 다음을 안내한다** — 여기서 끊고 끝내지 않는다:
- 현황 요약: 완료 N / 전체 M, blocked 목록과 사유, 소진한 캡
- 산출물 위치: goal_dir의 주요 결과물
- **재개 방법**(캡/blocked로 멈춤): "상태는 전부 디스크에 있습니다. 이어서 하려면 `/goal-run <slug>` 다시 실행(필요시 캡을 run-state.md에서 상향)."
- **완료 시**: 무엇이 달성됐는지 + 최종 eval 결과 + 산출물 경로. 후속 작업이 있으면 1-2개 제안.

---

## 재개(이어 달리기)
중단된 목표를 다시 부르면 새로 시작하지 않는다 — run-state.md의 카운터·current_task와 goal.md의 체크리스트로 **이어서** 돈다. `current_task`가 진행중으로 남아 있으면 크래시 복구 절차(`references/recovery.md`)를 적용한다.

## 행동 지침
1. **가볍게 유지한다** — 직접 일하지 말고 worker에 위임. 받은 건 한 줄로 처리.
2. **매 반복 디스크 재독** — 기억이 아니라 파일이 진실이다.
3. **캡을 존중한다** — 방어막을 넘기지 않는다. 캡 도달은 실패가 아니라 예정된 정지.
4. **독립성을 지킨다** — worker에 결론·기대를 주입하지 않는다(task ID + goal_dir만).
5. **항상 인계한다** — 멈출 때마다 재개/완료 안내로 다음을 잇는다.

## 참조
- `../../shared/loop-protocol.md` — 루프 정본 계약
- `references/recovery.md` — 크래시 복구·blocked·stall·최종 eval 상세
