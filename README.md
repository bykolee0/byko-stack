```
██████╗ ██╗   ██╗██╗  ██╗ ██████╗     ███████╗████████╗ █████╗  ██████╗██╗  ██╗
██╔══██╗╚██╗ ██╔╝██║ ██╔╝██╔═══██╗    ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
██████╔╝ ╚████╔╝ █████╔╝ ██║   ██║    ███████╗   ██║   ███████║██║     █████╔╝ 
██╔══██╗  ╚██╔╝  ██╔═██╗ ██║   ██║    ╚════██║   ██║   ██╔══██║██║     ██╔═██╗ 
██████╔╝   ██║   ██║  ██╗╚██████╔╝    ███████║   ██║   ██║  ██║╚██████╗██║  ██╗
╚═════╝    ╚═╝   ╚═╝  ╚═╝ ╚═════╝     ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚══════╝╚═╝  ╚═╝
 :: byko-plugins ::                                          (Claude Code/Codex)
```

> 별도의 프레임워크 없이, 스킬과 서브에이전트만으로 동작하는 미니멀리즘 하네스.

> English version: [README.en.md](./README.en.md)

## 구조

```
byko-plugins/
├── .agents/plugins/marketplace.json   # Codex 마켓플레이스 (플러그인 목록)
├── .claude-plugin/marketplace.json    # Claude Code 마켓플레이스 (플러그인 목록)
├── plugins/
│   ├── byko-stack/        # Claude Code용 스펙 기반 개발(SDD) 워크플로우 (skills + agents)
│   ├── byko-stack-codex/  # 위의 Codex 네이티브 포팅
│   └── byko-goal/         # 장기 목표를 새 세션 반복으로 자율 완수하는 워크플로우
└── README.md
```

각 플러그인 내부 구조 (해당하는 것만):

```
plugins/<플러그인>/
├── .claude-plugin/plugin.json   # Claude Code 매니페스트 (Codex용은 .codex-plugin/plugin.json)
├── skills/                       # 스킬 (각 <스킬>/SKILL.md)
├── agents/                       # 서브에이전트 정의
└── shared/                       # 스킬 간 공유 규약·템플릿
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
- Codex 전용 포팅 매니페스트: `plugins/byko-stack-codex/.codex-plugin/plugin.json`
- 스킬 디렉토리: `plugins/byko-stack/skills/`
- Codex 전용 스킬 디렉토리: `plugins/byko-stack-codex/skills/`

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

### byko-stack-codex

Codex 실행 모델에 맞춘 byko-stack 포팅이다. Claude Code의 플러그인 서브에이전트 구조를 그대로 복제하지 않고, Codex의 main session을 오케스트레이터로 두며 `manifest.md`와 파일 기반 산출물로 스킬 간 상태를 공유한다.

**핵심 차이**

| 영역 | Codex 포팅 방향 |
| --- | --- |
| 상태 공유 | `docs/specs/<project>/manifest.md`가 문제 정의, 산출물, 단계 상태, 핵심 결정을 기록한다. |
| 질문 정책 | 코드/문서로 확인 가능한 것은 직접 조사하고, 유저 결정이 필요한 경우에만 선택지+추천으로 묻는다. |
| eval | `codex-eval-gate`가 스펙/계획/구현의 정합성을 격리 컨텍스트에서 검증한다. |
| review | `codex-review`가 manifest의 원본 문제 정의를 기준으로 fresh-eyes 리뷰를 수행한다. |
| 구현 | `codex-spec-dev`가 스펙이 없어도 합의된 요구와 AC로 경량 매니페스트를 만들고 구현까지 진행한다. |
| 교차검증 | `codex-claude-eval`은 기본 평가가 아니라 Claude CLI 기반 선택 교차검증이다. |

Codex 공유 규약은 `plugins/byko-stack-codex/shared/`에 있다.

### byko-goal

장기 실행 목표를 **새 세션 반복**으로 자율 완수하는 워크플로우. 한 세션에 끝나지 않는 큰 목표를, 세션 크기의 체크리스트로 분해해 하나씩 자율적으로 완수한다. 코드뿐 아니라 집필·기획·리서치 등 도메인 무관 — 검증 기준은 목표에 따라 문서로 정의된다.

핵심은 **드라이버(오래 삶, 가벼움) / worker(일회용, 무거움) / 디스크 상태**의 분리다. 오래 사는 드라이버는 직접 일하지 않고 task마다 worker를 띄워 한 줄 결과만 받으므로 비대해지지 않는다. 일회용 worker는 구현·평가·수정을 자기 컨텍스트에서 끝내고 죽는다. 유일한 기억은 `docs/goals/<slug>/`의 문서라, 컨텍스트 요약·세션 종료에도 무손실로 이어진다.

**스킬**

| 스킬 | 역할 |
| --- | --- |
| `goal-design` | 유저와 대화로 장기 목표를 설계해 문서 세트(goal.md·run-state.md·knowledge.md)를 만든다. 목표를 세션 크기 task로 분해하고, 완수 조건과 캡(반복/시간)을 정한다. |
| `goal-run` | fire-and-forget 드라이버. 체크리스트가 전부 완료되거나 캡에 닿을 때까지 task마다 worker를 띄운다. 매 반복 디스크를 재독해 무손실 재개한다. |

**서브에이전트** (`agents/`)

| 에이전트 | 역할 |
| --- | --- |
| `worker` | task 1개를 끝까지 완결하는 일회용 실행자. 완료조건을 세우고 작업한 뒤 evaluator로 독립 검증을 받아 통과까지 수정한다. 큰 task는 explorer·하위 worker로 팬아웃. |
| `evaluator` | 격리 컨텍스트에서 task 완료조건을 독립 검증한다. 호출자 주장 불신, 디스크 정본과 실측으로 PASS/FAIL 판정. |
| `explorer` | read-only 조사 전담(코드 분석·웹 리서치). 근거가 달린 사실만 보고한다. |

#### 기본 워크플로우

```
/goal-design               →  목표 설계 + task 분해 (docs/goals/<slug>/ 생성)
claude --dangerously-skip-permissions   →  무프롬프트 세션으로 전환
/goal-run <slug>           →  자율 실행 (완수 또는 캡까지 반복, 재호출로 재개)
```

자율 실행은 무프롬프트(자동승인)를 전제로 한다 — `goal-design`이 마지막에 권장 권한 설정과 실행 커맨드를 안내한다. 공유 규약은 `plugins/byko-goal/shared/`에 있다. (Codex 포팅은 추후.)

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
