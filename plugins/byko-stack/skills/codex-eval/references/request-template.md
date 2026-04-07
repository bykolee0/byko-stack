# 요청 파일 템플릿

## 포맷

```markdown
# Evaluation Request

## Meta
- id: eval-<YYYYMMDD>-<HHMMSS>
- created_at: <ISO8601>
- evaluator: codex
- mode: spec | plan | implementation | custom

## Context
- project: <project name>
- stack: <language/framework/runtime>
- architecture: <key modules or layers>
- constraints: <relevant constraints>

## Target Files
평가자는 이 파일들을 읽고 판단한다.
- <path 1>
- <path 2>

## Evaluation Criteria
<!-- 모드별 체크리스트가 여기에 삽입된다 -->

## Source Documents
<!-- 대상 문서의 내용이 여기에 copy된다 -->

<details>
<summary>spec.md (copied)</summary>

(문서 전체 내용)

</details>

## Evaluation Response
<!-- EVAL_RESPONSE_START -->
<!-- EVAL_RESPONSE_END -->

## Caller Notes
<!-- 호출한 스킬이 검증 결과를 기록하는 영역 -->
```

## codex 전용 주의사항

codex는 sandbox 환경에서 실행되므로 파일 접근이 제한될 수 있다.
따라서 **가능한 한 모든 관련 문서를 Source Documents에 copy**하는 것을 우선한다.

- spec, plan 모드: 관련 문서 전체를 copy
- implementation 모드: spec은 copy, 소스 코드는 경로 기재 (codex가 workspace-write sandbox에서 읽을 수 있음)

## 교차검증 시 (기존 claude-eval 파일에 추가)

기존 claude-eval 파일이 주어진 경우, 기존 Response 아래에 codex 전용 섹션을 추가한다:

```markdown
## Codex Evaluation Response
<!-- CODEX_EVAL_RESPONSE_START -->
<!-- CODEX_EVAL_RESPONSE_END -->
```

## Source Documents 복사 가이드

**spec 모드:**
- spec.md (필수)
- ambiguity-ledger.md (있으면 필수)
- 같은 디렉토리의 관련 문서

**plan 모드:**
- implementation-plan.md (필수)
- spec.md (필수 — 계획이 스펙에 부합하는지 판단 기준)
- traceability.md (있으면)

**implementation 모드:**
- spec.md (필수 — 구현의 판단 기준)
- traceability.md (있으면)
- 소스 코드는 경로만 기재

**custom 모드:**
- 유저가 지정한 파일을 copy
