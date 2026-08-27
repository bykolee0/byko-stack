```
██████╗ ██╗   ██╗██╗  ██╗ ██████╗     ███████╗████████╗ █████╗  ██████╗██╗  ██╗
██╔══██╗╚██╗ ██╔╝██║ ██╔╝██╔═══██╗    ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
██████╔╝ ╚████╔╝ █████╔╝ ██║   ██║    ███████╗   ██║   ███████║██║     █████╔╝ 
██╔══██╗  ╚██╔╝  ██╔═██╗ ██║   ██║    ╚════██║   ██║   ██╔══██║██║     ██╔═██╗ 
██████╔╝   ██║   ██║  ██╗╚██████╔╝    ███████║   ██║   ██║  ██║╚██████╗██║  ██╗
╚═════╝    ╚═╝   ╚═╝  ╚═╝ ╚═════╝     ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚══════╝╚═╝  ╚═╝
 :: byko-plugins ::                                          (Claude Code/Codex)
```

> A minimalist harness that runs on skills and subagents — no extra framework required.

> Korean version: [README.md](./README.md)

## Structure

```
byko-plugins/
├── .agents/plugins/marketplace.json   # Codex marketplace (plugin list)
├── .claude-plugin/marketplace.json    # Claude Code marketplace (plugin list)
├── plugins/
│   ├── byko-stack/        # Spec-driven development (SDD) workflow for Claude Code (skills + agents)
│   ├── byko-stack-codex/  # Codex-native port of the above
│   ├── byko-goal/         # Claude Code workflow for long goals across repeated sessions
│   └── byko-goal-codex/   # Codex port using native goals and subagents
└── README.md
```

Internal structure of each plugin (only the parts that apply):

```
plugins/<plugin>/
├── .claude-plugin/plugin.json   # Claude Code manifest (Codex: .codex-plugin/plugin.json)
├── skills/                       # Skills (each <skill>/SKILL.md)
├── agents/                       # Subagent definitions
├── shared/                       # Cross-skill conventions and templates
├── scripts/                      # Tools skills invoke (byko-stack: doc build/check)
└── assets/                       # Resources shipped into artifacts (byko-stack: doc CSS/JS)
```

## Installation

### Claude Code

#### 1. Register the marketplace

Inside a Claude Code session, register this repository as a marketplace:

```
/plugin marketplace add bykolee0/byko-stack
```

If you have cloned the repo locally, a local path also works:

```
/plugin marketplace add /path/to/byko-plugins
```

#### 2. Install a plugin

Install any plugin from the registered marketplace:

```
/plugin install byko-stack@byko-plugins
```

After installation, run `/plugin` to verify it is active.

#### 3. Update

Pull the latest changes from the upstream repository:

```
/plugin marketplace update byko-plugins
```

### Codex

This repository also includes Codex plugin metadata.

- Marketplace metadata: `.agents/plugins/marketplace.json`
- Plugin manifest: `plugins/byko-stack/.codex-plugin/plugin.json`
- Codex-native port manifest: `plugins/byko-stack-codex/.codex-plugin/plugin.json`
- Long-goal port manifest: `plugins/byko-goal-codex/.codex-plugin/plugin.json`
- Skill directory: `plugins/byko-stack/skills/`
- Codex-native skill directory: `plugins/byko-stack-codex/skills/`
- Codex goal skill directory: `plugins/byko-goal-codex/skills/`

For local use, place this repository where Codex can read `.agents/plugins/marketplace.json`, or register this repository as a local marketplace in your Codex plugin marketplace configuration.

## Plugins

### byko-stack

A collection of skills for a spec-driven development (SDD) workflow.

| Skill | Role |
| --- | --- |
| `spec-designer` | Designs implementation specs with codebase exploration, manifest state, and ambiguity tracking. |
| `spec-dev` | Implements from a spec or agreed ACs with traceability and resumable progress files. |
| `agent-harness-builder` | Builds agent-facing docs and executable guardrails for existing or new projects. |
| `codex-eval` | Cross-validates artifacts from a different model's perspective via the OpenAI Codex CLI. |
| `eval-gate` | Uses an evaluator subagent to gate spec/plan/implementation consistency. |
| `review` | Uses a reviewer subagent for fresh-eyes problem fit, convention fit, and implementation integrity review. |

