# Source Notes

이 문서는 skill을 지속적으로 개선하기 위해 근거와 rationale을 보존한다.

## Primary Sources

- OpenAI — Harness Engineering: https://openai.com/ko-KR/index/harness-engineering/
- OpenAI — Unlocking the Codex harness: https://openai.com/index/unlocking-the-codex-harness/
- OpenAI Cookbook — Codex execution plans: https://cookbook.openai.com/articles/codex_exec_plans
- AGENTS.md convention: https://agents.md/
- matklad — ARCHITECTURE.md: https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html
- Alexis King — Parse, don’t validate: https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/

## Lessons Encoded

1. `AGENTS.md`는 큰 manual이 아니라 map이어야 한다.
2. repo-local docs는 agent-visible knowledge의 system of record다.
3. harness 품질은 문서만이 아니라 feedback loop에서 나온다.
4. 반복되는 실패는 tests, lint rules, scripts, generated checks가 되어야 한다.
5. 새 구조를 추가하기 전에 기존 project convention을 먼저 발견해야 한다.
6. Greenfield project는 open decision을 몰래 결정하지 않도록 intake가 먼저 필요하다.
7. Guardrail은 기존 stack을 사용하고 가볍게 시작해야 한다.

## Example That Seeded This Skill

Python/FastAPI 기반 financial data collector에서 다음을 추가했다.

- `docs/README.md`
- `docs/references/`
- `docs/design-docs/0001-agent-harness-foundation.md`
- layer imports, time conventions, docs structure를 검사하는 pytest architecture checks

재사용 가능한 교훈은 “모든 프로젝트에서 pytest를 쓰라”가 아니다. “프로젝트의 기존 validation tool을 사용해, 가장 위험한 convention 몇 개를 실행 가능한 check로 encode하라”는 것이다.
