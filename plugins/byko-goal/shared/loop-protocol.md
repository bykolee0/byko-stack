# 자율 루프 계약

byko-goal의 실행 모델. `goal-run`(드라이버), `worker`, `evaluator`가 공유한다. 한 번 읽고 따른다.

## 왜 이 구조인가

장기 목표는 한 세션의 컨텍스트에 다 들어가지 않는다. 그래서 **무상태 드라이버 + 일회용 worker + 디스크 상태**로 분리한다:

- **드라이버(오케스트레이터)는 오래 산다 → 비대해지면 안 된다.** 그래서 직접 일하지 않는다. task 1개당 worker 1개를 띄우고 **한 줄 결과만** 받는다.
- **worker는 task 1개 쓰고 죽는 일회용 → 부풀어도 무해하다.** 그래서 구현·평가·수정의 무거운 사이클을 전부 worker 안에서 끝낸다.
- **유일한 기억은 디스크의 문서다.** 매 반복 컨텍스트 기억에 의존하지 않고 디스크를 재독한다 — 자동 컨텍스트 요약(compaction)이 초반 지시를 날려도, 세션이 죽고 재개해도 무손실이다.

## 두 층의 루프

### 매크로 루프 — 드라이버(goal-run)

매 반복:

```
1. run-state.md + goal.md(체크리스트·완수조건) 재독   ← 기억이 아니라 디스크에서
2. 캡 체크: iterations_used ≥ max_iterations  OR  elapsed ≥ max_minutes
            → 정지, 재개 방법 안내
3. 체크포인트 체크: 마지막 체크포인트 이후 완료 task ≥ checkpoint_every
            → ▶ auditor dispatch (B 전역 회귀 + C 체크리스트 재검증)
            → concise 델타 적용(재오픈·체크리스트 수정, major 예산 체크) → 1로
4. 완료 체크: 마스터 체크리스트 전부 [x]
            → ▶ auditor 최종 패스 1회 → 최종 eval 실행 → 결과 보고 → 정지
5. 다음 [ ] task 선택 (의존성 있으면 풀린 것 우선). goal.md에 [~](진행중) 표시,
   run-state.current_task 기록
6. ▶ worker 1개 dispatch (byko-goal:worker). task ID + goal_dir만 전달.
7. 한 줄 결과 수신 → 게이트 처리(아래) → goal.md·run-state 갱신 → iterations_used++ → 1로
```

드라이버는 절대 직접 파일을 읽어 분석하거나 구현하지 않는다. 그 일은 worker의 몫이다. 드라이버의 컨텍스트는 "task 디스패치 기록"만 쌓여야 한다.

### 마이크로 루프 — worker (task 1개 내부)

```
a. goal.md(목표·완수조건·공통 컨텍스트) + knowledge.md + 최신 handoff 1-2개 재독
b. tasks/NN.md에 이 task의 완료조건 작성 — 각 조건에 검증 방법 동반
c. 작업 수행 (도메인에 맞게). 큰 task면 explorer/하위 worker를 Agent로 위임해 팬아웃
d. ▶ evaluator dispatch (byko-goal:evaluator). goal_dir + task ID만 전달 (독립성)
e. 판정 처리:
   - APPROVED → knowledge.md 갱신 + handoffs/NN.md 작성 → "DONE" 반환
   - NEEDS_REVISION → 피드백대로 수정 후 d 재시도.
     단 run-state.per_task_attempt_limit 초과 시 중단하고
     "BLOCKED:<정규화 사유>" 반환 (코드로 우회하지 않는다)
```

## 게이트 (드라이버가 worker 결과를 처리)

| worker 반환 | 드라이버 처리 |
|------------|--------------|
| `DONE` | goal.md 마스터 항목 [x], run-state 해당 task done |
| `BLOCKED:<사유>` | goal.md 항목 [!](blocked) + 사유. run-state BLOCKED 로그에 한 줄 추가. **다음 독립 task로** 진행 (없으면 정지) |
| `BOUNCE:<목표결함>` | 목표/계획 자체의 결함. 즉시 정지하고 사람 호출 — 자율 루프가 풀 수 없다 |

**패턴 감지 (드라이버가 잃은 시야의 보완책):** 드라이버는 eval 상세를 보지 않는다. 대신 BLOCKED 사유 한 줄들을 누적해, **같은 정규화 사유가 K회(기본 2) 누적되면** "목표 자체에 구조적 문제 가능" 신호로 보고 정지+사람 호출한다. 상세 근거는 항상 `eval/NN.md`에 있으니 디스크에서 확인 가능하다.

## 회귀 방지 (A 표적 · B 전역 체크포인트 · C 체크리스트 재검증)

장기 목표는 뒤 task가 앞 task 산출물을 깨거나(회귀), 진행하며 처음 계획이 틀려질 수 있다(드리프트). 세 겹으로 막되 **무거운 추적은 전부 서브에이전트가 하고, 드라이버는 concise 델타만 적용**한다.

**고정/가변 경계 (절대 원칙):** **목표 + 완수조건 = 고정 계약**(사람/goal-design만 변경). **마스터 체크리스트 = 가변 경로**(auditor가 목표를 향해 재계획 가능). 적응형 체크리스트를 주되 목표 자체의 표류는 차단한다.