#### Default workflow

```
/spec-designer             →  write the spec (+ manifest)
/eval-gate spec            →  validate the spec
/spec-dev                  →  implement
/eval-gate implementation  →  validate the implementation
/review                    →  fresh-eyes review from the problem definition
```

See each skill's `SKILL.md` for detailed usage.

#### Artifact formats — the reader decides

Documents a human opens to approve or decide are HTML; state and evidence that agents read and update stay Markdown.

| Artifact | Format | Notes |
| --- | --- | --- |
| `index.html` | HTML (generated) | Status dashboard generated from `manifest.md` — the human entry point |
| `spec.html` | HTML (authored) | **An explainer, not a specification list** — `0.one sentence → 1.concepts → 2.current structure → 3.happy path → 4.where it breaks → 5.what changes → 6.what you must decide → 7.done criteria`. Decisions are collected automatically from inline accents into chapter 6 |
| `implementation-plan.html` | HTML (authored) | Steps, target files, dependencies, blast radius — the document a human approves before code changes |
| `manifest.md`, `ambiguity-ledger.md`, `traceability.md`, `progress.md`, `analysis/`, `eval-results/`, `review-results/` | Markdown | Agent-facing state and evidence; skills summarize these in conversation |

Background comes before results for one reason: that is what lets a reader know what they are approving. HTML artifacts are offline-deterministic — no CDN or external scripts, print-friendly, fully readable with JavaScript disabled. Chapter navigation and the decision list are generated by `scripts/byko-doc.py`. Conventions live in `shared/doc-system.md`, components in `shared/doc-snippets.md`, and a **finished example in `plugins/byko-stack/examples/spec-example.html`**.

### byko-stack-codex

A Codex-native port of the byko-stack development cycle. It keeps the main Codex session as the orchestrator and shares state through `manifest.md` plus file-backed artifacts, rather than relying on one long context.

| Area | Codex direction |
| --- | --- |
| Shared state | `docs/specs/<project>/manifest.md` records the problem definition, artifacts, stage status, and key decisions. |
| Questions | Investigate code/docs first; ask only real user decisions with options and a recommendation. |
| Eval | `codex-eval-gate` checks spec/plan/implementation consistency in an isolated context. |
| Review | `codex-review` performs fresh-eyes review from the manifest's original problem definition. |
| Dev | `codex-spec-dev` can proceed from a spec or from agreed requirements with lightweight ACs. |
| Cross-check | `codex-claude-eval` is optional Claude CLI cross-validation, not the default gate. |

Codex shared conventions live in `plugins/byko-stack-codex/shared/`.

### byko-goal

A workflow that autonomously completes long-running goals across **repeated fresh sessions**. It breaks a goal too large for one session into session-sized checklist items and completes them one at a time. Domain-agnostic — code, writing, planning, research; the "done" criteria are defined as data in the goal's documents, not hardcoded.

The core is a split between a **driver (long-lived, lightweight) / worker (disposable, heavy) / disk state**. The long-lived driver never does the work itself — it spawns one worker per task and receives a single-line result, so it never bloats. Each disposable worker finishes implementation, evaluation, and revision inside its own context, then dies. The only memory is the documents under `docs/goals/<slug>/`, so progress survives context compaction and session termination losslessly.

Regression and plan drift are caught in three layers — each task's evaluator also re-checks the prior tasks it touched (targeted), an `auditor` runs every `checkpoint_every` tasks to check global regression and whether the remaining checklist still holds (periodic), and a final eval inspects the whole at the end. **The goal and completion conditions are fixed**; the checklist is re-planned by the auditor as work proceeds (destructive changes are capped by a budget).

**Skills**

