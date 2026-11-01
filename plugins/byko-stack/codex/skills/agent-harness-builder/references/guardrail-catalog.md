# Guardrail Catalog

Guardrail은 반복되는 실수를 실행 가능한 feedback으로 바꾼다. 처음에는 저렴한 check 몇 개만 두고, 실제 실패가 필요성을 증명할 때 확장한다.

## Universal Guardrails

| Guardrail | Prevents |
|---|---|
| docs structure check | entry docs 누락, 깨진 ADR index |
| required commands check | 문서화되지 않았거나 stale한 test/lint/build command |
| architecture boundary check | 금지된 layer crossing |
| forbidden dependency check | domain code가 framework/ORM/client library를 import함 |
| naming/layout check | 합의된 file/module convention에서 drift |
| time/date check | naive local time, timezone drift |
| generated reference freshness | stale DB/API/schema docs |
| fixture/contract check | external API shape drift |
| secret check | credentials 또는 local env 유출 |
| spec traceability check | test 없는 acceptance criteria |

## Selection Rules

다음 guardrail을 선호한다.

- local에서 저렴하게 실행 가능
- deterministic
- 실패 원인이 명확함
- 프로젝트의 기존 test/lint system으로 구현 가능
- 실제 project risk에 대응

피한다.

- broad rewrite
- 매 test run마다 비싼 check
- 프로젝트에서 아직 받아들이지 않은 tool dependency
- 개인 취향만 반영한 rule

## Failure Message Standard

각 실패 메시지는 다음을 말해야 한다.

1. 어떤 rule을 위반했는가
2. 어디에서 발생했는가
3. 왜 중요한가
4. 어떻게 고치는가

예:

```text
src/domain/user.py imports sqlalchemy.
Domain must stay persistence-free. Move ORM code to infrastructure/db/ and keep domain models plain.
```

## Feedback Loop

다음 loop를 사용한다.

```text
failure/review/confusion
  -> docs/spec/ADR에 capture
  -> one-off인지 repeated risk인지 classify
  -> repeated risk를 test/lint/script로 encode
  -> local validation과 CI에서 실행
  -> rule이 바뀌면 docs 갱신
```
