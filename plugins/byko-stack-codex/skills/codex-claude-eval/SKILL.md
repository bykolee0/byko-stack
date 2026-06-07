---
name: codex-claude-eval
description: Codex 워크플로우에서 claude -p를 사용해 스펙, 계획, 구현 결과를 다른 모델/프로세스 컨텍스트로 교차검증하는 선택 스킬. "$byko-stack-codex:codex-claude-eval spec docs/specs/project/manifest.md", "$byko-stack-codex:codex-claude-eval plan implementation-plan.md --output ...", "Claude로 eval", "교차검증해줘" 요청이나 codex-eval-gate가 논쟁적/되돌리기 어려운 변경을 추가 검증할 때 사용한다. Codex 기본 평가는 아니며, subagent 평가를 대체하지 않고 보완한다.
---

# Codex Claude Eval

`claude -p`가 설치된 환경에서만 사용한다. Codex의 기본 정합성 평가는 `codex-eval-gate`의 isolated Codex evaluator이며, 이 스킬은 다른 모델 시각이 필요할 때 쓰는 교차검증이다.

## Workflow

### 1. Preflight

```bash
command -v claude >/dev/null 2>&1
```

없으면 설치 안내만 하고 실패를 결과에 기록한다. `codex-eval-gate`에서 보조 평가로 호출된 경우, Codex evaluator가 성공했다면 전체 게이트를 즉시 실패시키지 않는다.

### 2. Resolve target

Accept a manifest, spec, plan, changed path list, or explicit output path. If a manifest exists, use only neutral context:

- problem definition
- key decisions
- artifact paths
- test results for implementation mode

Do not include the current session's expected verdict.

### 3. Write request file

Use `references/request-template.md` and `references/checklists.md`.

Default output:

```text
docs/specs/<project>/eval-results/<mode>-claude-<timestamp>.md
```

If no project path can be inferred, use `.myagents/eval-results/`.

Copy target source documents into the request where practical. Claude does not know the current conversation.

### 4. Execute

Use a long timeout/session runner when available:

```bash
claude -p \
  --allowedTools "Read,Write,Glob,Grep" \
  --permission-mode bypassPermissions \
  "<task>
Read <absolute request path>.
Inspect the Target Files.
Evaluate according to the Evaluation Criteria.
Write the result between the response markers in the same file.
Base every FAIL on concrete file/code evidence.
</task>"
```

### 5. Verify findings

Do not trust Claude output blindly. Recheck FAIL items and classify:

- `accepted`
- `rejected`
- `needs_followup`

### 6. Report

Include:

- verdict
- accepted findings
- rejected/needs_followup summary
- result file path
- whether this was standalone or cross-check
- suggested return point

## References

- `references/checklists.md`
- `references/request-template.md`
