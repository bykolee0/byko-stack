```
██████╗ ██╗   ██╗██╗  ██╗ ██████╗     ███████╗████████╗ █████╗  ██████╗██╗  ██╗
██╔══██╗╚██╗ ██╔╝██║ ██╔╝██╔═══██╗    ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
██████╔╝ ╚████╔╝ █████╔╝ ██║   ██║    ███████╗   ██║   ███████║██║     █████╔╝ 
██╔══██╗  ╚██╔╝  ██╔═██╗ ██║   ██║    ╚════██║   ██║   ██╔══██║██║     ██╔═██╗ 
██████╔╝   ██║   ██║  ██╗╚██████╔╝    ███████║   ██║   ██║  ██║╚██████╗██║  ██╗
╚═════╝    ╚═╝   ╚═╝  ╚═╝ ╚═════╝     ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚══════╝╚═╝  ╚═╝
 :: byko-plugins ::                                          (Claude Code/Codex)
```

> A minimalist harness that runs on skills alone — no extra framework required.

> Korean version: [README.md](./README.md)

## Structure

```
byko-plugins/
├── .agents/
│   └── plugins/
│       └── marketplace.json # Codex marketplace metadata and plugin list
├── .claude-plugin/
│   └── marketplace.json     # Claude Code marketplace metadata and plugin list
├── plugins/
│   ├── byko-stack/          # Claude Code-oriented plugin
│   │   ├── .codex-plugin/   # Codex-compatible manifest
│   │   ├── .claude-plugin/  # Claude Code plugin manifest
│   │   └── skills/          # Skills bundled in the plugin
│   └── byko-stack-codex/    # Codex-native port
│       ├── .codex-plugin/
│       ├── shared/
│       └── skills/
└── README.md
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
- Skill directory: `plugins/byko-stack/skills/`
- Codex-native skill directory: `plugins/byko-stack-codex/skills/`

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
