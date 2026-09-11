# 문서 세트 템플릿

`docs/goals/<slug>/`의 산출물 형태. goal-design이 생성하고, 매 세션이 갱신한다. `<slug>`는 한 프로젝트 안에서 목표끼리 충돌하지 않게 하는 키다.

```
docs/goals/<slug>/
├── goal.md          # 계약: 목표·완수조건·공통 컨텍스트·마스터 체크리스트·인덱스 (의미 상태 SSOT, 작게 유지)
├── run-state.md     # 드라이버 전용: 캡·카운터·task 상태표·BLOCKED 로그 (기계 상태 SSOT)
├── ownership.md     # 산출물 소유 맵 — worker가 행 추가, evaluator·auditor가 표적 회귀에 사용
├── knowledge.md     # 누적 지식 — worker가 갱신, auditor가 정리. 영역이 갈리면 knowledge/<영역>.md + 색인
├── history.md       # append-only 로그 — 체크리스트 변경·재오픈·정리·제안·BOUNCE·일시정지. 아무도 매 회 읽지 않는다
├── tasks/NN.md            # task별 완료조건 (worker 작성, evaluator 검증)
├── handoffs/NN.md         # 다음 세션 핸드오프 (다음 세션이 첫 5분에 알아야 할 것만)
├── eval/NN-<ts>.md        # evaluator 판정 — 회차 1 = 파일 1 (정본). regress/final 모드는 이름이 다르다
├── audit/NN-<ts>.md       # auditor 체크포인트 분석 (B 회귀 · C 체크리스트 · D 문서 정리)
└── archive/               # 정리·재오픈으로 밀려난 원문 (삭제 대신 이동). archive/eval/는 재오픈 전 라운드의 회차 파일
```

**계약 파일 ↔ 로그 파일 분리**가 핵심이다. 매 회 읽히는 파일(goal·run-state·ownership·knowledge)은 작고 안정적이어야 하고, 시간순으로 쌓이는 것은 전부 로그(history·eval·audit·archive)로 간다. 둘 다 디스크라 compaction·세션 종료에도 무손실이고, 인간은 goal.md 하나만 봐도 현황을 읽는다. 누가 무엇을 읽고 쓰는지는 `loop-protocol.md` §자라는 상태의 읽기 계약 표가 정본이다.

**파일명 규칙**: `NN`(2자리, 마스터 체크리스트 번호)이 키다. `tasks/`·`handoffs/`는 task당 1개라 `NN.md`. `eval/`은 회차마다 1개라 `NN-<ts>.md`(`<ts>` = `date +%Y%m%d-%H%M%S`). **회차 파일 이름의 `NN-` 뒤는 반드시 숫자로 시작한다** — 드라이버·worker가 `^NN-[0-9]`로 회차를 센다. 모드 파일은 `NN-regress-<ts>.md`(auditor 회귀 재검증)·`final-<ts>.md`(최종 점검)로 회차에 안 잡힌다. `NN-partA`·`NN-c1c4` 같은 쪼개기 이름은 금지다.

**칸 규칙(모든 표 공통)**: 칸은 한 낱말 또는 한 줄. 설명·근거·경위는 로그 파일에 쓰고 칸에는 포인터만.

---

## goal.md

