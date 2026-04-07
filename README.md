```
██████╗ ██╗   ██╗██╗  ██╗ ██████╗     ███████╗████████╗ █████╗  ██████╗██╗  ██╗
██╔══██╗╚██╗ ██╔╝██║ ██╔╝██╔═══██╗    ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
██████╔╝ ╚████╔╝ █████╔╝ ██║   ██║    ███████╗   ██║   ███████║██║     █████╔╝ 
██╔══██╗  ╚██╔╝  ██╔═██╗ ██║   ██║    ╚════██║   ██║   ██╔══██║██║     ██╔═██╗ 
██████╔╝   ██║   ██║  ██╗╚██████╔╝    ███████║   ██║   ██║  ██║╚██████╗██║  ██╗
╚═════╝    ╚═╝   ╚═╝  ╚═╝ ╚═════╝     ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚══════╝╚═╝  ╚═╝
 :: byko-plugins ::                                                (Claude Code)
```

> 별도의 프레임워크 없이, 오직 스킬만으로 동작하는 미니멀리즘 하네스.

> English version: [README.en.md](./README.en.md)

## 구조

```
byko-plugins/
├── .claude-plugin/
│   └── marketplace.json     # 마켓플레이스 메타데이터 및 플러그인 목록
├── plugins/
│   └── byko-stack/          # 개별 플러그인
│       └── skills/          # 플러그인에 포함된 스킬들
└── README.md
```

## 설치 방법

### 1. 마켓플레이스 등록

Claude Code 세션에서 아래 커맨드로 이 저장소를 마켓플레이스로 등록한다.

```
/plugin marketplace add bykolee0/byko-stack
```

로컬에 클론한 경우 경로로 바로 등록할 수도 있다.

```
/plugin marketplace add /path/to/byko-plugins
```

### 2. 플러그인 설치

등록한 마켓플레이스에서 원하는 플러그인을 설치한다.

```
/plugin install byko-stack@byko-plugins
```

설치 후 `/plugin` 커맨드로 활성 상태를 확인할 수 있다.

### 3. 업데이트

원본 저장소에 변경이 있으면 마켓플레이스를 갱신한다.

```
/plugin marketplace update byko-plugins
```

## 플러그인 목록

### byko-stack

스펙 기반 개발(Spec-Driven Development) 워크플로우를 위한 스킬 모음.

| 스킬 | 역할 |
| --- | --- |
| `spec-designer` | 유저와 대화하며 구현 스펙 문서를 설계·작성한다. |
| `spec-dev` | 작성된 스펙을 기반으로 실제 구현을 수행하거나 ralph-loop 준비물을 생성한다. |
| `claude-eval` | `claude -p`를 사용해 독립된 컨텍스트에서 문서/코드를 평가한다. |
| `codex-eval` | OpenAI Codex CLI로 다른 모델 시각에서 교차 검증한다. |
| `eval-gate` | `claude-eval`과 `codex-eval`을 오케스트레이션해 스펙/계획/구현의 품질 게이트 역할을 한다. |

#### 기본 워크플로우

```
/spec-designer   →  스펙 작성
/eval-gate spec  →  스펙 품질 검증
/spec-dev        →  구현
/eval-gate implementation  →  구현 결과 검증
```

각 스킬의 세부 사용법은 해당 스킬 디렉토리의 `SKILL.md`를 참고한다.

## 신규 플러그인 추가

새 플러그인을 이 마켓플레이스에 추가하려면,

1. `plugins/<플러그인-이름>/` 디렉토리를 만든다.
2. 필요한 `skills/`, `commands/`, `agents/`, `hooks/` 등을 배치한다.
3. `.claude-plugin/marketplace.json`의 `plugins` 배열에 항목을 추가한다.

```json
{
  "name": "<플러그인-이름>",
  "source": "./plugins/<플러그인-이름>"
}
```
