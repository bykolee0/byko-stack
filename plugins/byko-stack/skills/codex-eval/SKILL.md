---
name: codex-eval
description: OpenAI Codex CLI를 사용하여 독립된 모델/컨텍스트에서 문서/코드를 평가하는 스킬. Claude와 다른 모델의 시각으로 교차검증한다. 스펙, 구현 계획, 구현 결과 등의 독립 평가가 필요할 때 사용한다. "/codex-eval spec docs/specs/project/spec.md", "/codex-eval plan plan.md --output eval-results/plan-codex.md", "/codex-eval --cross eval-results/spec-claude-xxx.md" (교차검증) 등으로 트리거. eval-gate의 evaluator 평가와 함께 사용하면 두 모델의 평가를 비교할 수 있다.
argument-hint: "[mode] [target files...] [--output path] [--cross path]"
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Codex-Eval: 교차 모델 독립 평가

OpenAI Codex CLI를 사용하여 다른 모델의 시각으로 평가한다.
Claude와 다른 모델(OpenAI)이므로 편향이 다르고, 이것이 교차검증의 핵심 가치다.

요청/응답 포맷은 evaluator(eval-gate)의 결과 포맷과 호환된다 — 같은 파일을 공유할 수 있으며,
한 파일에서 두 모델의 평가를 비교할 수 있다.

---

## 사용법

```
/codex-eval spec docs/specs/project/spec.md
/codex-eval plan docs/specs/project/plan.md --output docs/specs/project/eval-results/plan-codex-20260326-1430.md
/codex-eval implementation docs/specs/project/spec.md src/
/codex-eval custom docs/any-document.md
/codex-eval .myagents/existing-request.md                                        # 기존 요청 파일 재실행
/codex-eval --cross eval-results/spec-claude-20260326-143052.md                  # evaluator 결과에 codex 교차검증 추가
```

| 인자 | 필수 | 설명 |
|------|------|------|
| mode | O | `spec`, `plan`, `implementation`, `custom` |
| target files | O | 평가 대상 파일 경로 (1개 이상) |
| `--output <path>` | X | 결과 파일 저장 경로. 생략 시 `.myagents/codex-eval-<timestamp>.md` |
| `--cross <path>` | X | 교차검증: 기존 eval 결과 파일에 codex 평가 추가 |

`--cross`와 `--output`은 동시 사용 불가.

---

## 이 스킬이 트리거되면

### Step 1: Pre-flight

```bash
command -v codex >/dev/null 2>&1 || { echo "codex not found"; exit 1; }
```

codex가 없으면 중단: "codex CLI를 설치해주세요: `npm install -g @openai/codex && codex login`"

### Step 2: 실행 모드 판별

| 조건 | 모드 | 동작 |
|------|------|------|
| `--cross <path>` 있음 | **교차검증** | 기존 파일에 CODEX_EVAL_RESPONSE 마커 추가 후 평가 |
| 첫 인자가 기존 eval 요청 파일 (`# Evaluation Request` 헤더 존재) | **재실행** | 기존 파일 그대로 사용 |
| 그 외 | **신규 평가** | 새 요청 파일 생성 후 평가 |

### Step 3: 결과 파일 경로 결정

```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
```

| 모드 | REQUEST_FILE |
|------|-------------|
| 신규 + --output | `--output` 경로 (mkdir -p 자동) |
| 신규 (기본) | `.myagents/codex-eval-${TIMESTAMP}.md` |
| 재실행 | 기존 파일 경로 |
| 교차검증 | `--cross` 파일 경로 |

### Step 4: 요청 파일 준비

**신규 평가**: `references/request-template.md` 포맷으로 작성한다.
- Source Documents에는 가능한 한 **문서 내용을 copy**한다 (codex sandbox에서 파일 접근 제한)

**재실행**: 기존 파일 그대로 사용.

**교차검증**: 기존 파일 끝에 `CODEX_EVAL_RESPONSE` 마커 추가.

### Step 5: codex 실행

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  "<task>
$(pwd)/$REQUEST_FILE 파일을 읽어라.
이 파일에는 Evaluation Request가 담겨 있다.
Source Documents에 복사된 문서 내용과 Evaluation Criteria 체크리스트를 기반으로 각 항목을 평가하라.
결과를 같은 파일의 응답 마커(<!-- EVAL_RESPONSE_START --> ~ <!-- EVAL_RESPONSE_END -->) 사이에 작성하라.
</task>

<structured_output_contract>
응답 형식:

### [체크리스트 섹션명]
- [PASS|FAIL|WARN] 항목명 — 1줄 근거 (Source Documents 또는 실제 코드의 구체적 내용 인용)

### 개선 제안
체크리스트의 "개선 제안의 운영 원칙"을 따른다. 네 조건을 전부 만족하는 제안이 있을 때만 작성하고, 없으면 "해당 없음"이라고만 쓴다. 출력 포맷은 체크리스트 참고 (대상/현재/제안/근거/영향).

### 전체 판정
- 판정: APPROVED | NEEDS_REVISION
- NEEDS_REVISION인 경우: FAIL 항목별 구체적 수정 제안