**산출물 소유 맵.** 회귀를 표적화하려면 "어느 task가 어느 산출물을 소유하는가"가 필요하다. worker는 완료 시 자기가 만들/바꾼 산출물을 `run-state.md`의 소유 맵에 기록한다(worker는 어차피 바뀐 파일을 안다). evaluator·auditor가 이 맵으로 표적 회귀를 건다.

**A — 표적 회귀 (per-task, worker 마이크로루프 안).** task N의 evaluator는 N의 조건만 보지 않는다: N이 건드린 산출물을 소유한 *이전* task가 있으면 그 task의 영향받는 조건만 함께 재검증한다. 회귀 시 NEEDS_REVISION → worker가 **이번 task 안에서** 고친다("네가 깼으면 네가 고친다"). 못 고치면 BLOCKED/BOUNCE. 드라이버 부담 0.

**B+C — 체크포인트 (주기적, auditor).** 드라이버는 `checkpoint_every`(기본 4) task마다 + 최종 eval 직전에 `byko-goal:auditor` 1개를 띄운다. auditor는 전체 상태(완료 task·조건·산출물·knowledge·남은 체크리스트)를 추적해 — **B**: 지난 체크포인트 이후 바뀐 산출물에 걸린 완료 task를 재검증(델타 기준, 전수 아님; 의심 task엔 evaluator를 띄움), **C**: knowledge·산출물에 비춰 남은 task가 아직 맞는가(불필요/누락/순서/범위)를 본다. 상세는 `audit/NN-<ts>.md`에 남기고 드라이버엔 **concise 델타만** 반환한다: `{재오픈할 task+사유, 체크리스트 변경(major 여부)}`.

**드라이버의 델타 적용 (가벼움 유지).**
- **재오픈**: 회귀한 task를 goal.md `[ ]`로 되돌리고 run-state에 사유 기록.
- **체크리스트 변경**: 추가/분할/정제는 **자율 적용**. 파괴적 변경(삭제/재범위/순서 뒤집기)은 **major로 카운트** — `major_changes_used`가 `major_changes_budget`(기본 3)을 넘으면 정지+사람 호출(목표 표류 방지). 적용한 변경은 goal.md "변경 이력"에 한 줄.
  - **major vs 정제 판정 기준(결정적):** task를 **추가/삭제/순서변경**하거나, 산출물을 **목표 요구 이하로 축소·제거**하면 `major`. 산출물이 목표 요구를 *여전히 충족*한 채 접근·조건만 명료화(중복 제거 포함)하면 `정제`. 애매하면 `major`로 본다(보수적 — 예산을 지킨다).
- auditor의 상세 분석은 컨텍스트에 들이지 않는다 — `audit/`에서 참조한다.

## 캡 = 방어막 (디스크 영속)

fire-and-forget의 안전핀. 최초 설계 시 유저가 입력하고 `run-state.md`에 기록 — 컨텍스트가 아니라 디스크에 있어야 compaction·재개에도 살아남는다.

- `max_iterations`: worker dispatch 횟수 상한 (≈ task 시도 횟수)
- `max_minutes`: 벽시계 상한 (최종 백스톱)
- `per_task_attempt_limit`: 한 task 내부 eval 재시도 상한 (기본 3) — 한 task가 예산을 다 먹는 것 방지
- `checkpoint_every`: auditor 체크포인트 주기 (기본 4 task) — 회귀·드리프트를 주기적으로 잡는다
- `major_changes_budget`: 파괴적 체크리스트 변경 허용 횟수 (기본 3) — 초과 시 정지+사람 호출

캡 도달 = 실패가 아니라 **예정된 정지**다. 진행 상태는 전부 디스크에 있으니 `/goal-run <slug>` 재호출로 이어서 진행한다.

## eval 독립성 (절대 원칙)

평가의 가치는 **독립성**이다. worker가 evaluator를 띄우더라도(중첩) 독립성은 구조로 보존한다:

1. **worker는 evaluator에 포인터만 준다** — `goal_dir`, `task ID`. 자기가 한 일·결론·기대를 절대 주입하지 않는다.
2. **evaluator는 정본을 디스크에서 직접 읽는다** — task 서술은 goal.md, 완료조건은 tasks/NN.md. worker가 task를 재구성·미화할 여지가 없다.
3. **evaluator는 실측으로 반증한다** — 검증 방법대로 직접(명령 실행 / 출처 대조 / 산출물·`git diff` 실측). "됐어요"라는 주장이 아니라 ground truth로 판정한다.

worker가 eval *피드백*을 보는 것은 정상이다(그걸로 고친다). 금지되는 건 evaluator가 worker의 *추론*을 보는 것이다.

**디스패치**: 설치 환경에선 `Agent`로 `byko-goal:evaluator`를 이름으로 띄운다. 이름이 해석되지 않는 환경(미설치·CI·도그푸딩)에선 일반 서브에이전트를 띄우되 `agents/evaluator.md`를 읽고 따르게 하고 입력은 동일하게 포인터(`goal_dir` + `task ID`)만 준다 — 독립성은 디스패치 방식과 무관하게 유지된다. worker의 explorer·하위 worker 위임도 같은 폴백을 쓴다.

## 크래시 복구

세션이 중간에 죽으면 `run-state.current_task`에 진행중 task가 남는다. 재개 시 드라이버는: 해당 task의 산출물·tasks/NN.md 상태를 worker에게 확인시켜 **이어서 할지/처음부터 다시 할지**를 판단하게 한다(기본: 이어서). 진전이 전혀 없던 세션(파일 변경·체크 0)은 실패 시도로 카운트한다.
