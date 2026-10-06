# 재사용하는 서브에이전트와 스킬

반복해서 맡기는 분석·구현·검토·사람용 자료 제작을 이 플러그인에서 관리한다. TOML은 역할과 모델 설정을, 스킬은 전문 작업 방법을 담는다. 스킬은 메인에서도 단독으로 사용할 수 있다. Stack의 설계·개발·리뷰 진입점은 [번들 역할 위임](../shared/delegation.md)을 사용하며 작업에 맞게 직접 수행과 위임을 선택한다.

## 구성

모든 역할의 기본 설정은 `model = "gpt-6.1-sol"`, `model_reasoning_effort = "high"`다. 기본 내장 역할을 덮어쓰지 않도록 `byko-` 이름을 사용한다.

| 역할 | 맡기는 일 | 참고하는 스킬 |
|---|---|---|
| [byko-analyst](byko-analyst.toml) | 필요한 근거를 조사하고 공유 가능한 분석으로 전달 | [byko-analyze](../skills/byko-analyze/SKILL.md) |
| [byko-implementer](byko-implementer.toml) | 맡은 동작 구현·보존 계약 확인·자체 검증 | [byko-implement](../skills/byko-implement/SKILL.md) |
| [byko-reviewer](byko-reviewer.toml) | 목적에 맞는 관점으로 검토하고 판정·근거 반환 | [코드](../skills/byko-review-code/SKILL.md), [문서](../skills/byko-review-document/SKILL.md), [뷰어](../skills/byko-review-viewer/SKILL.md) 중 필요한 지침 |
| [byko-viewer](byko-viewer.toml) | 배경 없는 독자에게 설명·시각화·탐색을 제공 | [byko-build-viewer](../skills/byko-build-viewer/SKILL.md), 기본 HTML |

검토 스킬은 에이전트를 생성하지 않는다. 직접 검토하거나 이미 생성된 검토자가 적용한다. 코드 리뷰는 `orchestrated-self-review`의 목적·실제 경계·독립 반증 원칙을 가져왔지만, 개인 전역 스킬 설치나 3명 구성·메인의 재검증 절차에 의존하지 않는다. 문서 리뷰는 논리·근거, 뷰어 리뷰는 독자의 이해·탐색을 판단한다. 복합 대상에는 필요한 지침을 조합한다.

공통 작업 기준은 [task-contract.md](../shared/task-contract.md), 검토 기준은 [review-principles.md](../shared/review-principles.md)에 있다. 기존 Stack의 manifest나 상태 관리 규칙을 필수로 불러오지 않는다.

## 호출과 범위

호출자는 원하는 결과와 알고 있는 대상·범위를 자연어로 전달하면 된다. 입력 schema나 특정 문서 세트를 채울 필요는 없다. 역할은 누락된 맥락을 가능한 범위에서 직접 확인하고, 결과를 바꾸는 미결정 사항만 질문한다.

- 분석가: “이 함수의 호출 경로만 조사해줘. DB·로그 조회는 제외해.”
- 구현자: “동일한 입력의 재시도는 기존 결과를 반환하게 해줘. 공개 인터페이스는 유지해.”
- 검토자: “이 설계로 원래 문제를 해결할 수 있는지 검토해줘. 구현은 아직 없어.”
- 뷰어 생성자: “이 비교 결과를 처음 보는 팀원이 판단할 수 있도록 보여줘.”

역할이 가진 능력 전체를 매번 수행하지 않는다. 명시된 제한을 지키며 범위 밖 확인이 필요하면 이유와 현재 결과를 반환한다. 분석·리뷰의 보고서 저장 위치가 없으면 응답으로 전달한다. 이미 완료된 자체 검증을 독립 검토라고 표시하지 않는다.

## 플러그인 파일을 읽어 동적으로 생성하기

이 디렉터리에 TOML이 포함됐다는 사실만으로 Codex custom agent가 자동 등록됐다고 가정하지 않는다. 역할 선택 인자가 없는 도구에서도 호출자는 TOML을 읽어 다음 값을 사용할 수 있다.