각 판정에는 반드시 Source Documents 또는 코드에서 확인한 근거를 포함할 것.
근거 없는 판정은 작성하지 않는다.
</structured_output_contract>

<grounding_rules>
모든 판단은 실제 파일 내용(Source Documents + Target Files)에 기반한다. 추측하지 않는다.

문서만 보고 판단하지 않는다 — 스펙/계획/구현은 모두 코드베이스 위에 성립한다. 평가자는 문서의 주장을 검증할 뿐 아니라, 주장이 없어도 Target Files(코드베이스)를 능동적으로 스캔한다:
- 주장 검증: 'N곳에서 사용된다' → Grep으로 세어 확인 / '기존 패턴은 X' → 실제 코드 확인 / '영향 범위는 A, B' → 호출 체인 추적
- 능동 확인: 대상 영역 주변 모듈/호출 체인을 Glob/Grep으로 스캔하여 문서가 놓친 영향 지점 탐색
- plan에 코드 스니펫·API 호출·함수 시그니처가 포함되면 실제 코드와 대조 (존재하지 않는 API, 잘못된 시그니처)
- implementation 평가는 스펙 준수 체크에 머물지 않고 로직 정확성(엣지케이스, 오류 경로, 동시성, 리소스, 보안)까지 판단

sandbox 제약으로 확인이 불가능한 경우에만 WARN으로 표기하고 사유를 명시한다.
</grounding_rules>

<verification_loop>
FAIL 판정 전, 다음을 확인한다:
1. 해당 내용이 Source Documents에 정말 누락/오류인지 다시 읽어 확인
2. 다른 섹션에 관련 내용이 있지 않은지 교차 확인
3. 근거가 구체적인지 (막연한 '불충분' 대신 무엇이 빠졌는지 명시)
확인 없이 FAIL을 내리면 false positive가 되어 평가의 가치가 떨어진다.
</verification_loop>" \
  < /dev/null 2>/dev/null
```

**필수 플래그**: `--skip-git-repo-check`, `--sandbox workspace-write`, `< /dev/null`

**중요**: 이 명령은 오래 걸릴 수 있다 (3-20분). Bash 실행 시 `run_in_background: true`로 실행한다. 기본 타임아웃(2분)으로 실행하면 평가 도중 잘린다. 백그라운드 실행 시 완료 알림이 자동으로 온다.

### Step 6: 결과 확인

응답 마커 사이를 읽는다.

**응답이 비어있을 때**: 바로 재시도하지 않는다. 먼저 원인을 확인한다:
- 요청 파일이 정상적으로 작성되었는가? (Read로 확인)
- codex가 에러 없이 종료되었는가?
- 원인을 파악한 후 1회만 재시도한다. 재시도해도 실패하면 유저에게 보고한다.

### Step 7: 결과 검증 및 보고

FAIL 항목을 직접 확인하여 `accepted`/`rejected`/`needs_followup` 분류.

**교차검증 시 추가 비교:**
- 두 모델 동시 FAIL → **높은 확신도 문제** (우선 수정)
- 한 모델만 FAIL → 추가 확인 필요
- 두 모델 PASS → 높은 확신도 통과

### Step 8: 유저에게 보고

**유저가 다른 파일을 열지 않고도 판단할 수 있도록** 각 항목에 충분한 컨텍스트를 포함한다:
- 해당 내용이 무엇에 대한 것인지 (항목 번호만이 아니라 실제 내용 설명)
- 현재 스펙/코드에 뭐라고 쓰여 있는지 (실제 문구 인용)
- 무엇이 문제인지, 어떻게 수정하면 되는지

분류별 제시:
- `accepted`: 문제와 수정 방향을 구체적으로
- `rejected`: 간단히 사유 언급
- `needs_followup`: 선택지를 제시하여 유저 판단 요청
- 전체 판정(APPROVED/NEEDS_REVISION) 명시
- **결과 파일 경로를 반드시 알린다**
- 교차검증 시 비교 결과 포함

📍 **eval-gate에서 호출된 경우**: eval-gate로 결과를 반환한다.
📍 **직접 호출된 경우**: 판정에 따라 다음 단계를 안내한다.

---

## 교차검증 지원

```
# evaluator(eval-gate) 먼저 → codex 교차검증
/eval-gate spec spec.md                      # eval-results/spec-claude-<ts>.md 생성
/codex-eval --cross eval-results/spec-claude-<ts>.md

# codex 단독 → eval-gate에서 교차검증 요청
/codex-eval spec spec.md --output eval-results/spec-codex.md
```

eval-gate가 교차검증 모드로 호출하면 evaluator와 병렬로 실행된다.

---

## 에러 처리

| 상황 | 조치 |
|------|------|
| codex 미설치 | `npm install -g @openai/codex && codex login` 안내 |
| 비정상 종료 | 에러 내용 보고, 수동 실행 제안 |
| 응답 비어있음 | 원인 확인 후 1회 재시도. 바로 재시도하지 않는다 |
| --output 디렉토리 없음 | mkdir -p 자동 생성 |
| --cross + --output 동시 | 에러 메시지 |