| Skill | Role |
| --- | --- |
| `goal-design` | Designs a long goal with the user and produces the document set (goal.md, run-state.md, knowledge.md). Decomposes the goal into session-sized tasks and sets completion conditions and caps (iterations/time). |
| `goal-run` | The fire-and-forget driver. Spawns a worker per task until the checklist is complete or a cap is hit. Re-reads disk each iteration for lossless resume. |

**Subagents** (`agents/`)

| Subagent | Role |
| --- | --- |
| `worker` | A disposable executor that completes one task end to end. Writes the completion conditions, does the work, and gets independent verification from the evaluator, revising until it passes. Fans out to explorer/sub-workers for large tasks. |
| `evaluator` | Independently verifies a task's completion conditions in an isolated context. Distrusts the caller's claims; judges PASS/FAIL against the on-disk source of truth and direct inspection. |
| `auditor` | Runs global regression and checklist re-validation at periodic checkpoints. Writes details to audit/ and returns only a concise delta (reopen tasks, checklist changes) to the driver. |
| `explorer` | Read-only investigation (code analysis, web research). Reports only evidence-backed facts. |

#### Default workflow

```
/goal-design               →  design the goal + decompose tasks (creates docs/goals/<slug>/)
claude --dangerously-skip-permissions   →  switch to a prompt-free session
/goal-run <slug>           →  autonomous run (repeats until done or cap; re-invoke to resume)
```

Autonomous runs assume a prompt-free (auto-approval) session — `goal-design` ends by guiding the recommended permission setup and the launch command. Shared conventions live in `plugins/byko-goal/shared/`.

### byko-goal-codex

A Codex-native port of the central `byko-goal` ideas: a **fixed goal contract, dynamic task plan, file-backed memory, and independent verification**. It uses the Codex native goal lifecycle instead of requiring blanket auto-approval, keeping autonomous progress separate from action authorization.

Each `docs/goals/<slug>/` stores the fixed contract (`goal.md`), mutable task graph (`plan.md`), machine state (`state.json`), curated knowledge (`knowledge.md`), and append-only history (`journal.md`). Tasks are preserved as `superseded` instead of being deleted, so auditor-driven add/split/refine/reorder changes retain their rationale and history.

Only the main session updates authoritative state. Workers perform assigned tasks, fresh evaluators judge disk truth and direct evidence without receiving worker claims, and auditors check regressions and remaining plan validity at checkpoints. Write workers run in parallel only when their ownership is genuinely disjoint.

**Skills**

| Skill | Role |
| --- | --- |
| `codex-goal-design` | Defines the objective, DoD, scope, authorization boundary, and task acceptance criteria, then creates the durable goal artifact set. |
| `codex-goal-run` | Creates or resumes the native goal and orchestrates worker/evaluator/auditor subagents until completion or a safe stop. |

#### Default workflow

```text
$byko-goal-codex:codex-goal-design <long-running objective>
$byko-goal-codex:codex-goal-run <slug>
```

If a run stops at a cap, approval boundary, or repeated blocker, invoke the same run skill again to resume from `state.json` and the journal. Shared contracts live in `plugins/byko-goal-codex/shared/`.

## Adding a new plugin

To add another plugin to this marketplace:

1. Create a `plugins/<plugin-name>/` directory.
2. Place the required `skills/`, `commands/`, `agents/`, `hooks/`, etc. inside it.
3. Add `plugins/<plugin-name>/.claude-plugin/plugin.json` for Claude Code or `plugins/<plugin-name>/.codex-plugin/plugin.json` for Codex.
4. Append an entry to the `plugins` array in `.claude-plugin/marketplace.json` for Claude Code or `.agents/plugins/marketplace.json` for Codex.

Claude Code:
```json
{
  "name": "<plugin-name>",
  "source": "./plugins/<plugin-name>"
}
```

Codex:
```json
{
  "name": "<plugin-name>",
  "source": {
    "source": "local",
    "path": "./plugins/<plugin-name>"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Productivity"
}
```
