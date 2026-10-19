# /root/baseline_code

## 2026-10-19T07:03:17.900Z

**candidate_a는 수정 필요, candidate_b는 이번 계약 범위에서 통과입니다.**

| 구현 | 판정 | 실행 결과 |
|---|---|---|
| candidate_a | 수정 필요 | 13개 사례 중 2개 실패: 재고 부족, 재고 0에서 차감 |
| candidate_b | 통과 | 동일한 13개 사례 모두 통과 |

candidate_a는 **재고가 부족할 때 예외 없이 재고를 변경합니다.** [candidate_a.py:4](/private/tmp/byko-purpose-review-20261019.kuA3QA/fixtures/code/candidate_a.py:4)의 `max(0, stock[sku] - quantity)`가 부족분을 0으로 보정하고, 다음 줄에서 저장하기 때문입니다.

`stock={'a':10,'b':20}`에서 `deduct(stock,'a',11)`은 `ValueError`와 전체 상태 보존이 기대됩니다. 실제로는 `0`을 반환하고 `stock={'a':0,'b':20}`으로 바뀌었습니다. 재고가 이미 0인 경우에도 예외가 발생하지 않습니다. 호출자는 실패해야 할 차감을 성공으로 받아들이게 됩니다. **쓰기 전에 재고 부족을 검사하여 `ValueError`를 발생시키는 수정이 필요합니다.**

candidate_b는 [candidate_b.py:5](/private/tmp/byko-purpose-review-20261019.kuA3QA/fixtures/code/candidate_b.py:5)에서 부족 여부를 검사한 뒤 차감합니다. 정상 차감·정확히 소진·부족 재고·0 재고, 잘못된 quantity(`0`, 음수, bool 두 값, float, 문자열, `None`), 없는 SKU, 여러 SKU의 연속 차감을 실행했습니다. 각 호출에서 반환값 또는 예외뿐 아니라 **stock 전체 상태**도 확인했습니다. 제공된 검토 가안 V1–V5의 기대 동작과도 일치합니다.

판정은 제공된 두 파일의 단일 스레드·메모리 내 동작에 한정합니다. 대상 SHA-256 접두사는 A `99ba7d884138`, B `a8de3153dee9`입니다.

실행 부록: `byko-reviewer.toml`, `byko-review-code/SKILL.md`, 연결된 `review-principles.md`·`task-contract.md`, fixture의 `REQUEST.md`·`CONTRACT.md`·`review-baseline.md`와 두 구현을 읽었습니다. `python3 -B`로 후보별 13개 사례를 메모리에서 실행했습니다. 파일 변경·추가 reviewer 생성·외부 접근은 없었습니다.