```markdown
# Goal: <목표 한 줄 제목>

> goal_dir: docs/goals/<slug>/ · domain: <code|writing|ops|research|...>
> created: YYYY-MM-DD · last_updated: YYYY-MM-DD HH:MM (<who>)

## 목표
<무엇을 왜 이루려는가. 2-5줄. 완성됐을 때의 상태로 서술.>

## 완수 조건 (Definition of Done)
- [공통] 아래 마스터 체크리스트 전 항목 완료
- [최종·옵션] <결과/동작 기준 — 도메인별. 검증 방법 명시. 3~5개 이내.
  예) "전체 테스트 스위트 통과 (`<명령>`)" / "목차 전체가 루브릭 X 충족" /
      "산출물 목록 전부 존재 + 상호 정합". 없으면 "공통 조건만">

## 공통 컨텍스트 (매 세션 주입)
<모든 세션이 알아야 할 안정적 사실만. 매 worker·evaluator가 읽는다 — 타이트하게.
 도메인 배경, 제약, 대상, 톤/스타일/기술스택, 확정 결정, 비범위(non-goals).
 절차 교훈·우회책·루프 규약은 여기 아니다 — knowledge.md 운영 노트 / 플러그인 정본.>

## 마스터 체크리스트 (각 항목 = 세션 1개, 한 줄)
<상태 표기: [ ] 대기 · [~] 진행중 · [x] 완료 · [!] blocked>
- [ ] 01 — <task 한 줄> · 산출물: <무엇> · 수용 힌트: <끝나면 무엇이 참이어야>
- [ ] 02 — <...> · (의존: 01)
- [ ] 03 — <...>

## 인덱스
- 런타임: run-state.md · 소유 맵: ownership.md · 지식: knowledge.md · 이력: history.md
- 완료조건: tasks/ · 핸드오프: handoffs/ · 평가: eval/ · 감사: audit/ · 보관: archive/
```

마스터 체크리스트 작성이 가장 중요하다 — **각 항목 하나가 한 세션의 목표**다. 항목은 한 줄이다(상세는 tasks/NN.md). 크기 기준은 `goal-design/references/task-sizing.md`. 변경 이력은 goal.md에 두지 않는다 — history.md로.

---

## run-state.md (드라이버 전용)

```markdown
# Run State — <slug>

> 드라이버만 쓴다. 매 반복 read→write. worker는 캡 값만 읽는다. 칸은 정수 또는 한 줄.

## 캡·노브 (방어막)
- max_iterations: <N>
- max_minutes: <M>
- per_task_attempt_limit: 3      # task 라운드당 evaluator 회차·worker dispatch 각각의 상한
- per_dispatch_minutes: <N>      # worker 한 번의 활성 시간 상한. goal-design이 task 예상 소요×2로 시드, auditor가 실측(완료 task 분 중앙값×2)으로 갱신
- checkpoint_every: 4            # auditor 체크포인트 주기 (task 수)
- major_changes_budget: 3        # 파괴적 체크리스트 변경 허용 횟수
- stall_limit: 3                 # 연속 dispatch에 새 [x] 0 → 정지
- started_at: <설정/첫 실행 시각>

## 카운터
- status: running                # running · paused · complete (complete면 재실행은 보고만 한다)
- iterations_used: 0             # worker dispatch 수 (auditor는 아래 체크포인트 기록에)
- elapsed_minutes: 0             # 활성 시간 합 (tick 방식, 분 반올림)
- last_tick: —                   # YYYY-MM-DD HH:MM:SS. 재개 시 now로 리셋(더하지 않음)
- current_task: —                # 진행중 task ID (크래시 복구용)
- dispatched_at: —               # 현재 dispatch 시각
- done_since_checkpoint: 0
- last_checkpoint: —             # 지난 체크포인트의 마지막 완료 task
- checkpoint_requested: —        # 계획 문제 BLOCKED(task-too-big 등) 시 사유 → 다음 반복에 체크포인트
- major_changes_used: 0
- stall_streak: 0                # 연속 무진전 dispatch 수

## task 상태
| task | 상태 | 디스패치 | 시도 | 분 | 토큰k | 결과(한 토막) |
|------|------|---------|------|----|-------|------------|
| 01 | pending | 0 | 0 | 0 | 0 | — |

## 체크포인트 기록 (auditor 비용 — 비용 요약에 포함)
| @task | 사유 | 분 | 토큰k | 델타 한 토막 |
|-------|------|----|-------|-------------|

## BLOCKED 사유 로그 (패턴 감지 — 같은 사유 K회면 사람 호출)
| task | 정규화 사유 | ts |
|------|------------|----|
```

상태: `pending · running · done · blocked · reopened`. **시도** = `ls eval | grep -cE '^NN-[0-9]'`(드라이버가 매번 덮어쓴다 — worker 신고가 아니다). **디스패치** = 이 라운드에 띄운 worker 수(재개 포함). **분·토큰k** = Agent 결과에 붙는 소요·토큰의 라운드 누적(분 반올림, 없으면 —). **결과** 칸은 `APPROVED`·`BLOCKED:<사유>`·`PARTIAL:time-budget`·`unverified-done`·`기록누락`·`over-time`처럼 한 토막 — 경위는 history.md·eval/에. 체크포인트(auditor) 비용은 task 행이 아니라 체크포인트 기록에 — 인계 보고의 비용 요약은 둘을 합친다.

