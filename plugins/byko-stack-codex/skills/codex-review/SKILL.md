---
name: codex-review
description: Codex 내부에서 스펙, 계획, 구현 결과를 독립적으로 검토하는 리뷰 스킬. codex-eval-gate가 외부 codex CLI 대신 호출하거나, 사용자가 "Codex subagent로 리뷰", "스펙 검토", "구현 독립 검증", "plan review"를 요청할 때 사용한다. 가능한 경우 subagent를 사용하고, 불가능하면 같은 컨텍스트 리뷰로 낮은 신뢰도 결과를 저장한다.
---

# Codex Review

외부 `codex exec`를 재귀 호출하지 않고 Codex 환경 안에서 독립 검토를 수행한다. 핵심은 현재 작업자의 결론을 그대로 믿지 않고, 파일과 코드 근거만으로 다시 판단하는 것이다.

## Workflow

### 1. 입력 파악

지원 모드:
- `spec`
- `plan`
- `implementation`
- `custom`

출력 경로가 없으면 다음을 사용한다.

```text
docs/specs/<project>/eval-results/<mode>-codex-review-<timestamp>.md
```

프로젝트 경로를 추론할 수 없으면 `.myagents/codex-review-<timestamp>.md`를 사용한다.

### 2. 요청 파일 작성

`references/request-template.md`와 `references/checklists.md`를 사용한다.

요청 파일에는 다음을 포함한다.
- 평가 모드
- 대상 파일 목록
- 모드별 체크리스트
- spec/plan/traceability/ledger 문서 내용 복사
- implementation 모드에서는 변경 파일 경로와 테스트 결과

문서 전체를 복사하면 subagent가 파일 접근에 실패해도 평가할 수 있다. 단, 구현 평가는 실제 코드도 읽어야 하므로 변경 파일 경로를 함께 적는다.

### 3. 리뷰 실행

현재 환경에서 subagent 사용이 허용되고 도구가 있으면 explorer 또는 default subagent를 사용한다. 프롬프트는 기대 결론을 누설하지 말고 다음처럼 최소화한다.

```text
Use the evaluation request at <absolute request path>.
Read the target files listed in it.
Evaluate according to the checklist.
Write the result into the response marker in the same file.
Base every FAIL on concrete file/code evidence.
```

subagent 사용이 허용되지 않거나 도구가 없으면 같은 컨텍스트에서 평가한다. 이 경우 결과에 `confidence: low`를 표시한다.

### 4. 리뷰 결과 검증

subagent 또는 self-review 결과를 그대로 믿지 않는다. FAIL 항목을 직접 확인하고 분류한다.

- `accepted`: 근거가 타당하고 수정 필요
- `rejected`: 오탐 또는 맥락 부족
- `needs_followup`: 타당할 수 있으나 사용자 결정이 필요

검증 결과를 Caller Notes에 기록한다.

### 5. 출력 형식

```markdown
# Codex Review Result: <mode>

## 판정: APPROVED | NEEDS_REVISION
- confidence: high | medium | low

## Findings
### Accepted
- ...

### Rejected
- ...

### Needs Follow-up
- ...

## Checklist Result
### <section>
- [PASS|FAIL|WARN] <item> - <근거>

## Caller Notes
- ...
```

사용자에게는 핵심 finding, 판정, 결과 파일 경로, 다음 단계를 보고한다.

## Review Rules

- 문서만 보고 판단하지 않는다. 코드베이스 주장과 실제 코드를 대조한다.
- 구현 평가는 스펙 준수, 로직 정확성, 엣지케이스, 실패 경로, 회귀 위험을 모두 본다.
- 개선 제안은 완전성/정확성/안전성을 높이는 경우에만 한다.
- 취향, 네이밍 선호, 범위 확장 제안은 제외한다.
- FAIL 전에는 관련 파일을 다시 읽어 false positive를 줄인다.

## References

- `references/checklists.md`
- `references/request-template.md`
