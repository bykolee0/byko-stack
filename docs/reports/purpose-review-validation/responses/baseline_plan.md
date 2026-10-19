# /root/baseline_plan

## 2026-10-19T07:03:05.064Z

**plan-a는 수정 필요, plan-b는 계획 검토 통과입니다.** plan-b는 구현에 넘길 수 있습니다. 이 판정은 문서와 현재 코드의 대조 결과이며, 구현 완료나 실행 검증 통과를 뜻하지 않습니다.

| 대상 | 판정 | 핵심 이유 |
|---|---|---|
| plan-a | 수정 필요 | 접수 식별 기준과 내용 충돌 처리가 계약에 어긋납니다. |
| plan-b | 통과 | 고객/request_id 기준 판별, 동일 bytes 재사용, 충돌 시 보존과 오류, 검증 방법이 계약에 맞습니다. |

plan-a에서 고쳐야 할 사항은 다음과 같습니다.

1. **파일명을 식별자로 쓰면 서로 다른 요청을 합칩니다.** [plan-a.md:2](/private/tmp/byko-purpose-review-20261019.kuA3QA/fixtures/plan/plan-a.md:2)는 고객별 소문자 파일명으로 기존 접수를 찾습니다. 하지만 계약의 식별자는 고객/request_id입니다. 같은 고객이 서로 다른 request_id로 같은 이름·내용을 보내면 각각 신규 접수여야 하는데 기존 ID를 반환하게 됩니다. 반대로 같은 request_id·내용을 다른 파일명으로 재전송하면 새 접수를 만들 수 있습니다. 고객/request_id 조합으로 판별하도록 바꿔야 합니다.

2. **내용 교체는 기존 내용 보존 계약을 위반합니다.** 같은 줄의 “내용이 다르면 기존 내용을 교체”는 동일 request_id의 내용 충돌에서 오류를 반환하고 기존 내용을 보존해야 한다는 [CONTRACT.md:1](/private/tmp/byko-purpose-review-20261019.kuA3QA/fixtures/plan/CONTRACT.md:1)과 충돌합니다. 내용이 다르면 저장 상태를 변경하지 않고 오류를 반환하도록 계획해야 합니다.

3. **저장 개수만 검사하면 위 두 문제를 놓칩니다.** 잘못된 요청 병합이나 기존 내용 교체가 일어나도 저장 개수는 하나일 수 있습니다. 반환 ID, 오류 발생 여부, 호출 전후 전체 records를 함께 확인하고, 서로 다른 요청의 독립성도 검증해야 합니다.

[plan-b.md:2](/private/tmp/byko-purpose-review-20261019.kuA3QA/fixtures/plan/plan-b.md:2)는 현재 `accept`가 매번 append한다는 [current.py:2](/private/tmp/byko-purpose-review-20261019.kuA3QA/fixtures/plan/current.py:2)의 동작을 정확히 짚고, 계약에 필요한 분기를 제시합니다. [계획된 검증:3](/private/tmp/byko-purpose-review-20261019.kuA3QA/fixtures/plan/plan-b.md:3)도 재전송, 내용 충돌, 동일 파일명의 별도 요청, 고객 간 독립성, 최초 접수 동작 보존을 실제 records와 반환/오류로 관찰합니다. 오류 메시지와 탐색 방법은 구현 중 정할 수 있으며, 명시된 순차 호출 범위에서 분산 락은 필요하지 않습니다.

실행 부록: 지정 reviewer 역할, `byko-review-document/SKILL.md`, 연결된 공통 기준·작업 범위와 fixture의 다섯 자료를 읽었습니다. 계약·현재 코드·두 계획을 정적으로 대조했으며 실행 테스트와 파일 변경은 하지 않았습니다. 검토본 SHA-256은 plan-a `3ff0d9caad6e09154fc3713f97ed5792ae479ebca86e36237fe365ad43643e78`, plan-b `9fb9a4b884ec568c53e97546c6a72eeb71eb4bcb8a795fe28de72a5ff70235fe`입니다.
