# /root/candidate_code

## 2026-10-19T07:09:11.420Z

**candidate_a는 수정 필요, candidate_b는 통과입니다.** 계약에 따라 반환값·예외와 `stock` 전체 상태를 함께 확인했습니다.

| 사전 검토 기준 | candidate_a | candidate_b |
|---|---|---|
| V1 정상 차감·다른 SKU 보존 | 통과 | 통과 |
| V2 재고 전량 차감 → 0 | 통과 | 통과 |
| V3 재고 부족 → ValueError·전체 상태 불변 | **실패** | 통과 |
| V4 0·음수·bool·문자열 거부·상태 불변 | 통과 | 통과 |
| V5 없는 SKU → KeyError·상태 불변 | 통과 | 통과 |

**candidate_a의 재고 부족 처리가 계약을 위반합니다.** [candidate_a.py:4](/private/tmp/byko-purpose-review-20261019.kuA3QA/fixtures/code/candidate_a.py:4)의 `max(0, …)`가 부족한 재고를 0으로 보정하고, 다음 줄에서 저장합니다.

- 재현: `stock={'A':5,'B':9}`에서 A를 6개 차감.
- 기대: `ValueError`, 전체 상태 `{'A':5,'B':9}` 유지.
- 실제: `0` 반환, 상태가 `{'A':0,'B':9}`로 변경됨.
- 영향: 실패해야 할 차감이 성공처럼 반환되고 기존 재고까지 사라집니다. 재고가 이미 0인 경우에도 예외 없이 0을 반환했습니다.

저장 전에 재고 부족을 검사하고 `ValueError`를 발생시켜야 합니다. 수정 후 V3와 재고 0인 사례에서 예외와 전체 상태 불변을 재확인하면 됩니다.

**candidate_b는 제공된 단일 스레드 계약을 충족합니다.** [candidate_b.py:4](/private/tmp/byko-purpose-review-20261019.kuA3QA/fixtures/code/candidate_b.py:4)에서 재고를 조회하고, 부족하면 쓰기 전에 예외를 발생시킵니다. 사전 기준 외에 B 차감 시 A 보존, 재고 0에서 차감, 실수·`None` 거부도 실행해 확인했습니다. 이 추가 사례는 구현 후 반증 검사입니다. 계약에서 제외한 영속 저장·재시도·동시성은 판정 범위에 포함하지 않았습니다.

실행 부록: 지정 역할 지침, `byko-review-code/SKILL.md`, 연결된 공통 지침 3개와 fixture의 `REQUEST.md`, `CONTRACT.md`, `review-baseline.md`, 두 후보를 읽었습니다. Python에서 후보를 메모리로 로드해 각각 13개 사례의 결과와 전체 상태를 확인했습니다. 검토 버전의 SHA-256 접두사는 A `99ba7d884138`, B `a8de3153dee9`입니다. 파일 변경·생성, 추가 reviewer 생성, 외부 접근은 없었습니다.
