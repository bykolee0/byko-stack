# Codex Goal-Loop 산출물 템플릿

## progress.md

긴 구현에서 Codex가 계속 읽고 업데이트하는 상태 추적 파일이다. 사용자가 `/goal`을 명시했거나 active goal이 있으면 이 파일과 goal 상태를 함께 갱신한다. goal 도구가 없거나 사용할 수 없으면 `progress.md`와 `update_plan`만 사용한다.

```markdown
# 구현 진행 현황

> 스펙: [spec.md](spec.md)
> 계획: [implementation-plan.md](implementation-plan.md)
> Traceability: [traceability.md](traceability.md)
> 마지막 업데이트: YYYY-MM-DD HH:MM

## 전체 상태: 진행중 (0/M AC 완료)

## AC 추적
| AC ID | 구현 | 테스트 | 검증 |
|-------|------|--------|------|
| AC-1 | pending | pending | pending |
| AC-2 | pending | pending | pending |

## 작업 로그
### YYYY-MM-DD HH:MM
- 작업 내용
- 결과

## 이슈 로그
<!-- iteration 중 발견된 문제, 결정 사항, bounce-back 필요 사항 -->
```

## goal-loop-prompt.md

긴 구현을 재개하거나 별도 Codex 세션에서 이어가기 위한 자기완결적 프롬프트이다.

```markdown
너는 Codex에서 스펙 기반 구현을 수행하는 개발자다.

## 참조 파일
- 스펙: docs/specs/[project-name]/spec.md
- 구현 계획: docs/specs/[project-name]/implementation-plan.md
- 진행 현황: docs/specs/[project-name]/progress.md
- Traceability: docs/specs/[project-name]/traceability.md

## 반복 절차

### 1. 상태 파악
- progress.md를 읽고 현재 상태를 파악한다
- traceability.md에서 미완료 AC를 확인한다
- 이전 이슈 로그를 확인한다

### 2. 구현
- 다음 미완료 AC를 선택한다
- 관련 코드를 읽고 기존 컨벤션을 확인한다
- 구현한다 (기존 패턴 준수, 사이드이펙트 주의)

### 3. 테스트
- 스펙 AC 기준으로 테스트를 작성한다
- 테스트를 실행하여 통과를 확인한다
- 자동 테스트가 없거나 실행할 수 없으면 AC별 수동/정적 검증 방법과 한계를 기록한다

### 4. 자기평가
- AC 준수: 이 코드가 해당 AC의 의도를 정확히 구현하는가?
- 드리프트: 스펙에 없는 기능을 추가하지 않았는가?
- 회귀: 이전 iteration에서 통과한 테스트가 여전히 통과하는가?

### 5. 방향 점검
- traceability matrix에서 AC 커버리지 확인
- 완료된 AC들의 테스트가 여전히 전부 통과하는가
- 초기 계획과 실제 구현 사이에 괴리가 없는가
- 괴리가 있다면 progress.md에 기록하고 남은 계획 조정

### 6. 기록
- progress.md 업데이트 (AC 추적표 + 작업 로그)
- traceability.md 업데이트 (상태 변경)
- 사용자 요청이 있거나 프로젝트 관례상 필요할 때만 git commit

### 7. 실패 분류 (문제 발생 시)
- 코드 문제 → 코드를 수정
- 스펙 문제 → progress.md에 BOUNCE_BACK 기록, 상세 사유 기록

## 구현 지침
- 기존 코드베이스의 컨벤션을 반드시 따른다
- 변경이 기존 기능에 영향을 주는지 호출 체인을 추적하여 확인한다
- 테스트는 코드가 아닌 스펙 AC 기준으로 작성한다
- 스펙에 없는 기능을 추가하지 않는다
- 구현 방향, 데이터 모델, 공개 API, 권한/보안, 마이그레이션, AC 의미를 바꾸는 [TBD]는 blocking으로 분류하고 멈춘다
- 구현 방향을 바꾸지 않는 [TBD]만 assumed로 기록하고 진행한다

## 완료 조건
모든 AC가 구현되고, 가능한 자동 테스트가 통과하거나 AC별 대체 검증이 기록되면:
1. traceability matrix에서 모든 칸이 채워졌는지 확인
2. 스펙의 AC를 하나씩 대조하여 누락이 없는지 최종 검증
3. 실패한 자동 테스트가 있으면 완료 처리하지 않는다
4. progress.md 전체 상태를 "완료"로 변경
5. 사용자에게 변경 파일, 테스트/대체 검증 결과, 다음 eval-gate 명령을 보고
```

## Codex 재개 안내 (유저에게 제시)

```
생성된 파일:
- docs/specs/[project-name]/implementation-plan.md — 상세 구현 계획
- docs/specs/[project-name]/traceability.md — AC → 구현 → 테스트 매핑
- docs/specs/[project-name]/progress.md — 진행 추적
- docs/specs/[project-name]/goal-loop-prompt.md — 긴 구현 또는 재개용 프롬프트

긴 구현을 goal로 관리하려면:
/goal start "Implement docs/specs/[project-name]/spec.md according to traceability.md"
```
