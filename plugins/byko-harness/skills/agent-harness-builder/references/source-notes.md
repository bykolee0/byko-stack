# 근거와 내력

스킬을 고칠 때 왜 지금 모양인지 확인하려고 남긴다. 근거마다 날짜가 있다. 모델과 도구가 바뀌면 다시 확인한다.

## 내력

- **2026-02:** OpenAI "Harness engineering"(2026-02-11)을 바탕으로 리포 하네스를 손으로 구성했다. AGENTS.md를 약 100줄 목차로 두고, docs/를 지식의 원본으로 삼고, 반복 실패는 검사로 만드는 방식이었다.
- **2026-05:** 한 Python 프로젝트의 하네스 작업을 일반화해 `agent-harness-builder`를 만들었다. 당시 구성은 AGENTS.md 지도, docs/{references, design-docs(ADR 0001), specs, exec-plans, generated}, pytest 구조 검사였다. byko-stack 안에 두고 Claude·Codex가 함께 썼다.
- **2026-11(이 판):** 9개월 사이 모델과 도구가 바뀐 것을 근거로 다시 썼고, 독립 플러그인 byko-harness로 옮겼다.

## 바뀐 판단과 근거

| 이전 | 지금 | 근거 |
|---|---|---|
| AGENTS.md는 지도, 세부 지식은 에이전트가 docs에서 찾아 읽음 | AGENTS.md에 영역 색인과 "언제 여는지", 규칙, 문서 규격을 둠. 꼭 지킬 정책은 검사로도 막음 | 열지 말지 정해야 하는 문서는 잘 열리지 않음: 스킬로 둔 문서는 56% 미호출이고, AGENTS.md 안 문서 색인은 통과율 100%(Vercel, 2026-01-27). 규칙이 자동 로드 파일에 없을 때 정책 파일을 연 경우 3.5%, 위반 248건 중 242건이 정책을 열지 않은 채 발생(Yang 외, arXiv 2607.26819). 로드된 지시는 잘 따름(Gloaguen 외, arXiv 2602.11988) |
| AGENTS.md 하나가 진입 파일 | CLAUDE.md에 `@AGENTS.md`. 하위 폴더 AGENTS.md 옆에도 같은 CLAUDE.md | Claude Code(2.1.277 이후)는 CLAUDE.md가 없으면 AGENTS.md를 직접 읽고 하위 폴더 것도 그때그때 읽는다. 작업 폴더나 그 위에 CLAUDE.md가 있으면 CLAUDE.md만 읽고, 코드 블록 안의 가져오기는 무시한다(Claude Code memory 문서, 2026-11-11 확인). 직접 읽지 못하는 세션도 있어 가져오기를 두고, 그 대신 하위 폴더에도 CLAUDE.md를 둔다 |
| 아키텍처·개요 서술 권장 | 코드로 알 수 없거나 매 세션 다시 파야 하는 것만 씀 | "Only write down what Claude can't find by reading the repo, or what it would otherwise spend time rediscovering every session." 아키텍처·파일 배치 서술은 "What you can stop doing"으로 분류(Claude Code best practices). 저장소 개요는 도움이 안 됨(Gloaguen 외) |
| design-docs/ADR·specs·exec-plans를 관리 | 결정·작업은 records(로그), 관리는 wiki(최종 정의)만 | ADR은 시간이 지나며 관리가 어려웠다(사용자 경험). LLM Wiki: 원자료(raw)와 LLM이 유지하는 위키를 나누고, 위키는 점검(lint)으로 모순·낡음·고아를 찾음(Karpathy, gist "llm-wiki.md", 2026-04-04) |
| docs/README.md(문서 지도) | AGENTS.md 색인 + 폴더별 index.md | 항상 로드되는 색인이 쓰임(Vercel). index를 먼저 읽고 파고드는 방식(LLM Wiki) |
| generated/ 따로 | references로 합치고 index에 만드는 명령을 적음 | 둘 다 SSOT가 아닌 참고 자료. 색인 없는 자료는 이유 없이 남음(사용자 판단) |
| 정책은 ADR의 결정 | 정책이 wiki의 중추이고 상태는 confirmed/from-code | 정책을 실행 조건으로 다룸(Palantir Ontology 문서). 예외 없이 지킬 규칙은 hook·deny 규칙으로(Claude Code best practices). 도움이 된 규칙은 모두 제약형(Zhang 외, arXiv 2604.11088) |
| 문서 구조 검사 | wiki 규격 검사(프론트매터, 정의 위치, 색인 일치, 근거 경로, AGENTS.md 크기, CLAUDE.md 가져오기) | 낡은 지시 파일을 90.1% 따름, 우선순위 한 문장으로 코드 따르기 4.2%→91.4%(Xu·Wu, arXiv 2610.30571). 명세가 낡는 것이 주된 실패(Codified Context, arXiv 2602.20478) |
| 단일 흐름 | 경우별 플레이북(새·기존 보완/정렬·유지·개발 외), 큰 리포는 병렬 분석과 독립 검토 | 하위 에이전트는 병렬 작업, 시끄러운 출력 분리, 독립 검토에 좋고 같은 일을 맡기는 것만으로는 답이 나아지지 않음(Claude Code best practices). 서브시스템을 읽기 전용 에이전트로 지도화한 팀들(Anthropic, 2026-05-14) |

