```
██████╗ ██╗   ██╗██╗  ██╗ ██████╗     ███████╗████████╗ █████╗  ██████╗██╗  ██╗
██╔══██╗╚██╗ ██╔╝██║ ██╔╝██╔═══██╗    ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
██████╔╝ ╚████╔╝ █████╔╝ ██║   ██║    ███████╗   ██║   ███████║██║     █████╔╝ 
██╔══██╗  ╚██╔╝  ██╔═██╗ ██║   ██║    ╚════██║   ██║   ██╔══██║██║     ██╔═██╗ 
██████╔╝   ██║   ██║  ██╗╚██████╔╝    ███████║   ██║   ██║  ██║╚██████╗██║  ██╗
╚═════╝    ╚═╝   ╚═╝  ╚═╝ ╚═════╝     ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚══════╝╚═╝  ╚═╝
 :: byko-plugins ::                                          (Claude Code/Codex)
```

> 별도의 프레임워크 없이, 오직 스킬만으로 동작하는 미니멀리즘 하네스.

> English version: [README.en.md](./README.en.md)

## 구조

```
byko-plugins/
├── .agents/
│   └── plugins/
│       └── marketplace.json # Codex 마켓플레이스 메타데이터 및 플러그인 목록
├── .claude-plugin/
│   └── marketplace.json     # Claude Code 마켓플레이스 메타데이터 및 플러그인 목록
├── plugins/
│   └── byko-stack/          # 개별 플러그인
│       ├── .codex-plugin/   # Codex 플러그인 매니페스트
│       ├── .claude-plugin/  # Claude Code 플러그인 매니페스트
│       └── skills/          # 플러그인에 포함된 스킬들
└── README.md
```

## 설치 방법

### Claude Code

#### 1. 마켓플레이스 등록

Claude Code 세션에서 아래 커맨드로 이 저장소를 마켓플레이스로 등록한다.

```
/plugin marketplace add bykolee0/byko-stack
```

로컬에 클론한 경우 경로로 바로 등록할 수도 있다.

```
/plugin marketplace add /path/to/byko-plugins
```

#### 2. 플러그인 설치

등록한 마켓플레이스에서 원하는 플러그인을 설치한다.

```
/plugin install byko-stack@byko-plugins
```

설치 후 `/plugin` 커맨드로 활성 상태를 확인할 수 있다.

#### 3. 업데이트

원본 저장소에 변경이 있으면 마켓플레이스를 갱신한다.

```
/plugin marketplace update byko-plugins
```

### Codex

이 저장소는 Codex 플러그인 매니페스트도 함께 제공한다.

- 마켓플레이스 메타데이터: `.agents/plugins/marketplace.json`
- 플러그인 매니페스트: `plugins/byko-stack/.codex-plugin/plugin.json`
- 스킬 디렉토리: `plugins/byko-stack/skills/`

로컬에서 사용할 때는 Codex가 이 저장소의 `.agents/plugins/marketplace.json`을 읽을 수 있는 위치에 두거나, Codex 환경의 플러그인 마켓플레이스 설정에서 이 저장소를 로컬 마켓플레이스로 등록한다.

## 플러그인 목록

### byko-stack

스펙 기반 개발(Spec-Driven Development) 워크플로우를 위한 스킬 + 서브에이전트 모음.

메인 세션은 오케스트레이터 역할을 한다 — 대화·결정·조율만 메인 컨텍스트에서 수행하고, 코드 분석·독립 평가·병렬 구현은 서브에이전트에 위임한다. 작업 단위마다 `manifest.md`(워크 매니페스트)가 산출물 경로와 단계 상태의 단일 진실 공급원이 되므로, 모든 스킬은 어떤 순서로든 독립 호출이 가능하다. 공유 컨벤션은 `plugins/byko-stack/shared/`를 참고한다.

**스킬**

| 스킬 | 역할 |
| --- | --- |
| `spec-designer` | 유저와 대화하며 구현 스펙을 설계·작성한다. 분석은 code-explorer에 위임. |
| `spec-dev` | 스펙(또는 합의된 AC)을 기반으로 구현한다. 큰 작업은 implementer 위임 루프로 오케스트레이션. |
| `eval-gate` | evaluator 서브에이전트로 스펙/계획/구현의 정합성을 독립 검증하는 품질 게이트. |
| `review` | reviewer 서브에이전트로 문제 정의에서 출발하는 fresh-eyes 리뷰 (방향·컨벤션·성실성). |
| `codex-eval` | OpenAI Codex CLI로 다른 모델 시각에서 교차 검증한다. |
| `agent-harness-builder` | 기존/신규 프로젝트를 분석해 에이전트용 문서 구조와 실행 가능한 guardrail을 구축한다. |

**서브에이전트** (`agents/`)

| 에이전트 | 역할 |
| --- | --- |
| `code-explorer` | read-only 코드 분석 전담. 파일:라인 근거가 달린 사실만 보고한다. |
| `evaluator` | 격리 컨텍스트에서 체크리스트 기반 정합성 평가 (APPROVED/NEEDS_REVISION). |
| `reviewer` | 문제 정의 기준의 fresh-eyes 리뷰 (SOUND/CONCERNS/RETHINK). |
| `implementer` | 독립 구현 단위(AC)를 코드 작성→테스트→보고까지 완결한다. |

#### 기본 워크플로우

```
/spec-designer             →  스펙 작성 (+ manifest 생성)
/eval-gate spec            →  스펙 정합성 검증
/spec-dev                  →  구현 (전략 A/B/C)
/eval-gate implementation  →  구현 정합성 검증
/review                    →  문제 정의 관점 fresh-eyes 리뷰
```

순서는 강제되지 않는다 — 문답만으로 `/spec-dev`를 바로 호출하거나, 임의 문서에 `/eval-gate custom`만 돌리는 것도 가능하다. 각 스킬의 세부 사용법은 해당 스킬 디렉토리의 `SKILL.md`를 참고한다.

## 신규 플러그인 추가

새 플러그인을 이 마켓플레이스에 추가하려면,

1. `plugins/<플러그인-이름>/` 디렉토리를 만든다.
2. 필요한 `skills/`, `commands/`, `agents/`, `hooks/` 등을 배치한다.
3. Claude Code용 `plugins/<플러그인-이름>/.claude-plugin/plugin.json` 또는 Codex용 `plugins/<플러그인-이름>/.codex-plugin/plugin.json`을 추가한다.
4. Claude Code는 `.claude-plugin/marketplace.json`, Codex는 `.agents/plugins/marketplace.json`의 `plugins` 배열에 항목을 추가한다.

Claude Code:
```json
{
  "name": "<플러그인-이름>",
  "source": "./plugins/<플러그인-이름>"
}
```

Codex:
```json
{
  "name": "<플러그인-이름>",
  "source": {
    "source": "local",
    "path": "./plugins/<플러그인-이름>"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Productivity"
}
```
