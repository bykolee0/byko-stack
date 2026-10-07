# 번들 역할로 작업 위임하기

역할 정의는 이 문서와 같은 플러그인의 `../agents/`에 있다. 사용자 native agent 등록이나 원본 Git checkout을 요구하지 않는다. 현재 읽은 스킬·이 문서의 실제 위치를 기준으로 경로를 해석하며, 작업 repo의 cwd나 예전 cache 경로를 플러그인 루트로 쓰지 않는다.

## 직접 수행과 위임

독립적인 조사 질문, 경계가 분리된 구현, 설명 자료 제작처럼 별도 컨텍스트의 이점이 있는 일은 아래 역할에 위임한다. 이 지침은 해당 위임을 명시적으로 요청한다. 작은 조회·수정은 같은 전문 스킬을 직접 적용해도 된다. 에이전트 수와 호출 순서를 고정하지 않으며, 단독 전문 스킬은 이 workflow를 다시 호출할 필요가 없다.

| 맡길 일 | TOML | 전문 스킬 |
|---|---|---|
| 근거 조사 | [byko-analyst](../agents/byko-analyst.toml) | [분석](../skills/byko-analyze/SKILL.md) |
| 범위가 정해진 구현 | [byko-implementer](../agents/byko-implementer.toml) | [구현](../skills/byko-implement/SKILL.md) |
| 독립 검토 | [byko-reviewer](../agents/byko-reviewer.toml) | [코드](../skills/byko-review-code/SKILL.md)·[문서](../skills/byko-review-document/SKILL.md)·[뷰어](../skills/byko-review-viewer/SKILL.md) 중 필요한 것 |
| 사람용 자료 제작 | [byko-viewer](../agents/byko-viewer.toml) | [뷰어 제작](../skills/byko-build-viewer/SKILL.md) |

## 생성에 설정 적용

TOML에서 `model`, `model_reasoning_effort`, `developer_instructions`를 읽는다. Python 3.11 이상을 사용할 수 있으면 [prepare_agent.py](../scripts/prepare_agent.py)를 실행해 설정과 현재 패키지의 전문 스킬 경로를 얻을 수 있다.

```sh
python3 "<설치된 플러그인 루트>/scripts/prepare_agent.py" byko-reviewer
```

출력의 `model`과 `reasoning_effort`는 생성 도구의 실제 설정 인자에, `message`는 역할 지침으로 전달한다. 메시지에 이번 목적·대상·허용 및 제외 범위·원본 근거 위치를 덧붙인다. 목적이 충분히 전달되면 고정 입력 양식이나 별도 요청서 파일을 만들 필요는 없다. helper가 없거나 Python이 맞지 않으면 TOML과 위 경로를 직접 읽어 같은 내용을 구성한다. 파일 누락·오류를 무시하고 기본 모델로 생성하지 않는다.

실행 도구가 제공하는 인자만 쓴다. `role`은 식별용 메타데이터이며 등록되지 않은 `agent_type`으로 넘기지 않는다. full-history fork가 모델·노력 수준 변경을 막는 도구라면 새 컨텍스트를 선택한다. 독립 reviewer에는 원래 요청과 대상·근거만 주고 작성자의 예상 판정·이전 리뷰·전체 구현 대화를 전달하지 않는다. 예를 들어 현재 도구가 `fork_turns`를 지원하면 독립 검토에는 `none`을 사용한다.

생성 요청과 도구가 반환하는 실행 설정을 확인한다. 도구가 실제 적용값을 노출하지 않으면 확인한 것은 요청 설정까지임을 구분한다. TOML 내용을 메시지에 적는 것만으로 모델·권한이 적용되었다고 보지 않는다. native 개발자 지침과 작업 메시지의 우선순위도 동일하다고 주장하지 않는다.

## 범위와 결과 통합

상세 맥락은 agent가 직접 찾을 수 있게 원본 위치로 전달한다. 코드만 조사하는 범위, write 소유권, 보존할 계약은 빠뜨리지 않는다. 독립 writer의 파일·공유 상태가 겹치면 순차 수행한다. 같은 질문을 여러 agent가 반복 조사하거나 여러 실행자가 같은 광역 검사를 돌리게 하지 않는다.

반환된 결과·변경 파일·검증 근거·남은 문제를 확인하고 현재 작업에 통합한다. 구현자의 자체 검증은 독립 리뷰를 대신하지 않는다. 독립 검토의 시작과 결과 통합은 [codex-review](../skills/codex-review/SKILL.md), 목적·방법이 바뀌는 판단은 설계 workflow가 맡는다. 유효한 발견 사항은 수정한 뒤 영향받은 부분을 재확인한다.

## 기능이 없거나 생성이 실패한 경우

현재 정책·도구·모델 지원을 먼저 확인한다. 기능 부재나 지속되는 같은 오류를 새 프로세스·외부 모델로 우회하지 않는다. 사용 가능한 전문 스킬로 현재 세션에서 가능한 작업을 수행하고, 위임·요청 설정·독립성 중 확보하지 못한 것을 결과에 명시한다. 독립 리뷰가 필요한 완료는 `미검증`으로 남긴다. 다른 모델을 조용히 선택하거나 생성 실패를 작업 완료로 보고하지 않는다.
