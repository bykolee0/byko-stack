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
│   ├── byko-stack/        # Claude Code용 작업 루프: 목표 → 조사 → 설계 → 구현 → 검증 (skills + agents)
│   ├── byko-stack-codex/  # Codex용 목표 중심 플레이북·재사용 스킬
│   ├── byko-goal/         # 장기 목표를 새 세션 반복으로 자율 완수하는 Claude Code 워크플로우
│   └── byko-goal-codex/   # native goal + subagent 기반 Codex 포팅
└── README.md
```

각 플러그인 내부 구조 (해당하는 것만):

```
plugins/<플러그인>/
├── .claude-plugin/plugin.json   # Claude Code 매니페스트 (Codex용은 .codex-plugin/plugin.json)
├── skills/                       # 스킬 (각 <스킬>/SKILL.md)
├── agents/                       # 서브에이전트 정의
├── shared/                       # 스킬 간 공유 규약·템플릿
├── scripts/                      # 스킬이 호출하는 도구
└── codex/skills/                 # Codex에만 노출하는 스킬 (byko-stack: agent-harness-builder)
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
- 플러그인 매니페스트: `plugins/byko-stack/.codex-plugin/plugin.json` (Codex에는 agent-harness-builder 하나만 노출)
- Codex 전용 포팅 매니페스트: `plugins/byko-stack-codex/.codex-plugin/plugin.json`
- 장기 goal 포팅 매니페스트: `plugins/byko-goal-codex/.codex-plugin/plugin.json`
- 스킬 디렉토리: `plugins/byko-stack/codex/skills/`
- Codex 전용 스킬 디렉토리: `plugins/byko-stack-codex/skills/`
- Codex goal 스킬 디렉토리: `plugins/byko-goal-codex/skills/`

로컬에서 사용할 때는 Codex가 이 저장소의 `.agents/plugins/marketplace.json`을 읽을 수 있는 위치에 두거나, Codex 환경의 플러그인 마켓플레이스 설정에서 이 저장소를 로컬 마켓플레이스로 등록한다.

## 플러그인 목록

### byko-stack

**0.5.1 — 요청 하나를 목표부터 검증까지 잇고, 문제가 드러나면 원인 단계로 되돌아가는 Claude Code 작업 루프.** 기능 개발·수정·리팩터·리뷰 지적 반영, 제보·알람의 원인·영향 판단, 그런 작업의 재개가 들어오면 `work` 스킬이 요청 전체를 맡는다. 설명만 원하는 질문과 일반 대화에는 끼어들지 않는다.

```
요청 ─▶ work ─▶ 목표 복원 → 연결 조사 → 설계·검증 기준 → 구현 → 검증 → 인계·보고
                   ▲                                                       │
                   └───── 실패 원인에 따라 그 단계의 항목을 다시 연다 ─────┘
```

- **경로.** 요청이 원하는 결과로 진단(사건·원인·영향), 변경(기능·수정), 구성(비교·계획만 같은 그 밖의 작업) 가운데 하나를 고르고 그 경로의 항목을 작업 기록에 옮긴다. 생략한 항목은 지우지 않고 사유를 남긴다.
- **순서를 지키는 곳은 셋이다.** 현행(as-is)을 보기 전에 방법을 정하지 않는다. 검증 기준은 구현 전에 쓴다. 최종 대상 commit에 독립 판정이 없으면 완료하지 않는다.
- **무게는 조사로 정한다.** 기본은 '보통'이고, '가벼움'은 조사로 근거를 얻어야 줄어든다. 금액·권한·데이터·정책처럼 민감한 축은 사람에게 넘기지 않고 맞는 검토 관점과 보존 기준을 더한다.
- **사람에게 가져가는 것.** 조사·검토·재조사로도 풀리지 않는 정책·의도 결정, 요청이 허락하지 않은 비가역·공유 환경 행동만 결정할 수 있는 형태로 가져간다. 단계별 승인 대기는 없다.

**작업 기록** — 대상 리포의 `.byko/work/<날짜-이름>/`. `.byko/.gitignore`(`*` 한 줄)로 git에서 빠지므로 PR에 섞이지 않는다.

| 파일 | 담는 것 | 쓰는 이·읽는 이 |
| --- | --- | --- |
| `brief.md` | 일의 정의: 요청 원문 위치, 육하원칙 대목표, 범위·하지 말 것, 리포 맥락 출처, 판단과 연결, 구현 전 검증 기준. 작성자의 결론은 넣지 않는다 | 메인이 쓴다. 모든 작업자가 먼저 읽고, 첫 검토자는 이것만 읽는다 |
| `record.md` | 진행: 경로·무게·구성, 열린 항목, 진행 중 위임, 결정과 바뀐 것, 검토 결과와 처분 | 메인만 쓴다. 압축이나 새 세션 뒤 여기서 이어간다 |
| 조사·후보·검토 결과 파일 | 서브에이전트 각자의 결과 | 그 서브에이전트가 쓴다 |

