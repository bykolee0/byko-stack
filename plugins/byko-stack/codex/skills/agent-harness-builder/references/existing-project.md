# Existing Project Workflow

brownfield project에 사용한다. 넓은 질문을 하기 전에 repo를 먼저 읽는다.

## Shallow Scan

수집할 항목:

- root files: `AGENTS.md`, `README*`, architecture docs, package manifests, lockfiles
- source layout과 tests
- lint/format/build/test/typecheck commands
- CI config
- docs structure
- deployment와 infra hint

먼저 `rg --files`를 사용한다. 이후 entry point, architecture, commands, current decisions를 설명하는 문서만 골라 읽는다.

## Analyze

짧은 working model을 만든다.

- project purpose
- stack과 package manager
- agent/human용 기존 entry point
- 알려진 commands
- architecture boundaries
- 기존 docs와 누락된 index
- 강한 convention, 약한 convention, 충돌하는 convention
- 이미 문서화된 open decisions

분석 중에는 refactor하지 않는다.

## Ask Only Targeted Questions

다음 경우에만 질문한다.

- docs와 code가 서로 다름
- correctness command가 없음
- convention이 일관되지 않고 하나를 고르면 향후 작업 방향이 바뀜
- security, data retention, deployment, auth, public API, migration policy가 불명확함

파일에서 확인 가능한 내용을 다시 묻지 않는다.

## Brownfield Harness Output

incremental change를 선호한다.

1. `AGENTS.md`를 map으로 갱신하거나 생성한다.
2. docs에 index가 없으면 `docs/README.md`를 추가한다.
3. 반복 참조되는 외부 자료가 있으면 `docs/references/index.md`와 local summary를 추가한다.
4. `docs/design-docs/index.md`와 foundation ADR을 추가한다.
5. 기존 test/lint 도구를 사용해 lightweight guardrail을 추가한다.

프로젝트에 이미 동등한 파일이 있으면 정확한 이름을 강제하지 말고 local convention에 맞춘다.
