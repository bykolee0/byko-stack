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
│   ├── byko-stack/        # Claude Code work loop: goal → research → design → implement → verify (skills + agents)
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
├── scripts/                      # Tools skills invoke
└── codex/skills/                 # Skills exposed only to Codex (byko-stack: agent-harness-builder)
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
- Plugin manifest: `plugins/byko-stack/.codex-plugin/plugin.json` (exposes only agent-harness-builder to Codex)
- Codex-native port manifest: `plugins/byko-stack-codex/.codex-plugin/plugin.json`
- Long-goal port manifest: `plugins/byko-goal-codex/.codex-plugin/plugin.json`
- Skill directory: `plugins/byko-stack/codex/skills/`
- Codex-native skill directory: `plugins/byko-stack-codex/skills/`
- Codex goal skill directory: `plugins/byko-goal-codex/skills/`

For local use, place this repository where Codex can read `.agents/plugins/marketplace.json`, or register this repository as a local marketplace in your Codex plugin marketplace configuration.

## Plugins

### byko-stack

**0.5.0 — a Claude Code work loop that carries one request from goal to verification and returns to the stage that caused a problem.** Feature work, fixes, refactors, review follow-ups, cause/impact questions about a report or alert, and resuming such work all enter through the `work` skill, which owns the whole request. Explanation-only questions and general conversation are left alone.

```
request ─▶ work ─▶ restore goal → trace links → design + checks → implement → verify → hand off
                       ▲                                                                   │
                       └───────────── reopen the items of the stage that caused it ────────┘
```

- **Paths.** The result the request wants picks one path: diagnosis (event, cause, impact), change (feature, fix), or composed (comparisons, plan-only, other work). The path's items are copied into the work record; a skipped item stays with its reason.
- **Three ordering gates.** No method before the current state (as-is) is seen. Verification criteria are written before implementation. Nothing is done until the final target commit has an independent verdict.
- **Weight comes from research.** The default is "normal"; "light" needs evidence from research. Sensitive axes (money, permissions, data, policy) add the matching review perspectives and preservation checks instead of being handed to a person.
- **What goes to a person.** Only policy or intent decisions that research, review, and re-research cannot settle, and irreversible or shared-environment actions the request did not allow — in a form that can be decided. There are no per-stage approval waits.

**Work record** — `.byko/work/<date-name>/` in the target repository. `.byko/.gitignore` (a single `*`) keeps it out of git, so it never lands in a PR.

| File | Holds | Written / read by |
| --- | --- | --- |
| `brief.md` | Definition of the work: where the request lives, a 5W1H goal, scope and non-goals, repo context sources, judgments and the links they rest on, verification criteria written before implementation. No author conclusions | Written by the main session; every worker reads it first, and a first reviewer reads only this |
| `record.md` | Progress: path, weight, composition, open items, running delegations, decisions and changes, review results and dispositions | Main session only; work resumes from here after compaction or in a new session |
| Research, candidate, and review result files | Each subagent's own output | That subagent |

**Skills**

| Skill | Role |
| --- | --- |
| `work` | Entry skill. Owns the request and picks the next action from the open items in the work record. Also callable as `/byko-stack:work`. |
| `design` | Method choice and pre-implementation verification criteria; compares candidates when genuinely different approaches exist. Also usable alone for design- or plan-only requests. |
| `review` | Composes multi-perspective independent review, standalone branch/PR review, and judging external PR findings (review bots, CI). |
| `review-run` | Hands one blocking independent review to the reviewer and waits for the result. Called by `work`, `design`, and `review`. |

**Subagents** (`agents/`)

| Agent | Role | Model · effort |
| --- | --- | --- |
| `code-explorer` | Separate research that follows the links a judgment rests on; returns evidence, confidence level, and places searched in a result file. | opus-5-5 · high |
| `implementer` | Implementation unit with a separate write scope; derives tests from the criteria and reports DONE, BLOCKED, or BOUNCE_BACK. | opus-5-5 · high |
| `proposer` | Writes one design candidate for one direction; does not read other candidates or judge. | opus-5-5 · high |
| `reviewer` | Independent review from two stances, criteria check and problem fit; verdict is pass, needs changes, or unverified. | opus-5-5 · xhigh |

Subagents have no Skill or Agent tool, so they cannot call the orchestration skills back or delegate again.

**Changes from 0.4.0.** The spec-driven stage skills (`spec-designer`, `spec-dev`, `eval-gate`, the old `review`) are replaced by the four skills above, and `codex-eval` is removed. `evaluator` is merged into `reviewer`. The HTML document system (`shared/`, `scripts/byko-doc.py`, `assets/`, `examples/`) is gone. 0.4.0 artifacts left in a target repository (`docs/specs/…`) are read as source material when relevant and are neither migrated nor deleted. `agent-harness-builder` moved to `codex/skills/`, which only Codex sees.

### byko-stack-codex

**0.6.0 — goal-driven playbooks for Codex.** `byko-work` handles issue, feature, incident, change, and resume requests through explicit diagnosis, change, or composed paths. Diagnosis-only requests stop at an evidence-backed explanation. Specialists remain independently usable.

