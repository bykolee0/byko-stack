---
name: codex-spec-dev
description: Codex에 최적화된 스펙 기반 구현 스킬. spec.md, docs/specs 폴더, implementation-plan.md, "스펙 구현", "spec 기반 개발", "구현 시작", "이 기능 개발해줘" 요청에서 사용한다. 스펙 품질을 확인하고 AC 추적성을 유지하며 실제 코드를 수정, 테스트, 검증까지 수행한다. 긴 작업에서는 Codex goal/plan을 활용하고, ralph-loop 대신 goal-loop 산출물과 진행 보고를 사용한다.
---

# Codex Spec Dev

스펙을 실제 동작하는 코드로 끝까지 구현한다. Codex에서는 "계획 제안 후 멈춤"이 실패로 보이기 쉬우므로, 사용자가 구현을 요청했다면 blocking 결정이 없는 한 구현과 검증까지 진행한다.

## Codex 진행 원칙

- 매 응답에 현재 단계, 완료/미완료 상태, 다음 행동을 밝힌다.
- 파일을 수정하기 전에 어떤 범위의 수정을 할지 짧게 알린다.
- 스펙의 모든 AC를 traceability로 추적한다. AC 누락 상태로 완료하지 않는다.
- 테스트를 실행할 수 없으면 이유와 대체 검증을 기록한다.
- 긴 구현에서 사용자가 `/goal` 또는 목표 추적을 명시했거나 이미 active goal이 있으면 goal 상태를 활용한다. 없으면 일반 plan/checklist로 진행한다.
- 사용자 요청이 "구현 시작"이면 계획만 만들고 멈추지 않는다. blocking 조건이 없으면 코드 수정과 검증까지 진행한다.

## Workflow

### 1. 스펙 수집과 품질 게이트

사용자가 경로를 주면 그 파일을 읽는다. 경로가 없으면 `docs/specs/` 아래 최신 또는 관련 스펙을 찾고, 후보가 여러 개면 짧게 확인한다.

읽을 파일:
- `spec.md`
- `ambiguity-ledger.md`
- `codebase-analysis.md`
- `traceability.md`, `implementation-plan.md`가 있으면 함께 읽기
- `sub-specs/`가 있으면 관련 항목 읽기

구현을 막는 조건:
- ledger에 `blocking`이 있음
- AC에 검증 방법이 없음
- 스펙 요구사항이 현재 코드와 명백히 충돌함
- `[TBD]`가 구현 방향, 데이터 모델, 공개 API, 권한/보안, 마이그레이션, AC 의미를 바꿀 수 있음

`[TBD]` 처리:
- 구현 방향에 영향을 주는 `[TBD]`는 blocking으로 보고 구현하지 않는다.
- 문구, 로그 메시지, 내부 네이밍처럼 구현 방향을 바꾸지 않는 `[TBD]`는 합리적 기본값으로 진행하되 `progress.md` 또는 최종 보고에 `assumed`로 기록한다.
- 판단이 애매하면 멈추고 사용자에게 결정 요청한다.

막는 조건이 없으면 구현 목표와 AC 요약을 사용자에게 짧게 알리고 계속 진행한다.

### 2. 구현 분석

스펙이 가리키는 코드 주변을 다시 확인한다. 기존 `codebase-analysis.md`를 신뢰하되, 구현 직전 최신 코드와 대조한다.

확인할 것:
- 기존 구조와 네이밍
- 에러 처리와 로깅 방식
- 테스트 프레임워크와 fixture 방식
- 변경 영향 범위
- 스펙이 언급한 API/함수/필드가 실제로 존재하는지

### 3. Traceability와 Plan

작업이 단순하면 메모리/응답의 checklist로 충분하다. 여러 단계가 있거나 AC가 3개 이상이면 파일을 만든다.

```text
docs/specs/<project>/
├── traceability.md
├── implementation-plan.md
├── progress.md
└── goal-loop-prompt.md   # 긴 구현이거나 재개 가능성이 있으면 생성
```

Traceability 필수 컬럼:

| AC ID | AC 내용 | 구현 Step | 대상 파일 | 테스트 | 상태 |
|-------|---------|-----------|-----------|--------|------|

모든 AC가 매핑되어야 한다. 매핑되지 않은 AC가 있으면 구현 전 스펙/계획을 보완한다.

### 4. 구현

스펙의 구현 순서와 코드베이스 패턴을 따른다.

- 작은 변경: 직접 구현하고 관련 테스트 실행
- 중간 변경: plan/checklist를 갱신하며 단계별 구현
- 큰 변경: `references/goal-loop-template.md`를 참고해 `progress.md`와 `goal-loop-prompt.md`를 만들고, Codex goal 또는 plan 업데이트와 함께 진행

Subagent 위임 기준:
- 사용자가 subagent/병렬 작업을 명시했거나 현재 세션 정책상 subagent 사용이 허용된 경우에만 사용한다.
- 위임 단위는 서로 다른 파일/모듈 소유권을 가져야 한다.
- worker에게 "다른 작업자가 있을 수 있으니 사용자 변경을 되돌리지 말라"고 지시한다.
- 결과를 받은 뒤 변경 파일과 AC 충족 여부를 직접 검토하고 통합한다.
- 허용되지 않거나 파일 소유권을 분리하기 어렵다면 직접 수행한다.

### 5. 검증

완료 전 반드시 확인한다.

- AC별 구현 여부
- AC별 테스트 또는 수동 검증 결과
- 관련 테스트 통과 여부
- 기존 기능 회귀 가능성
- 스펙에 없는 기능을 추가하지 않았는지

자동 테스트가 없는 프로젝트에서는 수동 검증 또는 정적 검증으로 AC를 확인할 수 있다. 단, "테스트 없음"을 통과처럼 쓰지 말고, 어떤 명령/검토/시나리오로 대체했는지 AC별로 기록한다.

검증 결과를 `progress.md` 또는 최종 응답에 남긴다.

### 6. 완료 보고와 다음 단계

완료 시:

```markdown
구현을 완료했습니다.
- 변경 파일: ...
- AC 검증: AC-1 pass, AC-2 pass, ...
- 테스트: ...

다음 단계:
`/codex-eval-gate implementation docs/specs/<project>/spec.md <changed paths>`로 독립 검증을 진행할 수 있습니다.
```

완료하지 못했으면 "미완료"라고 말하고, 남은 AC와 막힌 결정을 구체적으로 적는다.

## Bounce Back

다음은 코드에서 해결하지 말고 스펙으로 되돌린다.

- AC가 둘 이상으로 해석됨
- 스펙 요구사항이 현재 아키텍처와 충돌함
- 데이터/권한/운영 정책 결정이 빠짐
- 테스트 가능 기준이 없음

보고 형식:

```markdown
스펙 보완이 필요합니다.
- 문제: ...
- 근거: 파일:라인 또는 스펙 문구
- 돌아갈 단계: `/codex-spec-designer docs/specs/<project>/spec.md`
```

## References

- `references/goal-loop-template.md`
