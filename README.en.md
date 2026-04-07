```
██████╗ ██╗   ██╗██╗  ██╗ ██████╗     ███████╗████████╗ █████╗  ██████╗██╗  ██╗
██╔══██╗╚██╗ ██╔╝██║ ██╔╝██╔═══██╗    ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
██████╔╝ ╚████╔╝ █████╔╝ ██║   ██║    ███████╗   ██║   ███████║██║     █████╔╝ 
██╔══██╗  ╚██╔╝  ██╔═██╗ ██║   ██║    ╚════██║   ██║   ██╔══██║██║     ██╔═██╗ 
██████╔╝   ██║   ██║  ██╗╚██████╔╝    ███████║   ██║   ██║  ██║╚██████╗██║  ██╗
╚═════╝    ╚═╝   ╚═╝  ╚═╝ ╚═════╝     ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚══════╝╚═╝  ╚═╝
 :: byko-plugins ::                                                (Claude Code)
```

> A minimalist harness that runs on skills alone — no extra framework required.

> Korean version: [README.md](./README.md)

## Structure

```
byko-plugins/
├── .claude-plugin/
│   └── marketplace.json     # Marketplace metadata and plugin list
├── plugins/
│   └── byko-stack/          # A single plugin
│       └── skills/          # Skills bundled in the plugin
└── README.md
```

## Installation

### 1. Register the marketplace

Inside a Claude Code session, register this repository as a marketplace:

```
/plugin marketplace add <github-user>/byko-plugins
```

A local path also works:

```
/plugin marketplace add /path/to/byko-plugins
```

### 2. Install a plugin

Install any plugin from the registered marketplace:

```
/plugin install byko-stack@byko-plugins
```

After installation, run `/plugin` to verify it is active.

### 3. Update

Pull the latest changes from the upstream repository:

```
/plugin marketplace update byko-plugins
```

## Plugins

### byko-stack

A collection of skills for a spec-driven development (SDD) workflow.

| Skill | Role |
| --- | --- |
| `spec-designer` | Designs and writes implementation specs through a dialogue with the user. |
| `spec-dev` | Implements code based on a completed spec, or prepares a ralph-loop package for larger work. |
| `claude-eval` | Evaluates documents/code in an isolated context using `claude -p`. |
| `codex-eval` | Cross-validates artifacts from a different model's perspective via the OpenAI Codex CLI. |
| `eval-gate` | Orchestrates `claude-eval` and `codex-eval` as a quality gate for specs, plans, and implementations. |

#### Default workflow

```
/spec-designer             →  write the spec
/eval-gate spec            →  validate the spec
/spec-dev                  →  implement
/eval-gate implementation  →  validate the implementation
```

See each skill's `SKILL.md` for detailed usage.

## Adding a new plugin

To add another plugin to this marketplace:

1. Create a `plugins/<plugin-name>/` directory.
2. Place the required `skills/`, `commands/`, `agents/`, `hooks/`, etc. inside it.
3. Append an entry to the `plugins` array in `.claude-plugin/marketplace.json`:

```json
{
  "name": "<plugin-name>",
  "source": "./plugins/<plugin-name>"
}
```
