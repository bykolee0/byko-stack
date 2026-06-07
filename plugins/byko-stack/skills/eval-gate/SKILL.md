---
name: eval-gate
description: 스펙, 구현 계획, 구현 결과를 독립 컨텍스트에서 검증하는 품질 게이트 스킬. byko-stack:evaluator 서브에이전트로 현재 대화의 편향 없이 평가하고 APPROVED/NEEDS_REVISION을 판정한다. 교차검증이 필요하면 codex-eval을 병행한다. "/eval-gate spec", "/eval-gate plan", "/eval-gate implementation", "검증해줘", "스펙 평가해줘", "독립 검증" 등으로 트리거. spec-designer/spec-dev의 단계 전환 시는 물론, 임의 문서·코드의 품질 검증이 필요한 모든 경우 단독으로도 사용한다.
argument-hint: "[mode] [target files...]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, Skill
---

# Eval-Gate: 품질 검증 게이트

스펙/계획/구현의 정합성을 독립 컨텍스트에서 검증한다. 직접 평가하지 않는다 — 같은 대화 안에서 자기 산출물을 평가하면 확증 편향이 생기므로, 격리된 컨텍스트의 `byko-stack:evaluator`가 문서와 코드만 보고 평가한다.

먼저 읽을 것: `../../shared/workflow.md`.

방향·성실성 리뷰(문제를 제대로 풀었는가)는 이 스킬이 아니라 `/review`의 몫이다. 이 스킬은 정합성(상위 산출물·코드베이스와 맞는가)을 본다.

---

## 사용법

```
/eval-gate spec [스펙 경로]
/eval-gate plan [계획 경로]
/eval-gate implementation [스펙 경로] [코드 경로]
/eval-gate custom [아무 문서] — 평가 기준을 함께 정의
```

경로 생략 시 매니페스트에서 해석한다 (workflow.md 탐색 규칙).

---

## 이 스킬이 트리거되면

### Step 1: 대상 해석 + 셀프 게이트 (비용 0 — 구조적 사전 검증)

인자 > 매니페스트 > 유저 확인 순으로 대상을 해석한 뒤, 기계적 사전 검증을 수행한다:

**mode: spec** — spec.md 존재 / ledger 존재 시 `blocking` 0개 / AC 테이블 존재 + 모든 AC에 검증 방법
**mode: plan** — plan 존재 / spec(또는 매니페스트의 AC) 존재 / traceability 있으면 모든 AC 매핑
**mode: implementation** — spec(또는 AC) 존재 / 관련 테스트 존재 / 테스트 통과 (Bash로 실행)

**FAIL 시**: 독립 평가를 호출하지 않고 실패 사유와 수정 방법을 구체적으로 안내한다.

통과 시 "구조 검증 통과. 독립 평가를 진행합니다." 안내 후 바로 진행한다 — 평가 방식을 매번 묻지 않는다.

### Step 2: 독립 평가 — evaluator 호출

`byko-stack:evaluator` 서브에이전트를 호출한다. 전달할 것:

- 평가 모드와 대상 파일 경로
- 맥락: 매니페스트의 **문제 정의**와 **핵심 결정** 발췌 — 이것만. **현재 세션의 결론·기대·"아마 통과할 것" 같은 뉘앙스를 절대 누설하지 않는다**
- 결과 저장 경로: `<작업 디렉토리>/eval-results/<mode>-claude-<timestamp>.md` (매니페스트가 없으면 대상 옆에 `eval-results/`)
- custom 모드면 합의한 평가 기준

**교차검증**: 유저가 요청했거나, 직전 평가가 논쟁적이었거나, 되돌리기 어려운 변경(스키마, 공개 API)인 경우 `/codex-eval`을 evaluator와 **병렬로** 실행한다. 그 외에는 evaluator 단독이 기본 — 보고 시 교차검증 옵션을 안내만 한다.

### Step 3: 결과 검증

evaluator의 판정을 그대로 신뢰하지 않는다. FAIL 항목의 근거를 직접 확인하여 분류한다:

- `accepted` — 근거가 타당한 지적
- `rejected` — 오탐 (근거 파일을 직접 확인하여 반박 가능)
- `needs_followup` — 타당하지만 유저 판단 필요

**판정:**

| 결과 | 판정 |
|------|------|
| accepted FAIL 0개 | **APPROVED** |
| accepted FAIL 있으나 전부 경미 | 유저에게 판단 위임 |
| accepted FAIL에 구조적/의미적 문제 | **NEEDS_REVISION** |

**교차검증 시**: 두 모델 동시 FAIL → 높은 확신으로 수정 / 한쪽만 FAIL → 양쪽 근거를 함께 제시하고 유저 판단 / 두 모델 PASS → 높은 확신의 APPROVED.

### Step 4: 기록 + 보고

게이트 결과를 `eval-results/<mode>-gate-<timestamp>.result.md`로 저장한다 (판정, 상세 결과 파일 경로, accepted 수정 사항, needs_followup). 매니페스트가 있으면 eval 결과 상태를 갱신한다.

**보고 원칙: 유저가 다른 파일을 열지 않고 판단할 수 있어야 한다.** 각 finding에:

- 무엇에 대한 것인지 (항목 번호가 아니라 내용 설명)
- 현재 스펙/코드에 뭐라고 쓰여 있는지 (실제 인용)
- 무엇이 문제이고 어떻게 수정하면 되는지
- needs_followup이면 선택지 제시

### Step 5: 다음 단계 안내

**APPROVED**: spec → 📍 `/spec-dev` / plan → 📍 구현 진행 / implementation → 📍 완료 또는 `/review`로 fresh-eyes 리뷰

**NEEDS_REVISION**: 어느 단계로 돌아갈지 안내한다 —

- AC 문제, 요구사항 누락·모호 → `/spec-designer`
- 계획의 영향 범위·순서 문제 → `/spec-dev` 계획 수정
- 구현 코드 문제 → `/spec-dev`에서 수정

수정 후 재실행하면 타임스탬프로 이력이 보존된다.

---

## Notes

- eval-gate는 오케스트레이터다 — 직접 평가하지 않는다
- 셀프 게이트는 비용이 없으므로 항상 수행한다
- evaluator에게 결론을 누설하는 순간 독립 평가의 가치가 사라진다