---

## ownership.md

```markdown
# Ownership — <slug> (산출물 소유 맵)

> worker가 완료 시 행 추가. evaluator·auditor가 표적 회귀에 쓴다. 한 산출물 = 한 행. 칸은 한 낱말 — 설명은 쓰지 않는다.
> 같은 디렉토리의 파일 여럿은 글롭 한 행으로 묶어도 된다. 다른 task가 나중에 손대면 그 행의 공유 칸에 task를 덧붙인다.

| 산출물(경로/글롭) | 소유 task | 공유 |
|---|---|---|
| <경로> | 01 | 단독 |
| <경로> | 01 | 공유:03,07 |
```

---

## knowledge.md

```markdown
# Knowledge — <slug>

> 다음 worker가 재조사 없이 일하는 데 필요한 것만. 항목은 **갱신**한다(중복·구식 제거) — 맹목 append 금지.
> 사실엔 원문 전사 대신 포인터(파일:라인 / URL / 명령). 판정 질문: "다음 worker가 매번 읽어야 할 만큼 항구적인가?" — 특정 영역에서만 필요하면 knowledge/<영역>.md로, 한 번만 필요하면 handoff로, 경위·원문이면 archive로.
> 아래 섹션은 도메인에 맞게 design 단계가 시드한다 (예시 골격).

## 확정 사실 / 근거
## 컨벤션 / 용어 / 톤
## 핵심 결정 (+ 근거)
## 함정 / 주의
## 구조 맵 (산출물 ↔ 위치)
## 운영 노트 (절차 교훈 — 근거 필수 · auditor가 반증/무근거 항목을 은퇴시킨다)
## 미해결 / 추가 조사 필요
```

**영역 파일(knowledge/<영역>.md)**: 지식이 여러 영역(예: 장별 사실 / 문체 규칙 / 구조 맵 / 도구 함정)으로 갈리고 task마다 필요한 영역이 다르면, 영역별 파일로 나누고 knowledge.md는 색인이 된다 — 영역 파일 표(`파일 | 무엇이 들어 있나 | 누가 언제 여는가`) + 운영 노트. worker는 자기 task에 걸리는 영역만 연다. 나누는 기준은 "매번 다 읽을 필요가 없어졌는가"이지 크기가 아니다.

**knowledge ↔ handoff 경계** (둘 다 쓰되 중복하지 않기): knowledge는 **항구적**이다 — 목표 내내 유효한 사실·결정·컨벤션·구조. handoff는 **휘발성**이다 — "방금 한 일 + 바로 다음 세션을 위한 일회성 주의"이며 최신 1-2개만 읽힌다. 같은 내용을 양쪽에 쓰지 마라. 판정 질문: "다음 worker가 매번 읽어야 할 만큼 항구적인가?" 아니면 영역 파일/archive.

---

## history.md (append-only 로그)

```markdown
# History — <slug> (append-only)

> 시간순 로그. 아무도 매 회 읽지 않는다 — 사람과 auditor가 필요할 때 본다. 한 사건 = 한 줄.
> 형식: `- <ts> · <역할> · <종류> · <내용>`  종류: 체크리스트변경(major 표시) · 재오픈 · 정리 · 은퇴 · 제안 · BOUNCE · 일시정지/재개 · 캡변경 · 이행 · 완료
> `제안`은 worker도 쓴다(계획 수준 변경 제안 — auditor가 다음 체크포인트에 처리). 나머지는 드라이버·auditor.
```

---

## tasks/NN.md