| Skill | Responsibility |
| --- | --- |
| `byko-work` | Own the request, goal, agreements, execution path, and outcome. |
| `byko-design` | Establish the goal, preservation and verification criteria, then orchestrate proposals and independent review. |
| `byko-review` | Coordinate independent document, code, and viewer reviews and validate findings. |
| `byko-propose` | Produce a bounded design proposal without recursive orchestration. |
| `byko-analyze`, `byko-implement` | Investigate or implement an assigned scope. |
| `byko-review-document`, `byko-review-code`, `byko-review-viewer` | Perform the assigned review. |
| `byko-build-viewer` | Produce reader-focused visual explanations; HTML by default. |

Start explicitly with `$byko-work` when reliable selection matters. Natural-language discovery depends on the host and model; the plugin is not an interception hook. Follow the default path, then reduce work only when observed evidence supports doing so. Recheck the goal and valid agreements when accepting results, changing direction, and finishing. Investigation follows relevant dependencies beyond example lists or repository boundaries within the authorized scope.

Reuse and update existing shared work artifacts. New persistent work starts at `docs/work/<task>/index.md`; split analysis, design, and verification only when independently reading or updating them is useful. No mandatory per-stage or per-agent document set. Handoffs connect goals and primary evidence to the actual target; a summary is not proof of complete context.

Five bounded roles cover analysis, proposals, implementation, review, and viewer production. The [role guide](plugins/byko-stack-codex/agents/README.md) explains configuration and host limitations. The helper prepares spawn arguments; it does not register or execute agents or enforce permissions.

**Migration from 0.5:** `codex-spec-dev` → `byko-work`, `codex-spec-designer` → `byko-design`, `codex-review` → `byko-review`. The plugin identity stays unchanged. Old-name wrappers are not retained. Existing task documents are reused, and historical reports keep their original names.

See the [implementation and validation report](docs/reports/byko-stack-codex-0.6.md) for observed behavior and remaining limits.

### byko-goal

A workflow that autonomously completes long-running goals across **repeated fresh sessions**. It breaks a goal too large for one session into session-sized checklist items and completes them one at a time. Domain-agnostic — code, writing, planning, research; the "done" criteria are defined as data in the goal's documents, not hardcoded.

The core is a split between a **driver (long-lived, lightweight) / worker (disposable, heavy) / disk state**. The long-lived driver never does the work itself — it spawns one worker per task and receives a single-line result, so it never bloats. Each disposable worker finishes implementation, evaluation, and revision inside its own context, then dies. The only memory is the documents under `docs/goals/<slug>/`, so progress survives context compaction and session termination losslessly.

Regression and plan drift are caught in three layers — each task's evaluator also re-checks the prior tasks it touched (targeted), an `auditor` runs every `checkpoint_every` tasks to check global regression and whether the remaining checklist still holds (periodic), and a final eval inspects the whole at the end. **The goal and completion conditions are fixed**; the checklist is re-planned by the auditor as work proceeds (destructive changes are capped by a budget).

Since 0.3 the harness also has a **model of cost and time**, derived from measurements across nine goals run with this plugin. ① The source of truth for verdicts and attempts is the `eval/NN-<ts>.md` file; the driver cross-checks the worker's claim against file counts and the verdict line — the party being capped never counts itself. ② The documents read on every iteration (goal · knowledge · ownership · run-state) have a read contract (who reads what, every time) and a write criterion ("will the next worker need this every time?"), and at each checkpoint the auditor moves whatever does not belong there into area files or archive/ — contract files and the append-only log (`history.md`) are never mixed. Size is not the criterion; location, form, and relevance are, and the signal is the trend of real per-task time and tokens. ③ Completion conditions must be closable by one evaluator in one attempt (only as many as needed, folded into a single entry point where one exists, predicates with a fixed point), and harness bookkeeping is never a condition. ④ The driver measures active time and stalls; the auditor watches the per-task cost trend — measured where the cost is actually paid.

**Skills**

| Skill | Role |
| --- | --- |
| `goal-design` | Designs a long goal with the user and produces the document set (goal.md, run-state.md, knowledge.md). Decomposes the goal into session-sized tasks and sets completion conditions and caps (iterations/time). |
| `goal-run` | The fire-and-forget driver. Spawns a worker per task until the checklist is complete or a cap is hit, and cross-checks each result against disk (eval files, attempt counts). Re-reads disk each iteration for lossless resume; records per-task time/tokens and detects stalls. |

**Subagents** (`agents/`)

| Subagent | Role |
| --- | --- |
| `worker` | A disposable executor that completes one task end to end. Writes the completion conditions, does the work, and gets independent verification from a single evaluator, revising until it passes (the verdict is read from the eval file). Fans out to explorer/general subagents for large tasks. |
| `evaluator` | Independently verifies a task's completion conditions in an isolated context. Distrusts the caller's claims; judges PASS/FAIL against the on-disk source of truth and direct inspection. Writes the report first (PENDING) and updates it, so an attempt survives even if the agent dies. |
| `auditor` | Runs global regression, checklist re-validation, and document tidying (cost trend, moving what does not belong in the every-iteration read set, retiring unfounded operating notes) at periodic checkpoints. Writes details to audit/ and returns only a concise delta to the driver. |
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