Python 3.11 이상에서는 `python3 "<플러그인 루트>/scripts/prepare_agent.py" byko-reviewer`로 현재 패키지의 설정과 스킬 경로를 JSON으로 받을 수 있다. 이 helper는 agent를 실행하거나 사용자 설정을 수정하지 않는다. 반환된 `message`에 이번 목적과 범위를 덧붙여 생성 도구에 전달한다. Python이 없으면 TOML과 [위임 지침](../shared/delegation.md)을 직접 읽는다.

| TOML | 동적 생성에 적용할 내용 |
|---|---|
| `name`, `description` | 역할 선택과 설명 |
| `model` | 도구가 지원하는 모델 인자 |
| `model_reasoning_effort` | 도구가 지원하는 노력 수준 인자(예: `reasoning_effort`) |
| `developer_instructions` | 역할 지침. 별도 지침 인자가 없으면 작업 메시지에 포함 |

실행 도구가 허용하는 인터페이스를 사용한다. TOML의 키를 통째로 생성 도구에 넘기거나, 모델·노력 수준을 메시지에 쓰는 것만으로 설정됐다고 간주하지 않는다. 현재 도구에 full-history fork와 모델 변경의 동시 사용 제한이 있으면 필요한 작업 정보만 전달하는 새 컨텍스트를 선택한다. 설정을 적용할 수 없으면 실제 사용할 설정과 제한을 알리고, 다른 모델로 조용히 대체하지 않는다.

지침을 작업 메시지로 전달하는 방식은 native `developer_instructions` 적용과 우선순위가 같지 않다. 어느 방식도 부모의 권한·실행 정책을 확대하지 않는다. TOML에는 sandbox 변경을 넣지 않았으며, 제품 read-only 등의 역할 지침은 운영 규칙이지 도구 수준 접근 제어를 대신하지 않는다.

스킬 목록에 이 패키지가 있으면 이름으로 찾는다. 목록에 없다면 호출자가 사용할 스킬의 실제 `SKILL.md` 경로를 전달할 수 있다. 그 경로는 설치된 플러그인 또는 소스 checkout에서 확인하며 캐시 버전·개인 절대경로를 TOML에 고정하지 않는다. 스킬이 없어도 역할은 기본 지침으로 가능한 작업을 수행하고 전문 검증의 공백을 반환한다.

## 사용자 Codex에 직접 등록하기

역할 등록을 지원하는 로컬 Codex에서는 필요한 TOML을 프로젝트의 `.codex/agents/` 또는 개인의 `~/.codex/agents/`에 복사해 사용할 수 있다. 이 패키지의 `byko-*` 스킬도 함께 이용할 수 있게 플러그인을 설치하거나 해당 스킬 경로를 제공한다. **TOML만 복사하면 스킬까지 설치되는 것은 아니다.**

예를 들어 이 플러그인 루트에서 다음 명령은 개인용 역할 파일을 복사한다. 이미 같은 파일이 있으면 덮어쓸지 확인한다.

```sh
mkdir -p ~/.codex/agents
cp -i agents/byko-*.toml ~/.codex/agents/
```

프로젝트용은 작업할 프로젝트의 `.codex/agents/`를 대상으로 한다. 등록 후 새 세션에서 역할이 발견되는지, 모델·노력 수준이 실제 적용됐는지 확인한다. native 역할 파일에 지정된 모델·노력 수준을 바꾸려면 해당 TOML을 수정한다. 이 저장소의 업데이트가 이미 복사한 사용자 파일에 자동 반영되지는 않는다.

공식 참고: [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents), [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol). 호스트별 등록·생성 지원은 실제 실행 환경에서 확인한다.

## 검증 범위

TOML·스킬 형식과 상대 참조 검사는 실행 품질을 보장하지 않는다. 대표 작업에서 범위 준수·기존 계약 보존·판정 근거·뷰어의 실제 이해와 탐색을 확인해야 한다. native 자동 등록, 동적 설정 적용, 자체 검증, 독립 리뷰, 실제 사용자 평가는 각각 구분해서 기록한다.
