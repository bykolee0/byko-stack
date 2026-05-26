---
name: codex-spec-designer
description: Codex에 최적화된 구현 스펙 작성 스킬. 사용자의 기능 개발, 변경 설계, 구현 명세, "스펙 작성", "설계 문서", "spec 만들어줘", "기능 설계", "구현 전에 정리" 요청에서 사용한다. 코드베이스를 먼저 분석하고, 모호성을 ledger로 추적하며, 완료 가능한 spec.md와 ambiguity-ledger.md를 작성한 뒤 eval-gate 또는 구현으로 이어지는 다음 단계를 명확히 안내한다. 기존 byko-stack의 spec-designer를 Codex 실행 방식에 맞게 대체할 때 사용한다.
---

# Codex Spec Designer

목표는 구현자가 추가 맥락 없이 작업을 시작할 수 있는 스펙을 완성하는 것이다. Codex에서는 사용자가 현재 상태를 놓치기 쉬우므로, 매 응답에 현재 단계, 완료 여부, 다음 행동을 분명히 적는다.

## Codex 진행 원칙

- 먼저 코드를 읽고, 코드로 확인 가능한 질문은 사용자에게 묻기 전에 직접 확인한다.
- 질문은 blocking 결정에만 사용한다. 코드 탐색으로 해소 가능한 내용은 직접 해소하고 근거를 남긴다.
- 산출물을 만들기 전에는 무엇을 만들고 있는지 짧게 알린다.
- 중간에 멈춰야 하면 "아직 완료 아님", "필요한 답변", "답변 후 재개 위치"를 명시한다.
- 스펙 완료 시에는 `docs/specs/<project>/spec.md`, `ambiguity-ledger.md`, 필요한 보조 문서 경로와 다음 단계 명령을 반드시 알려준다.

## Workflow

### 1. 요청 해석과 초기 코드 탐색

요청이 충분히 구체적이면 관련 파일을 `rg`, `rg --files`, `sed`, `git grep` 등으로 먼저 찾는다.

확인할 것:
- 기존 구현, 유사 패턴, 컨벤션
- 관련 테스트와 fixture
- 변경 지점의 호출자/피호출자
- 데이터 모델, API, 권한, 실패 처리, 관측성 단서

요청이 너무 넓어 탐색 범위를 정할 수 없으면, 범위를 좁히는 질문을 1-3개만 한다.

### 2. 모호성 분류

`references/question-routing.md`를 사용해 질문을 분류한다.

- Type A: 코드에서 확인 가능하면 직접 확인하고 근거만 제시한다.
- Type B: 제품/정책/우선순위처럼 사용자만 결정 가능하면 질문한다.
- Type C: 코드 사실은 직접 확인하고 판단 부분만 질문한다.
- Type D: 판단이 필요한데 정보가 없으면 추측하지 말고 질문한다.

스펙을 쓰기 전까지 13개 항목의 상태를 추적한다. 상세 기준은 `references/ambiguity-ledger.md`를 읽는다.

### 3. 심층 분석

요청 지점만 보지 말고 같은 개념이 쓰이는 곳까지 추적한다.

- 함수명뿐 아니라 필드명, 에러 코드, 도메인 용어로 검색한다.
- 엔티티의 일부 연산에서 패턴을 발견하면 나머지 CRUD/상태 전이도 확인한다.
- 테스트와 운영 영향까지 확인한다.
- 분석 범위가 넓고 현재 환경에서 subagent 사용이 허용되면 독립 영역별로 위임한다. 허용되지 않으면 직접 분석하고 범위 제한을 기록한다.

분석 결과는 `docs/specs/<project>/codebase-analysis.md`에 저장하거나 스펙의 "현행 분석" 섹션에 충분히 남긴다.

### 4. Ledger와 Spec 작성

정보가 충분하면 다음 파일을 만든다.

```text
docs/specs/<project>/
├── spec.md
├── ambiguity-ledger.md
└── codebase-analysis.md
```

Ledger 게이트:
- `blocking`: 0개
- `assumed`: 2개 이하
- `open`: 3개 이하
- 각 상태는 사용자 확인 또는 파일:라인 근거를 가진다.

`references/spec-templates.md`를 사용해 `spec.md`를 작성한다. 필수 포함:
- 목표와 비목표
- 현행 분석 요약과 근거 파일
- 요구사항과 도메인 규칙
- 구현 상세
- 실패/예외 처리
- Acceptance Criteria 테이블
- 테스트 전략
- 구현 순서
- 남은 결정 사항

AC는 반드시 검증 가능해야 한다. 각 AC에는 검증 방법을 붙인다.

### 5. 완료 보고

스펙이 완성되면 다음 형식으로 보고한다.

```markdown
스펙 초안을 완료했습니다.
- spec: docs/specs/<project>/spec.md
- ledger: docs/specs/<project>/ambiguity-ledger.md
- gate 상태: blocking 0, assumed N, open N

다음 단계:
1. `/codex-eval-gate spec docs/specs/<project>/spec.md`로 독립 검증
2. 검증을 건너뛰려면 `/codex-spec-dev docs/specs/<project>/spec.md`로 구현 시작
```

완료 전이면 완료라고 말하지 않는다. 사용자 답변이 필요한 경우 다음 질문과 재개 지점을 남긴다.

## References

- `references/ambiguity-ledger.md`
- `references/question-routing.md`
- `references/spec-templates.md`
