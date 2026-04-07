# 요청 파일 템플릿

## 포맷

```markdown
# Evaluation Request

## Meta
- id: eval-<YYYYMMDD>-<HHMMSS>
- created_at: <ISO8601>
- evaluator: claude
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

<details>
<summary>ambiguity-ledger.md (copied)</summary>

(문서 전체 내용)

</details>

## Evaluation Response
<!-- EVAL_RESPONSE_START -->
<!-- EVAL_RESPONSE_END -->

## Caller Notes
<!-- 호출한 스킬이 검증 결과를 기록하는 영역 -->
```

## Source Documents 복사 가이드

### 어떤 파일을 copy하는가

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
- 소스 코드는 copy하지 않고 경로만 기재 (평가자가 직접 읽음)

**custom 모드:**
- 유저가 지정한 파일을 copy

### 기존 문서가 주어진 경우

유저가 이미 작성된 문서(`.myagents/*.md` 등)를 전달한 경우:
1. 해당 문서를 새 요청 파일의 Source Documents에 copy한다
2. Meta와 Evaluation Criteria는 새로 작성한다
3. 원본 문서 경로를 Meta에 기록한다

이 방식으로 기존 문서를 재활용하면서도 평가 이력을 유지할 수 있다.
