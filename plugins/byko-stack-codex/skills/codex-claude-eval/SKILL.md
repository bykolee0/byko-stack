---
name: codex-claude-eval
description: Codex 워크플로우에서 claude -p를 사용해 스펙, 계획, 구현 결과를 별도 컨텍스트로 평가하는 선택적 교차검증 스킬. "$byko-stack-codex:codex-claude-eval spec docs/specs/project/spec.md", "$byko-stack-codex:codex-claude-eval plan implementation-plan.md --output ...", "Claude로 eval" 요청이나 codex-eval-gate의 선택 평가 단계에서 사용한다.
---

# Codex Claude Eval

`claude -p`가 설치된 환경에서만 사용한다. Codex의 기본 독립 검증은 `codex-review`이며, 이 스킬은 선택적 교차검증이다.

## Workflow

### 1. Preflight

```bash
command -v claude >/dev/null 2>&1
```

없으면 설치 안내만 하고 실패를 결과에 기록한다. `codex-eval-gate`에서 호출된 경우 전체 게이트를 즉시 실패시키지 않는다.

### 2. 요청 파일 작성

`references/request-template.md`와 `references/checklists.md`를 사용한다.

출력 경로가 없으면:

```text
docs/specs/<project>/eval-results/<mode>-claude-<timestamp>.md
```

프로젝트 경로를 추론할 수 없으면 `.myagents/claude-eval-<timestamp>.md`를 사용한다.

요청 파일에는 target files와 source documents를 포함한다. Claude 프로세스는 현재 대화 컨텍스트를 모른다는 전제로 작성한다.

### 3. 실행

긴 평가가 될 수 있으므로 현재 도구의 긴 타임아웃 또는 세션 실행 기능을 사용한다.

```bash
claude -p \
  --allowedTools "Read,Write,Glob,Grep" \
  --permission-mode bypassPermissions \
  "<task>
<absolute request path> 파일을 읽고 Target Files를 확인하라.
Evaluation Criteria에 따라 평가하라.
결과를 같은 파일의 응답 마커 사이에 작성하라.
근거 없는 FAIL은 작성하지 말라.
</task>"
```

### 4. 결과 검증

Claude 결과도 그대로 믿지 않는다. FAIL 항목을 직접 확인하고 `accepted`, `rejected`, `needs_followup`으로 분류한다.

### 5. 보고

보고에는 다음을 포함한다.
- 판정
- accepted finding
- rejected finding 요약
- 결과 파일 경로
- 다음 단계

## References

- `references/checklists.md`
- `references/request-template.md`
