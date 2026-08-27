# Task design

## 좋은 task의 조건

각 task는 다음을 만족한다.

1. fresh worker가 goal 문서와 관련 코드만 읽고 한 context에서 완결할 수 있다.
2. 결과가 objective가 아니라 observable acceptance criteria로 판정된다.
3. focused verification이 있고, 필요한 regression 범위가 드러난다.
4. write scope와 dependency가 명확하다.
5. 다음 task가 이어받을 artifact 또는 결정이 있다.

task가 너무 작아 setup과 eval 비용이 work보다 크면 합친다. 한 worker가 여러 독립 subsystem이나 대규모 산출물을 함께 다뤄야 하면 나눈다. 숫자 규칙보다 context와 verification boundary를 우선한다.

## 분해 기준

- vertical slice와 검증 가능한 milestone을 우선한다.
- research가 implementation 방향을 바꿀 수 있으면 별도 task로 둔다.
- shared schema, migration, generated file, global config는 병렬 write 경계로 쓰지 않는다.
- 최종 합성이나 end-to-end 검증은 별도 task 또는 final audit에서 명시한다.
- score-driven optimization은 "개선" 같은 무한 task로 두지 않고 baseline, metric, target, stop rule을 정의한다.

## acceptance criteria

각 조건은 "완료됐다"가 아니라 무엇을 관찰할지 적는다.

```markdown
- [ ] invalid signature 요청이 401이고 기존 valid request는 성공한다
  — 검증: `pytest tests/webhook -q`와 관련 handler diff 대조
```

좋은 검증은 필요에 따라 결합한다.

- deterministic: test, build, lint, schema check, metric
- artifact inspection: 실제 문서, UI render, image, generated output
- evidence comparison: primary source, existing contract, baseline
- independent rubric: 주관 품질이 중요한 경우 fresh evaluator

worker가 criteria를 처음 정의하게 하지 않는다. worker는 누락된 negative case나 더 엄격한 check를 추가할 수 있지만 기존 coverage를 낮출 수 없다.

## dependency와 병렬성

task마다 `depends_on`과 `Expected write scope`를 쓴다. 다음 중 하나면 병렬 writer로 표시하지 않는다.

- 같은 file 또는 directory를 수정한다.
- 하나가 다른 하나의 API/schema/output을 결정한다.
- lockfile, migration, generated index, global config를 함께 건드린다.
- 둘의 acceptance가 같은 integration behavior에 의존한다.

read-only 조사와 독립 test execution은 write scope가 겹치지 않아도 병렬화할 수 있다.

## dynamic plan 변경

진행 중 새 사실이 나오면 plan을 개선한다.

- **add**: 기존 DoD에 필요한 누락 work를 새 monotonic ID로 추가
- **split**: 원 task를 `superseded`로 만들고 replacement IDs 기록
- **refine**: pending task의 의미를 좁히지 않는 범위에서 조건 명료화
- **reorder**: dependency를 만족하는 pending task만 이동
- **supersede**: 이미 충족되거나 중복인 pending task를 근거와 함께 보존 종료

goal contract, acceptance coverage, authorization을 바꾸는 변경은 plan 개선이 아니라 contract change다. 사용자 승인 없이 적용하지 않는다.

## domain별 검증 예

- software: behavior test, caller/callee impact, build/lint, failure path
- writing: outline coverage, factual source check, tone/readability rubric, cross-section consistency
- research: claim-source ledger, contradictory evidence, method limits, synthesis traceability
- operations: policy checklist, dry run, rollback, ownership and failure handling
- visual artifact: deterministic render plus direct visual inspection and rubric
