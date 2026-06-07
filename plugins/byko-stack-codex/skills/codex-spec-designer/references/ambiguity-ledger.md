# Ambiguity Ledger 상세

## 13개 추적 항목

| # | 항목 | 설명 | 대표 질문 |
|---|------|------|----------|
| 1 | **goal** | 이 프로젝트가 달성하려는 핵심 목표 | "무엇을 만드는가?" |
| 2 | **scope / non-goals** | 포함 범위와 명시적으로 제외할 것 | "어디까지 이번에 하고, 뭘 안 하는가?" |
| 3 | **current-state facts** | 현재 시스템의 관련 상태 (코드, 인프라, 데이터) | "지금 어떻게 되어 있는가?" |
| 4 | **desired behavior** | 완성 후 기대하는 동작 | "완성되면 어떻게 동작해야 하는가?" |
| 5 | **data model** | 관련 데이터 구조, 스키마, 관계 | "어떤 데이터를 다루고, 구조는?" |
| 6 | **external interfaces** | 외부 API, 서비스, 시스템 연동 | "외부와 어떻게 통신하는가?" |
| 7 | **failure handling** | 에러, 예외, 장애 시 동작 | "실패하면 어떻게 되어야 하는가?" |
| 8 | **auth / permission** | 인증, 인가, 권한 모델 | "누가 이 기능을 쓸 수 있는가?" |
| 9 | **migration / backfill** | 기존 데이터 마이그레이션, 백필 필요 여부 | "기존 데이터는 어떻게 처리하는가?" |
| 10 | **observability / logging** | 로깅, 모니터링, 알림 | "무엇을 로깅하고 어떻게 모니터링하는가?" |
| 11 | **rollout / fallback** | 배포 전략, 롤백 방법 | "어떻게 배포하고, 문제 시 어떻게 되돌리는가?" |
| 12 | **acceptance criteria** | 성공/완료의 검증 가능한 기준 | "무엇이 되면 '완성'인가?" |
| 13 | **verification method** | AC를 어떻게 검증할 것인가 | "어떻게 확인할 것인가?" |

## 상태 정의

| 상태 | 의미 | 근거 요구 | 게이트 영향 |
|------|------|----------|-----------|
| `confirmed` | 유저가 직접 확인함 | 유저 발언 라운드 번호 | 통과 가능 |
| `from-code` | 코드에서 확인한 사실 | 파일:라인 필수 | 통과 가능 |
| `assumed` | AI가 조사 후 추천안을 채택, 유저 미확인 | 채택안 + 근거 + 검토한 대안 | **3개 이상이면 게이트 미통과** |
| `open` | 아직 논의되지 않았으나 구현 방향을 막지는 않음 | — | **4개 이상이면 게이트 미통과** |
| `blocking` | 해소 전 진행 불가 | — | **1개라도 있으면 게이트 미통과** |

## 상태 전환 규칙

- `open` → `confirmed`: 유저가 답변함
- `open` → `from-code`: 코드에서 사실 확인
- `open` → `blocking`: 구현에 필수적인데 정보 없음
- `open` → `assumed`: 질문 정책상 유저 결정 조건에 해당하지 않아 추천안을 채택하고 근거/대안을 기록
- `assumed` → `confirmed`: 유저가 확인함
- `assumed` → `blocking`: 유저가 부정하거나 재논의 필요
- `blocking` → `confirmed`: 유저가 답변함
- `blocking` → `open`: **유저만** 전환 가능 (AI가 임의로 blocking 해제 금지)

## 템플릿

```markdown
# Ambiguity Ledger

> 프로젝트: [project-name]
> 최종 업데이트: YYYY-MM-DD HH:MM (Phase N)

## 추적표

| # | 항목 | 상태 | 내용 요약 | 근거/출처 |
|---|------|------|----------|----------|
| 1 | goal | open | — | — |
| 2 | scope / non-goals | open | — | — |
| 3 | current-state facts | open | — | — |
| 4 | desired behavior | open | — | — |
| 5 | data model | open | — | — |
| 6 | external interfaces | open | — | — |
| 7 | failure handling | open | — | — |
| 8 | auth / permission | open | — | — |
| 9 | migration / backfill | open | — | — |
| 10 | observability / logging | open | — | — |
| 11 | rollout / fallback | open | — | — |
| 12 | acceptance criteria | open | — | — |
| 13 | verification method | open | — | — |

## 게이트 상태

- blocking: ? / 0
- assumed: ? / ≤ 2
- open: ? / ≤ 3
- **게이트**: ❌ 미통과

## 변경 이력

### Phase 1 (YYYY-MM-DD)
- goal: open → confirmed — "태스크 관리 CLI, CRUD 4개" (유저 Round 1)
- ...
```

## 항목별 적용 가이드

모든 프로젝트에 13개 항목 모두가 관련되지는 않는다. 프로젝트 성격에 따라:

- **신규 개발**: current-state facts, migration이 덜 중요할 수 있음 → 코드/요구사항 근거가 있으면 `from-code`/`from-docs: "해당 없음"`, 아니면 `assumed: "해당 없음"`으로 처리
- **기존 기능 수정**: current-state facts, migration이 매우 중요 → 철저히 분석
- **인프라/배포 변경**: rollout/fallback이 핵심
- **API 개발**: external interfaces, auth, failure handling이 핵심

"해당 없음"도 유효한 상태다. 코드/문서/요구사항으로 판단 가능하면 유저에게 묻지 않는다. 다만 유저 결정 조건(제품 정책, 보안, 마이그레이션, 공개 API 등)에 해당하면 선택지와 추천을 제시해 확인한다.
