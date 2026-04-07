---
name: eval-gate
description: 스펙, 구현 계획, 구현 결과를 독립 컨텍스트에서 검증하는 품질 게이트 스킬. 내부적으로 /claude-eval과 /codex-eval을 호출하여 현재 대화의 편향 없이 평가하고, 결과를 종합하여 APPROVED/NEEDS_REVISION을 판정한다. "/eval-gate spec docs/specs/project/spec.md", "/eval-gate plan docs/specs/project/plan.md", "/eval-gate implementation docs/specs/project/spec.md src/" 등으로 트리거. spec-designer에서 스펙 완성 후, spec-dev에서 계획 수립 후, 구현 완료 후 등 단계 전환 시 이 스킬을 통과하면 다음 단계의 품질을 보장할 수 있다.
argument-hint: "[mode] [target files...]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, Skill
---

# Eval-Gate: 품질 검증 게이트

스펙/계획/구현의 품질을 독립적으로 검증하는 오케스트레이터다.
직접 평가하지 않고, `/claude-eval`과 `/codex-eval`을 호출하여 별도 컨텍스트에서 평가한 결과를 종합한다.

같은 대화 안에서 자기 산출물을 평가하면 확증 편향이 생긴다. 별도 프로세스에서 문서만 보고 평가해야 진짜 허점이 드러난다.

---

## 사용법

```
/eval-gate spec docs/specs/project/spec.md
/eval-gate plan docs/specs/project/implementation-plan.md
/eval-gate implementation docs/specs/project/spec.md src/
```

| 모드 | 호출 시점 | PASS 시 다음 단계 |
|------|----------|-----------------|
| **spec** | spec-designer 완료 후 | 📍 `/spec-dev` |
| **plan** | spec-dev 계획 수립 후 | 📍 구현 진행 |
| **implementation** | spec-dev 구현 완료 후 | 📍 완료 |

---

## 이 스킬이 트리거되면

### Step 1: 셀프 게이트 (비용 $0 — 구조적 사전 검증)

독립 평가 호출 전에, 파일 존재 여부와 필수 섹션 같은 기계적 판단을 먼저 수행한다.

#### mode: spec
- [ ] spec.md 파일이 존재하는가
- [ ] ambiguity-ledger.md가 존재하는가
- [ ] ledger에 `blocking` 항목이 0개인가
- [ ] AC 테이블이 존재하고, 모든 AC에 검증 방법이 있는가
- [ ] `assumed` ≤ 2, `open` ≤ 3인가

#### mode: plan
- [ ] implementation-plan.md 파일이 존재하는가
- [ ] spec.md가 존재하는가
- [ ] traceability.md가 있으면, 모든 AC가 매핑되었는가

#### mode: implementation
- [ ] spec.md가 존재하는가
- [ ] 관련 테스트 파일이 존재하는가
- [ ] 테스트가 통과하는가 (`bash`로 실행)

**셀프 게이트 FAIL 시**: 독립 평가를 호출하지 않고 바로 실패를 반환한다.
실패 사유와 수정 방법을 구체적으로 안내한다.

⏸️ 셀프 게이트 통과 시 유저에게 "구조 검증 통과. 독립 평가를 진행합니다." 안내 후 진행.

---

### Step 2: 평가 방식 확인

유저에게 평가 방식을 확인한다:

- **claude-eval만**: `claude -p` 독립 컨텍스트 평가
- **codex-eval만**: OpenAI Codex 독립 평가
- **둘 다 (교차검증)**: claude-eval 실행 후 codex-eval로 교차검증

⏸️ **유저 답변을 기다린다.**

---

### Step 3: 독립 평가 실행

```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SPEC_DIR="docs/specs/[project-name]"
mkdir -p "$SPEC_DIR/eval-results"
```

유저가 선택한 방식에 따라 Skill 도구로 호출한다.
스킬 미설치 시 유저에게 설치를 안내한다.

**claude-eval 실행 시:**
```
/claude-eval [mode] [target files] --output $SPEC_DIR/eval-results/[mode]-claude-${TIMESTAMP}.md
```