**스킬**

| 스킬 | 역할 |
| --- | --- |
| `work` | 진입 스킬. 요청 전체를 맡고, 작업 기록의 열린 항목으로 다음 행동을 고른다. `/byko-stack:work`로 직접 부를 수도 있다. |
| `design` | 방법 선택과 구현 전 검증 기준. 실제로 다른 접근이 둘 이상이면 후보를 비교한다. "설계·계획만" 요청에 단독으로도 쓴다. |
| `review` | 다관점 독립 검토 구성, 브랜치·PR 단독 리뷰, PR에 달린 외부 지적(리뷰 봇·CI) 판정. |
| `review-run` | 다음 단계를 막는 독립 검토 하나를 reviewer에게 맡기고 결과를 기다린다. `work`·`design`·`review`가 부른다. |

**서브에이전트** (`agents/`)

| 에이전트 | 역할 | 모델·effort |
| --- | --- | --- |
| `code-explorer` | 판단이 기대는 연결을 따라가는 분리 조사. 근거·확인 수준·찾아본 곳을 결과 파일로 돌려준다. | opus-5-5 · high |
| `implementer` | 쓰기 범위가 분리된 구현 단위. 검증 기준에서 테스트를 유도하고 DONE·BLOCKED·BOUNCE_BACK으로 보고한다. | opus-5-5 · high |
| `proposer` | 방향 하나의 설계 후보 작성. 다른 후보를 읽지 않고 판정하지 않는다. | opus-5-5 · high |
| `reviewer` | 독립 검토. '기준 대조'와 '문제 적합' 두 입장으로 통과·수정 필요·미검증을 판정한다. | opus-5-5 · high |

서브에이전트에는 Skill·Agent 도구가 없어 조율 스킬을 되부르거나 다시 위임하지 않는다.

**effort.** `work`는 부른 턴을 high로 돈다. 단독으로 부른 `review`·`design`은 세션 effort를 따른다(브리프와 검토 관점을 쓰는 메인의 판단이 검토 정확도를 좌우했다). 세션이 xhigh·max여도 그 턴만 high이고, 다음 입력부터 세션 값으로 돌아온다. Opus 5.5는 xhigh·max에서 호출마다 훨씬 길게 생각하고, 같은 사례 평가에서 이 루프의 시간 대부분이 그 출력에서 나왔다(측정은 [보고서](docs/reports/byko-stack-0.5.md)). 대화형 세션에서는 위임 완료 알림으로 열린 다음 턴부터 세션 effort로 돌아가므로 효과는 부르는 턴에 한정된다. 더 높은 effort로 돌리려면 `CLAUDE_CODE_EFFORT_LEVEL` 환경변수를 쓴다. 스킬과 서브에이전트 설정보다 앞서므로 검토자를 포함한 모든 서브에이전트도 그 값으로 돈다.

**0.4.0에서 바뀐 것.** spec 주도 단계 스킬(`spec-designer`·`spec-dev`·`eval-gate`·옛 `review`)은 위 네 스킬로 바꿨고 `codex-eval`은 뺐다. `evaluator`는 `reviewer`로 합쳤다. HTML 문서 체계(`shared/`, `scripts/byko-doc.py`, `assets/`, `examples/`)는 없앴다. 대상 리포에 남은 0.4.0 산출물(`docs/specs/…`)은 관련될 때 원자료로 읽고, 옮기거나 지우지 않는다. `agent-harness-builder`는 Codex에만 노출하는 `codex/skills/`로 옮겼다.

### byko-stack-codex

**0.6.0 — 일반 요청에서 목표·조사·설계·구현·독립 검증을 연결하는 Codex 플러그인.** `byko-work`가 요청과 유효한 합의를 유지하고 진단·변경·미정형 작업의 기본 경로를 수행한다. 전문 스킬은 메인이나 서브에이전트에서 단독으로 사용할 수도 있다.

| 스킬 | 역할 |
| --- | --- |
| `byko-work` | 이슈·기능·알람·수정·재개 요청의 전체 조율. 진단만 요청하면 설명으로 종료한다. |
| `byko-design` | 육하원칙 목표·보존·검증 기준을 구체화하고 방법·계획의 독립 검토를 연결한다. |
| `byko-review` | 목표·계획·구현·뷰어의 독립 검토를 구성하고 근거로 종합한다. |
| `byko-propose` | 주어진 기준에 맞는 방법 후보를 작성한다. 전체 조율이나 검토자 생성은 하지 않는다. |
| `byko-analyze` · `byko-implement` | 범위가 정해진 조사·구현을 수행하고 실제 근거를 반환한다. |
| `byko-review-document` · `byko-review-code` · `byko-review-viewer` | 맡은 문서·코드·화면을 검토한다. 직접 작업하거나 위임받은 검토자가 사용한다. |
| `byko-build-viewer` | 독자에게 맞는 설명·시각화 자료를 만든다. 형식 미지정 시 HTML이다. |

