---
name: codex-eval-gate
description: Codex에 최적화된 스펙, 구현 계획, 구현 결과 품질 게이트. "/codex-eval-gate spec docs/specs/project/spec.md", "/codex-eval-gate plan docs/specs/project/implementation-plan.md", "/codex-eval-gate implementation docs/specs/project/spec.md src/" 요청에서 사용한다. 외부 codex CLI 재호출 대신 Codex subagent 기반 codex-review와 선택적 claude-eval을 조합해 독립 검증하고 APPROVED 또는 NEEDS_REVISION을 판정한다. 평가 본문은 현재 세션에서 수행하지 않고 반드시 별도 컨텍스트에서 수행한다.
---

# Codex Eval Gate

스펙, 계획, 구현의 다음 단계 진입 여부를 판정한다. Codex에서 외부 `codex exec`를 다시 호출하지 않는다. 평가는 반드시 현재 세션과 분리된 컨텍스트에서 수행한다.

현재 세션에서 할 수 있는 것은 self-gate, 평가 요청 파일 작성, 독립 평가 결과의 근거 재확인, 결과 종합뿐이다. 실제 평가 본문을 현재 세션에서 수행하지 않는다. 현재 세션 리뷰는 환각, 관성적 통과, 작성자 편향을 막지 못하므로 eval-gate 결과로 인정하지 않는다.

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

평가 방식이 사용자의 요청에 명시되어 있지 않으면, 독립 평가를 시작하기 전에 짧게 묻는다.

```text
평가는 현재 세션이 아닌 별도 컨텍스트에서만 진행합니다. 어떤 방식으로 진행할까요?
1. Codex subagent review (권장)
2. Codex subagent review + Claude eval
3. Claude eval only
```

기본 권장값은 `Codex subagent review`다. 단, 현재 환경의 tool policy가 subagent 사용에 명시적 사용자 허가를 요구하면 이 질문이 그 허가 요청 역할을 한다.

허용되는 평가 방식:
- `Codex subagent review`: `codex-review`가 subagent에게 평가를 맡긴다.
- `Codex subagent review + Claude eval`: subagent 평가 후 `codex-claude-eval`로 교차검증한다.
- `Claude eval only`: `claude -p` 별도 프로세스로만 평가한다. Codex subagent를 사용할 수 없고 Claude CLI가 있을 때의 대안이다.

금지:
- 현재 세션에서 `codex-review` 평가 본문을 수행하지 않는다.
- subagent도 Claude도 사용할 수 없으면 게이트를 진행하지 않는다. 결과 파일이 필요하면 `BLOCKED` 또는 `NEEDS_REVISION`으로 저장하고 "독립 평가 미실행"을 명시한다.
- `confidence: low` 현재 세션 리뷰로 APPROVED를 내지 않는다.

### 3. 결과 파일 위치

```text
docs/specs/<project>/eval-results/
├── <mode>-codex-review-<timestamp>.md
├── <mode>-claude-<timestamp>.md
└── <mode>-gate-<timestamp>.result.md
```

`<project>`는 target file이 속한 `docs/specs/<project>`에서 추론한다. 추론할 수 없으면 `.myagents/eval-results/`를 사용한다.

### 4. Codex Review 실행

`codex-review` 스킬을 사용해 평가 요청 파일을 만들고 subagent에게 평가를 맡긴다. subagent를 사용할 수 없으면 이 단계를 실패로 처리하고 현재 세션 리뷰로 대체하지 않는다.

평가자는 다음을 해야 한다.
- 문서 주장만 보지 말고 코드베이스와 대조한다.
- FAIL 전에는 관련 파일을 다시 확인한다.
- 근거 없는 취향 제안은 하지 않는다.
- 결과를 `APPROVED` 또는 `NEEDS_REVISION`으로 판정한다.

### 5. Claude Eval 실행

사용자가 `Codex subagent review + Claude eval` 또는 `Claude eval only`를 선택하면 `codex-claude-eval`을 실행한다.

Claude eval 실패 처리:
- subagent review가 성공했고 Claude eval만 실패하면, 실패 사유를 결과 파일에 기록하고 subagent review만으로 판정할지 사용자에게 확인한다.
- `Claude eval only`에서 Claude eval이 실패하면 게이트를 진행하지 않는다.

### 6. 종합 판정

- 모든 실행 독립 평가가 APPROVED: `APPROVED`
- 하나라도 구조적/의미적 FAIL이 타당함: `NEEDS_REVISION`
- 평가 간 의견이 갈림: 근거를 재확인하고, 타당한 FAIL이 있으면 `NEEDS_REVISION`; 불확실하면 사용자 결정 필요로 표시
- 실행된 독립 평가가 0개이면 `APPROVED` 금지

결과 파일 형식:

```markdown
# Eval-Gate Result: <mode>

## 판정: APPROVED | NEEDS_REVISION | BLOCKED
- 평가일시: YYYY-MM-DD HH:MM
- confidence: high | medium
- self-gate: pass | fail
- evaluation_context: codex-subagent | claude-process | codex-subagent+claude-process | none

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
- 어떤 별도 컨텍스트로 평가했는지

Next step:
- spec APPROVED: `/codex-spec-dev docs/specs/<project>/spec.md`
- plan APPROVED: 구현 진행
- implementation APPROVED: 완료
- NEEDS_REVISION: `/codex-spec-designer` 또는 `/codex-spec-dev` 중 돌아갈 위치 명시
