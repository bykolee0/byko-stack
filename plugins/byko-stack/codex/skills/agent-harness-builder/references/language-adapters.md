# Language Adapters

아래 내용은 implementation option이지 고정 rule이 아니다. 기존 project tool이 우선이다.

## Python

선호:

- 초기 harness는 pytest architecture tests
- 이미 사용 중이면 ruff로 lint/format
- import graph rule이 커지면 import-linter

좋은 첫 check:

- layer별 forbidden imports
- naive `datetime.now()`
- docs/ADR structure
- external API용 fixture contract tests

## Node / TypeScript

기존 npm scripts를 우선한다.

- eslint로 import boundaries와 style
- vitest/jest로 guardrail tests
- docs/index check용 custom Node scripts
- 이미 사용 중이면 TypeScript project references 또는 path rules

좋은 첫 check:

- domain/server module에서 UI import 금지
- repository/data layer 밖에서 direct DB client 사용 금지
- generated API types freshness
- docs links와 ADR status

## Go

선호:

- `go test ./...`
- package boundary check용 작은 `_test.go` 파일
- 이미 설정되어 있으면 `go vet` 또는 lint tool
- package tests가 어색할 때만 scripts

좋은 첫 check:

- package import direction
- domain package에서 infra client 금지
- generated schema freshness

## Rust

선호:

- `cargo test`
- workspace-level tests
- 이미 사용 중이면 clippy
- 존재하면 `xtask`

좋은 첫 check:

- crate dependency boundaries
- generated schema/protobuf freshness
- feature flag policy

## Polyglot / Monorepo

repo-level command를 선호한다.

```text
scripts/check-harness
```

또는 기존 task runner를 사용한다. check는 작고 조합 가능하게 유지한다.

- docs structure
- package ownership
- cross-service API contract references
- package별 required commands
- generated docs freshness

하나의 language test framework를 전체 repo에 강제하지 않는다.