일반 요청은 `byko-work`의 description을 통해 발견되도록 구성한다. 확실한 진입이 필요하면 `$byko-work`로 지정한다. 암묵 발견·선택은 실행 환경과 모델에 영향을 받으며 설치만으로 모든 요청을 가로채는 hook은 아니다. 이름을 지정한 전문 스킬 요청은 해당 범위를 유지한다.

진단은 관찰·원인·고객 영향·회복·미확인을 구분한다. 변경은 현행 이해와 보존·검증 기준을 준비한 뒤 설계·구현·독립 검토·관련 재작업으로 이어진다. 플레이북에 없는 요청도 원하는 결과와 허용 범위로 재사용 능력을 연결한다. 조사 대상은 코드·정책 같은 예시 목록으로 닫지 않는다. 기본 수행을 먼저 제시하고 충분한 근거로만 축소한다.

기존 문서·진행 체계가 있으면 공유·갱신한다. 새 지속 작업은 `docs/work/<작업>/index.md`에서 시작하고 독립적인 읽기·갱신이 필요할 때만 분석·설계·검증 자료를 나눈다. 단계·작업자별 문서세트나 HTML을 자동 생성하지 않는다. 위임·재개에서는 목표·합의·원자료와 현재 대상을 대조하며 요약의 공백 목록을 조사 범위의 상한으로 삼지 않는다.

역할은 분석가·설계자·구현자·검토자·뷰어 제작자이며 설정은 [역할 안내](plugins/byko-stack-codex/agents/README.md)에 있다. TOML helper는 생성 설정을 준비할 뿐 자동 등록·실행·권한 강제를 하지 않는다. 지원하지 않는 위임이나 독립 검토는 미실시로 표시한다.

**0.5에서 이전:** `codex-spec-dev` → `byko-work`, `codex-spec-designer` → `byko-design`, `codex-review` → `byko-review`. 패키지 이름은 유지하며 구명칭 스킬의 중복 wrapper는 제공하지 않는다. 기존 작업 문서는 자동 이관하지 않고 이어받는다. 과거 보고서는 당시 이름을 유지한다.

[구현·검증 기록](docs/reports/byko-stack-codex-0.6.md)에서 확인한 행동과 남은 한계를 구분한다.

### byko-goal

장기 실행 목표를 **새 세션 반복**으로 자율 완수하는 워크플로우. 한 세션에 끝나지 않는 큰 목표를, 세션 크기의 체크리스트로 분해해 하나씩 자율적으로 완수한다. 코드뿐 아니라 집필·기획·리서치 등 도메인 무관 — 검증 기준은 목표에 따라 문서로 정의된다.

핵심은 **드라이버(오래 삶, 가벼움) / worker(일회용, 무거움) / 디스크 상태**의 분리다. 오래 사는 드라이버는 직접 일하지 않고 task마다 worker를 띄워 한 줄 결과만 받으므로 비대해지지 않는다. 일회용 worker는 구현·평가·수정을 자기 컨텍스트에서 끝내고 죽는다. 유일한 기억은 `docs/goals/<slug>/`의 문서라, 컨텍스트 요약·세션 종료에도 무손실로 이어진다.

회귀와 계획 드리프트는 세 겹으로 막는다 — 매 task의 evaluator가 자기가 건드린 이전 task를 함께 검증하고(표적), `checkpoint_every`마다 `auditor`가 전역 회귀와 남은 체크리스트의 타당성을 점검하며(주기), 마지막에 최종 eval로 전체를 검수한다. **목표·완수조건은 고정**이고, 체크리스트는 진행에 따라 auditor가 재계획한다(파괴적 변경은 예산으로 제한).

0.3부터는 **비용과 시간의 모델**이 더해졌다(같은 플러그인으로 돌린 목표 9개의 실측에서 나온 것). ① 판정과 회차의 정본은 `eval/NN-<ts>.md` 파일이고 드라이버가 파일 수·판정 줄로 worker의 말을 대조한다 — 한도를 받는 쪽이 스스로 세지 않는다. ② 매 회 읽히는 문서(goal·knowledge·ownership·run-state)에는 읽기 계약(누가 무엇을 매번 읽나)과 쓰기 기준("다음 worker가 매번 읽어야 할 만큼 항구적인가")이 있고, auditor가 체크포인트마다 있을 자리가 아닌 것을 영역 파일·archive/로 옮긴다 — 계약 파일과 append-only 로그(`history.md`)는 섞이지 않는다. 크기는 기준이 아니다; 위치·형태·관련성이 기준이고, 신호는 task당 실제 소요·토큰의 추세다. ③ 완료조건은 evaluator 하나가 한 회차에 닫을 수 있는 양(필요한 만큼만, 진입점 하나로 접기, 고정점 있는 술어)이어야 하고, 하네스 기록은 조건이 아니다. ④ 활성 시간·공회전을 드라이버가, task당 비용 추세를 auditor가 잰다 — 측정은 돈이 나가는 자리에서.