## 유지한 것

- 기존 리포는 먼저 읽고, 파일로 알 수 있는 것은 묻지 않는다.
- 미결정을 몰래 정하지 않는다. 사실 라벨은 정책 상태(confirmed/from-code)와 "미결정" 절로 이어졌다.
- 검사는 리포의 기존 도구로 만들고, 새 도구를 들이지 않는다.
- 실패 메시지 표준: 무엇·어디·왜·어떻게
- 실행되는 검사가 없으면 완성이라 하지 않는다.
- 질문은 한 번에 3개 이내
- 큰 변경 기록의 형식: 목표·범위 / 검증 기준 / 미결정 / 결과

## 뺀 것

| 이전 | 지금 | 이유 |
|---|---|---|
| 사실 라벨 `recommended`·`open`·`blocking` | 문서에는 정책 상태(`confirmed`·`from-code`)와 "미결정"만 둔다. 추천은 보고의 "다음 후보"로 간다 | 문서에 적힌 추천을 다음 에이전트가 규칙으로 읽는다. 로드된 지시는 따르고(Gloaguen 외), 낡거나 틀린 파일도 따른다(Xu·Wu) |
| 기초 ADR `docs/design-docs/0001-agent-harness-foundation.md`(status proposed) | AGENTS.md "문서 규격"·"미결정"과 records의 결정 기록으로 나눴다 | 기록은 로그이고, 지금 기준은 AGENTS.md와 wiki가 말한다 |
| "모호함" 상태 | 가장 가까운 경우를 고르고 이유를 보고한다. 질문 여부는 사람이 있는지(원칙 7)로 정한다 | 비대화형 실행에서도 멈추지 않게 하기 위해서다 |
| 자율 수준 질문(문서만~PR 자동화) | 하네스의 범위를 문서와 검사로 고정했다 | 작업 흐름 자동화는 byko-stack 같은 작업 도구의 몫이다 |
| 스펙 추적 검사(테스트 없는 수용 기준) | 없앴다 | 스펙이 records(로그)로 내려가 관리 대상이 아니다 |
| 명령 검사(문서의 명령이 낡음) | 자동 검사 후보에서 빼고 유지 작업의 확인 항목으로 옮겼다 | 판단: 명령이 있는지 보는 곳이 리포마다 달라(매니페스트, Makefile, CI) 공통 검사로 만들기 어렵다 |
| language-adapters.md | checks.md의 "언어별로 만들기"·"언어별 수단"으로 줄였다 | 실제로 쓰는 내용은 러너별 옮기는 법과 강제 수단뿐이었다 |

## 근거의 한계

- 컨텍스트 파일 전반의 효과는 연구마다 엇갈린다.
  - 비용이 20% 넘게 늘고 성공률은 대체로 그대로였다(Gloaguen 외).
  - 실행 시간과 출력 토큰이 줄었다(Lulla 외, arXiv 2601.20404).
- Vercel 결과는 업체 자체 평가이고, 도구 사용이 나아지면 격차가 줄 수 있다고 스스로 밝혔다.
- 대부분 2026년 arXiv 예비 논문이고, 상당수가 단독 저자다.
- AGENTS.md가 가리키는 문서를 에이전트가 따라 여는 비율을 잰 연구는 찾지 못했다.
- 정책 판단과 데이터 흐름 이해를 직접 잰 연구도 찾지 못했다.

## 원자료

- OpenAI, Harness engineering — https://openai.com/index/harness-engineering/
- Karpathy, LLM Wiki — https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Claude Code best practices — https://code.claude.com/docs/en/best-practices
- Claude Code memory — https://code.claude.com/docs/en/memory
- Codex AGENTS.md — https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Vercel — https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals
- Gloaguen 외 — https://arxiv.org/abs/2602.11988
- Yang 외 — https://arxiv.org/abs/2607.26819
- Xu·Wu — https://arxiv.org/abs/2610.30571
- Zhang 외 — https://arxiv.org/abs/2604.11088
- Codified Context — https://arxiv.org/abs/2602.20478
- Lulla 외 — https://arxiv.org/abs/2601.20404
- Anthropic, Claude Code in large codebases — https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start
- matklad, ARCHITECTURE.md — https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html
