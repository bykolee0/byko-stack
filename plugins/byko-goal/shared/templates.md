# 문서 세트 템플릿

`docs/goals/<slug>/`의 산출물 형태. goal-design이 생성하고, 매 세션이 갱신한다. `<slug>`는 한 프로젝트 안에서 목표끼리 충돌하지 않게 하는 키다.

```
docs/goals/<slug>/
├── goal.md          # 헌장: 목표·완수조건·공통 컨텍스트·마스터 체크리스트·인덱스 (의미 상태 SSOT)
├── run-state.md     # 캡·카운터·task 상태 (기계 상태 SSOT, 드라이버가 매 반복 갱신)
├── knowledge.md     # 누적 분석 (worker가 갱신, 재분석 방지)
├── tasks/NN.md            # task별 완료조건 (worker 작성, evaluator 검증)
├── handoffs/NN.md         # 다음 세션 핸드오프
└── eval/NN-<ts>.md        # evaluator 독립 판정 (재시도마다 1개 → ts로 구분)
```

**의미 상태(goal.md) ↔ 기계 상태(run-state.md) 분리**가 핵심이다. 둘 다 디스크라 compaction·세션 종료에도 무손실이고, 인간은 goal.md 하나만 봐도 현황을 읽는다.

**파일명 규칙**: `NN`(2자리, 마스터 체크리스트 번호)이 키다. `tasks/`·`handoffs/`는 task당 1개라 `NN.md`로 충분하다. `eval/`은 한 task가 재시도로 여러 번 평가될 수 있어 타임스탬프를 붙여 `NN-<ts>.md`로 구분한다. 가독성을 위해 `NN-<slug>.md`처럼 슬러그를 덧붙여도 되지만 **선택**이다 — 도구는 `NN`만으로 매칭한다.

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
- [최종·옵션] <결과/동작 기준 — 도메인별. 검증 방법 명시.
  예) "전체 테스트 스위트 통과 (`<명령>`)" / "목차 전체가 루브릭 X 충족" /
      "산출물 목록 전부 존재 + 상호 정합". 없으면 "공통 조건만">

## 공통 컨텍스트 (매 세션 주입)
<모든 세션이 알아야 할 안정적 사실만. 타이트하게 — 매 worker가 읽는다.
 도메인 배경, 제약, 대상, 톤/스타일/기술스택, 확정 결정, 비범위(non-goals).>

## 마스터 체크리스트 (각 항목 = 세션 1개)
<상태 표기: [ ] 대기 · [~] 진행중 · [x] 완료 · [!] blocked>
- [ ] 01 — <task 한 줄> · 산출물: <무엇> · 수용 힌트: <끝나면 무엇이 참이어야>
- [ ] 02 — <...> · (의존: 01)
- [ ] 03 — <...>

## 인덱스
- 런타임 상태: run-state.md · 누적 지식: knowledge.md
- 완료조건: tasks/ · 핸드오프: handoffs/ · 평가: eval/

## 발견된 변경 제안 (append-only)
<세션이 마스터 계획의 결함·누락을 발견하면 제안만 적는다.
 구조적 재계획은 사람 확인을 거친다 — 세션이 마음대로 계획을 갈아엎지 않는다.>
```

마스터 체크리스트 작성이 가장 중요하다 — **각 항목 하나가 한 세션의 목표**다. 너무 크면 한 worker 컨텍스트에 안 들어오고, 너무 잘면 세션 오버헤드가 커진다. 크기 기준은 `goal-design/references/task-sizing.md`.

---

## run-state.md

```markdown
# Run State — <slug>

> 드라이버가 매 반복 read→write. 기계 상태 SSOT. 캡은 컨텍스트가 아니라 여기 살아야 한다.

## 캡 (방어막)
- max_iterations: <N>
- max_minutes: <M>
- per_task_attempt_limit: 3
- started_at: <설정/첫 실행 시각>

## 카운터
- iterations_used: 0
- elapsed_minutes: 0
- current_task: —   # 진행중 task ID (크래시 복구용)

## task 상태
| task | 상태 | 시도 | 마지막 결과 한 줄 |
|------|------|------|------------------|
| 01 | pending | 0 | — |

## BLOCKED 사유 로그 (패턴 감지)
<드라이버가 정규화 사유를 한 줄씩 누적. 같은 사유 K회 → 사람 호출>
```

---

## knowledge.md

```markdown
# Knowledge — <slug> (누적 분석)

> 세션이 새로 분석/개선한 것만 갱신한다. 재분석 방지용. 요약체 — 원문·전사 금지.
> 아래 섹션은 도메인에 맞게 design 단계가 시드한다 (예시 골격).

## 확정 사실 / 근거
## 컨벤션 / 용어 / 톤
## 핵심 결정 (+ 근거)
## 함정 / 주의
## 구조 맵 (산출물 ↔ 위치)
## 미해결 / 추가 조사 필요
```

knowledge는 무한정 자라면 매 worker의 컨텍스트를 잠식한다. 항목을 **갱신**(중복·구식 제거)하지 맹목 append하지 않는다.

**knowledge ↔ handoff 경계** (둘 다 쓰되 중복하지 않기): knowledge는 **항구적**이다 — 목표 내내 유효한 사실·결정·컨벤션·구조. handoff는 **휘발성**이다 — "방금 한 일 + 바로 다음 세션을 위한 일회성 주의"이며 최신 1-2개만 읽힌다. 같은 내용을 양쪽에 쓰지 마라: 다음 세션 이후로도 유효하면 knowledge로, 직후 한 번만 쓸모 있으면 handoff로 보낸다.

---

## tasks/NN-<slug>.md

```markdown
# Task NN: <제목>

> worker가 작업 전 작성. evaluator가 이 파일을 정본으로 검증.

## 완료조건 (체크리스트 안의 체크리스트)
<각 조건은 검증 가능해야 하고 '검증 방법'을 동반한다. 도메인에 맞게.>
- [ ] <조건> — 검증: <명령 실행 / 출처 대조 / 산출물 실측 / 기준 대조>
- [ ] <조건> — 검증: <...>

## 산출물
<이 task가 만들/바꿀 것>

## 작업 노트
<이 task 한정 메모>
```

---

## handoffs/NN-<slug>.md

```markdown
# Handoff NN → 다음 세션

> 짧게. 최신 1-2개만 본문 로드된다.

- 한 일: <요약>
- 바뀐 산출물: <목록>
- 다음이 알아야 할 것 / 함정: <...>
- 미완 / 이어서 할 것: <...>
```

---

## eval/NN-<ts>.md

```markdown
# Eval — Task NN — <ts>

> 독립 평가. 호출자 주장 불신. 검증 방법대로 직접 반증한다.

## 조건별 판정
- [PASS|FAIL] <조건> — 근거(실측 인용: 명령 결과 / URL·출처 / 산출물 위치·`git diff`)

## 조건 적정성
<tasks/NN.md 조건이 task를 충분히 커버하는가. 느슨하거나 빠진 게 있으면 지적.>

## 판정: APPROVED | NEEDS_REVISION
<NEEDS_REVISION이면 무엇을 어떻게 고쳐야 하는지 구체적으로>
```