**codex-eval 실행 시:**
```
/codex-eval [mode] [target files] --output $SPEC_DIR/eval-results/[mode]-codex-${TIMESTAMP}.md
```

**둘 다 (교차검증) 시:**
```
/claude-eval [mode] [target files] --output $SPEC_DIR/eval-results/[mode]-claude-${TIMESTAMP}.md
/codex-eval --cross $SPEC_DIR/eval-results/[mode]-claude-${TIMESTAMP}.md
```

평가 완료 후 결과를 읽는다.

---

### Step 4: 결과 종합 및 판정

**단일 모델 평가 시:**

| 결과 | 판정 |
|------|------|
| 모든 항목 PASS | **APPROVED** |
| FAIL이 있지만 경미 | 유저에게 판단 위임 |
| FAIL 1개 이상 (구조적/의미적 문제) | **NEEDS_REVISION** |

**교차검증 시:**

| 결과 | 판정 |
|------|------|
| 두 모델 PASS | **APPROVED** (높은 확신) |
| 두 모델 FAIL | **NEEDS_REVISION** (높은 확신, 반드시 수정) |
| 한 모델만 FAIL | 유저에게 판단 위임 — 양쪽 근거를 함께 제시 |

---

### Step 5: 결과 저장 및 보고

```bash
GATE_RESULT="$SPEC_DIR/eval-results/[mode]-gate-${TIMESTAMP}.result.md"
```

결과 파일 형식:
```markdown
# Eval-Gate Result: [mode]

## 판정: APPROVED | NEEDS_REVISION
- 평가일시: YYYY-MM-DD HH:MM
- 평가 모드: spec | plan | implementation

## 상세 결과 파일
- claude-eval: [path]
- codex-eval: [path] (또는 미실행)

## claude-eval 요약
- PASS: N개, WARN: N개, FAIL: N개

## accepted 수정 사항 (NEEDS_REVISION인 경우)
1. ...

## needs_followup
1. ...
```

타임스탬프 포함이므로 여러 번 실행해도 이전 결과를 덮어쓰지 않는다.

---

### Step 6: 유저에게 보고

**보고의 원칙: 유저가 다른 파일을 열지 않고도 판단할 수 있어야 한다.**

각 finding을 보고할 때 다음을 포함한다:
- **무엇에 대한 것인지** — 항목 번호나 제목만이 아니라, 해당 내용이 무엇을 말하는지 충분히 설명
- **현재 스펙/코드에 뭐라고 쓰여 있는지** — 실제 문구나 코드를 인용
- **무엇이 문제인지** — 왜 수정이 필요한지, 어떤 모순/누락이 있는지
- **어떻게 수정하면 되는지** — 구체적 수정 방향 (accepted의 경우)
- **유저가 결정할 것** — 어떤 선택지가 있는지 (needs_followup의 경우)

---

### Step 7: 다음 단계 안내

**APPROVED 시:**

| 모드 | 다음 단계 |
|------|----------|
| spec | 📍 **Next: `/spec-dev docs/specs/[project]/spec.md`로 구현을 시작할 수 있습니다.** |
| plan | 📍 **Next: 계획이 확정되었습니다. 구현을 진행하세요.** |
| implementation | 📍 **Done: 구현이 검증되었습니다.** |

**NEEDS_REVISION 시:**

수정 사항과 함께 **어느 단계로 돌아가야 하는지** 안내한다:
- AC 문제, 구현 상세 부족 → `/spec-designer` Phase 4 (Draft)
- 요구사항 누락, 모호성 → `/spec-designer` Phase 3 (Clarification)
- 코드 분석 부족 → `/spec-designer` Phase 2 (Code Analysis)
- 구현 코드 문제 → `/spec-dev`에서 수정

---

## Notes

- eval-gate는 오케스트레이터이지 직접 평가하지 않는다
- 셀프 게이트는 비용이 없으므로 항상 수행한다
- 결과 파일은 보존하여 이력 관리에 활용한다