**스킬**

| 스킬 | 역할 |
| --- | --- |
| `goal-design` | 유저와 대화로 장기 목표를 설계해 문서 세트(goal.md·run-state.md·knowledge.md)를 만든다. 목표를 세션 크기 task로 분해하고, 완수 조건과 캡(반복/시간)을 정한다. |
| `goal-run` | fire-and-forget 드라이버. 체크리스트가 전부 완료되거나 캡에 닿을 때까지 task마다 worker를 띄우고, 결과를 디스크(eval 파일·회차 수)와 대조한다. 매 반복 디스크를 재독해 무손실 재개하고, task당 소요·토큰을 기록하며 공회전을 잰다. |

**서브에이전트** (`agents/`)

| 에이전트 | 역할 |
| --- | --- |
| `worker` | task 1개를 끝까지 완결하는 일회용 실행자. 완료조건을 세우고 작업한 뒤 evaluator 하나로 독립 검증을 받아 통과까지 수정한다(판정은 eval 파일에서 읽는다). 큰 task는 explorer·일반 서브에이전트로 팬아웃. |
| `evaluator` | 격리 컨텍스트에서 task 완료조건을 독립 검증한다. 호출자 주장 불신, 디스크 정본과 실측으로 PASS/FAIL 판정. 보고서를 먼저 만들고(PENDING) 갱신하므로 죽어도 회차가 남는다. |
| `auditor` | 주기적 체크포인트마다 전역 회귀·체크리스트 재검증·문서 정리(비용 추세·있을 자리가 아닌 것 옮기기·운영 노트 은퇴)를 수행한다. 상세는 audit/에 남기고 드라이버엔 concise 델타만 반환. |
| `explorer` | read-only 조사 전담(코드 분석·웹 리서치). 근거가 달린 사실만 보고한다. |

#### 기본 워크플로우

```
/goal-design               →  목표 설계 + task 분해 (docs/goals/<slug>/ 생성)
claude --dangerously-skip-permissions   →  무프롬프트 세션으로 전환
/goal-run <slug>           →  자율 실행 (완수 또는 캡까지 반복, 재호출로 재개)
```

자율 실행은 무프롬프트(자동승인)를 전제로 한다 — `goal-design`이 마지막에 권장 권한 설정과 실행 커맨드를 안내한다. 공유 규약은 `plugins/byko-goal/shared/`에 있다.

### byko-goal-codex

`byko-goal`의 핵심인 **고정 goal contract + 동적 task plan + 파일 기반 기억 + 독립 검증**을 Codex 실행 모델에 맞게 포팅한 플러그인이다. blanket 자동승인을 요구하지 않고 Codex native goal lifecycle을 사용하며, 자율 실행과 action 권한을 분리한다.

`docs/goals/<slug>/`에는 고정 계약(`goal.md`), 가변 task graph(`plan.md`), machine state(`state.json`), 압축 지식(`knowledge.md`), append-only history(`journal.md`)가 남는다. task는 삭제하지 않고 `superseded`로 보존하므로 auditor가 실행 중 add/split/refine/reorder를 해도 변경 근거와 과거 계획이 사라지지 않는다.

main session만 authoritative state를 갱신한다. worker는 실제 task를 수행하고, fresh evaluator는 worker 설명 없이 disk 정본과 실측으로 판정하며, auditor는 checkpoint마다 회귀와 남은 plan을 검토한다. write scope가 확실히 분리된 task만 병렬화한다.

**스킬**

| 스킬 | 역할 |
| --- | --- |
| `codex-goal-design` | objective, DoD, scope, 승인 경계, task acceptance를 설계하고 durable goal 문서 세트를 만든다. |
| `codex-goal-run` | native goal을 생성·재개하고 worker/evaluator/auditor subagent loop를 완수 또는 안전한 stop까지 실행한다. |

#### 기본 워크플로우

```text
$byko-goal-codex:codex-goal-design <장기 목표>
$byko-goal-codex:codex-goal-run <slug>
```

실행이 cap, 사용자 승인, 반복 blocker에서 멈춰도 같은 run skill을 다시 호출하면 `state.json`과 journal에서 이어진다. 공유 계약은 `plugins/byko-goal-codex/shared/`에 있다.

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