```markdown
# Task NN: <제목>

> worker가 작업 전 작성. evaluator가 이 파일을 정본으로 검증.
> 완료조건 규칙(loop-protocol §완료조건): 산출물 술어만 · 필요한 만큼만(10개 넘으면 신호) · 검증은 명령/대조 대상 · 고정점 · 하네스 기록 제외 · 진입점 하나로 접기

## 완료조건
| # | 조건 (산출물에 대한 술어) | 검증 (명령 / 대조 대상) |
|---|---|---|
| C1 | <조건> | `<명령>` 종료코드 0 |
| C2 | <조건> | `<파일>`에 <X>가 N개 (grep) |

## 산출물
<이 task가 만들/바꿀 경로>

## 작업 노트
<이 task 한정 메모. 짧게 — 실측 원문·전사는 붙이지 않는다(evaluator가 직접 잰다).>
```

---

## handoffs/NN.md

```markdown
# Handoff NN → 다음 세션

> 다음 세션이 첫 5분에 알아야 할 것만. 최신 1-2개만 본문 로드된다.

- 한 일: <요약>
- 바뀐 산출물: <목록>
- 다음이 알아야 할 것 / 함정: <...>
- 미완 / 이어서 할 것: <...>
```

---

## eval/NN-<ts>.md (회차 정본)

```markdown
# Eval — Task NN — <ts>

> 독립 평가. 호출자 주장 불신. **파일을 먼저 만들고**(판정 PENDING) 조건을 잴 때마다 갱신한다 — 평가자가 죽어도 진행이 남는다.

## 판정: PENDING
<최종: APPROVED | NEEDS_REVISION. NEEDS_REVISION이면 무엇을 어떻게 고쳐야 하는지 구체적으로. 이 줄은 파일에 하나뿐이다 — 드라이버가 grep한다>

## 조건별 판정
| # | 판정 | 근거 (실측 인용: 명령 결과 / URL·출처 / 파일:라인 / `git diff`) |
|---|---|---|
| C1 | PASS·FAIL·WARN | ... |

## 표적 회귀
<이전 task 영향 조건 재검증 결과. 없으면 "해당 없음">

## 조건 적정성
<조건이 task를 충분히 커버하는가. 느슨·누락이면 지적(NEEDS_REVISION 사유).
 하네스 기록·자기지시·과분할 조건은 판정에서 제외하고 여기 적는다.>
```

---

## audit/NN-<ts>.md

> auditor가 체크포인트마다 Write. 상세는 여기 남기고 드라이버엔 concise 델타만 반환한다. NN = 체크포인트 시점의 마지막 완료 task — *언제* 감사했는지를 가리키는 순번이지, 발견 대상 task가 아니다.

```markdown
# Audit — checkpoint @ task NN — <ts>

> 범위: 지난 체크포인트(task MM) 이후 델타. 목표·완수조건은 평가 대상이 아니다(고정 계약).

## B 전역 회귀
- [OK|REGRESSED] task KK — <근거: 어떤 산출물이 어느 task에 의해 깨졌나 / 실측 인용>
재오픈 권고: <task 목록 + 한 줄 사유>  (없으면 "없음")

## C 체크리스트 재검증
남은 task가 knowledge·산출물에 비춰 타당한가: <요약>
변경 권고:
- [추가|분할|정제] <task> — <무엇/왜>             (자율 적용)
- [삭제|재범위|순서] <task> — <무엇/왜> · major    (예산 차감)
(없으면 "없음")

## D 문서 정리
- 비용 추세: 이번 구간 평균 시도 <n> · 분 <n> · 토큰k <n> vs 직전 구간 <...> — <오르고 있으면 원인 추정 + 처방(정리/정제), 아니면 "정상">
- 정리: <읽기 세트에서 무엇을 어디로 옮겼나 (영역 파일 / archive) · 표 칸 산문 정리> (없으면 "불필요")
- 운영 노트: <은퇴 항목 + 사유> (없으면 "없음")
- 기록 누락 보정: <task + 무엇을 재구성했나> (없으면 "없음")

## 드라이버 델타 (concise — 이것만 반환)
- 재오픈: <task 목록 또는 없음>
- 체크리스트: <변경 목록 또는 없음> · major <n>건
- 문서 정리: <옮김 n건 · 은퇴 n건 · 비용 추세 정상/악화(원인) · run-state 정리 요청 여부 또는 없음>
```
