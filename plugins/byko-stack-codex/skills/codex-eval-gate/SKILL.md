---
name: codex-eval-gate
description: Codex에 최적화된 스펙, 구현 계획, 구현 결과 품질 게이트. "/codex-eval-gate spec docs/specs/project/spec.md", "/codex-eval-gate plan docs/specs/project/implementation-plan.md", "/codex-eval-gate implementation docs/specs/project/spec.md src/" 요청에서 사용한다. 외부 codex CLI 재호출 대신 Codex subagent 기반 codex-review와 선택적 claude-eval을 조합해 독립 검증하고 APPROVED 또는 NEEDS_REVISION을 판정한다.
---

# Codex Eval Gate

스펙, 계획, 구현의 다음 단계 진입 여부를 판정한다. Codex에서 외부 `codex exec`를 다시 호출하지 않는다. 기본 평가는 `codex-review`로 수행하고, 사용자가 원하거나 `claude` CLI가 있으면 `codex-claude-eval`을 추가한다.

## Modes

```text
/codex-eval-gate spec docs/specs/project/spec.md
/codex-eval-gate plan docs/specs/project/implementation-plan.md
/codex-eval-gate implementation docs/specs/project/spec.md src/
```

| mode | 목적 | 승인 후 다음 단계 |
|------|------|------------------|
| spec | 스펙이 구현 착수 가능한지 검증 | `/codex-spec-dev docs/specs/<project>/spec.md` |
| plan | 구현 계획과 AC 추적성이 충분한지 검증 | 구현 진행 |
| implementation | 구현이 스펙과 AC를 만족하는지 검증 | 완료 |

## Workflow

### 1. 셀프 게이트

독립 평가 전에 기계적 검사를 직접 수행한다.

Spec:
- `spec.md` 존재
- `ambiguity-ledger.md` 존재
- ledger의 `blocking` 0개
- `assumed` 2개 이하, `open` 3개 이하
- AC 테이블 존재
- 모든 AC에 검증 방법 존재

Plan:
- `implementation-plan.md` 존재
- `spec.md` 존재
- `traceability.md`가 있으면 모든 AC 매핑

Implementation:
- `spec.md` 존재
- 변경 파일 또는 변경 범위 존재
- 관련 테스트 또는 대체 검증 방법 존재
- 가능한 테스트를 실행하고 결과 기록

셀프 게이트가 실패하면 독립 평가를 호출하지 않는다. 실패 이유와 수정해야 할 파일을 말하고 `NEEDS_REVISION` 결과 파일을 저장한다.

### 2. 평가 방식 결정

기본값:
- `codex-review` 1회
- 사용자가 교차검증을 원하거나 `claude` CLI 사용을 요청하면 `codex-claude-eval` 추가

현재 환경에서 subagent 사용이 명시적으로 허용되지 않는다면 사용자에게 짧게 허가를 요청한다. 허용되지 않거나 도구가 없으면 같은 컨텍스트 리뷰를 수행하되 결과에 `confidence: low`를 표시한다.

### 3. 결과 파일 위치

```text
docs/specs/<project>/eval-results/
├── <mode>-codex-review-<timestamp>.md
├── <mode>-claude-<timestamp>.md
└── <mode>-gate-<timestamp>.result.md
```

`<project>`는 target file이 속한 `docs/specs/<project>`에서 추론한다. 추론할 수 없으면 `.myagents/eval-results/`를 사용한다.

### 4. Codex Review 실행

`codex-review` 스킬을 사용해 평가 요청 파일을 만들고, 가능한 경우 subagent에게 평가를 맡긴다.

평가자는 다음을 해야 한다.
- 문서 주장만 보지 말고 코드베이스와 대조한다.
- FAIL 전에는 관련 파일을 다시 확인한다.
- 근거 없는 취향 제안은 하지 않는다.
- 결과를 `APPROVED` 또는 `NEEDS_REVISION`으로 판정한다.

### 5. Claude Eval 실행(선택)

`claude` CLI가 있고 사용자가 원하면 `codex-claude-eval`을 실행한다. 실패하면 게이트 전체를 실패시키지 말고, Claude 평가 실패 사유를 결과 파일에 기록하고 Codex review만으로 판정할지 사용자에게 명시한다.

### 6. 종합 판정

- 모든 실행 평가가 APPROVED: `APPROVED`
- 하나라도 구조적/의미적 FAIL이 타당함: `NEEDS_REVISION`
- 평가 간 의견이 갈림: 근거를 재확인하고, 타당한 FAIL이 있으면 `NEEDS_REVISION`; 불확실하면 사용자 결정 필요로 표시

결과 파일 형식:

```markdown
# Eval-Gate Result: <mode>

## 판정: APPROVED | NEEDS_REVISION
- 평가일시: YYYY-MM-DD HH:MM
- confidence: high | medium | low
- self-gate: pass | fail

## 상세 결과 파일
- codex-review: ...
- claude-eval: ... 또는 not-run

## Accepted Findings
1. ...

## Rejected Findings
1. ...

## Needs Follow-up
1. ...

## Next Step
...
```

### 7. 사용자 보고

사용자가 파일을 열지 않아도 판단할 수 있게 보고한다.

- 최종 판정
- accepted finding과 수정 방향
- rejected finding이 있으면 짧은 사유
- 결과 파일 경로
- 다음 단계

Next step:
- spec APPROVED: `/codex-spec-dev docs/specs/<project>/spec.md`
- plan APPROVED: 구현 진행
- implementation APPROVED: 완료
- NEEDS_REVISION: `/codex-spec-designer` 또는 `/codex-spec-dev` 중 돌아갈 위치 명시
