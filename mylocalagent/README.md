# Local Agent with Strands + Ollama + Azure DevOps MCP

Local DevOps/Platform Engineering chat agent built with the [Strands Agents SDK](https://strandsagents.com/docs/user-guide/sdk/quickstart/python/), a local **Ollama** model, and the official [Azure DevOps MCP server](https://github.com/microsoft/azure-devops-mcp) connected as real tools.

## What it does

- Runs an interactive chat loop in the terminal (`Tú: ...`) that keeps conversation context between turns.
- Uses **Ollama** (`qwen3.8:latest` by default) as the local LLM backend, falling back to Bedrock (Strands' default provider) if Ollama isn't reachable.
- Connects to the real **Azure DevOps MCP server** as agent tools (work items, projects, repos, pipelines, wikis, test plans, Advanced Security alerts, etc.), so the agent calls actual Azure DevOps APIs instead of guessing/hand-writing `curl`/`az` commands.
- The Azure DevOps MCP server is installed **inside this project** (via `npm`, see [package.json](./package.json)) — no external clone or global install required.
- Centralizes operating rules/defaults (organization, project, sprint logic, etc.) in [system_instructions.py](./system_instructions.py).

## Project structure

- `agent.py`: chat agent entry point (Ollama model + Azure DevOps MCP client wiring)
- `system_instructions.py`: consolidated operating instructions and ADO defaults
- `requirements.txt`: Python dependencies
- `package.json`: pins the `@azure-devops/mcp` npm package used by `agent.py`
- `setup_venv.sh`: creates the Python venv, installs Python deps, and installs the Azure DevOps MCP server via `npm`
- `run_agent.sh`: activates the venv and runs `agent.py`
- `integrations/azure_devops.py`, `explore_mcp_paths.py`: earlier exploratory REST/MCP helpers, not used by the current `agent.py` flow

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally, with the model pulled:
  ```bash
  ollama pull qwen3.8:latest
  ```
- **Node.js + npm** (any reasonably recent LTS) — only needed to run the Azure DevOps MCP server. If missing, the agent still runs, just without Azure DevOps tools.
- An Azure DevOps **Personal Access Token (PAT)** to use the Azure DevOps tools.

## Setup

```bash
./setup_venv.sh
```

This creates `venv/`, installs the Python dependencies from `requirements.txt`, and — if `npm` is available — runs `npm install` to fetch the Azure DevOps MCP server into `node_modules/` (both `venv/` and `node_modules/` are git-ignored).

## Required environment variables

Set these **before** running the agent so it can connect to Azure DevOps:

| Variable | Description |
|---|---|
| `ADO_ORG` | Azure DevOps organization name (e.g. `ATHINA-HADEA`). Passed directly to the MCP server. |
| `AZURE_DEVOPS_EXT_PAT` | Personal Access Token used to authenticate with Azure DevOps (same env var name used by the `az devops` CLI extension). Needs at least read access to Work Items/Projects; add write scopes if you want the agent to create/update items. |

Example (bash):

```bash
export ADO_ORG="ATHINA-HADEA"
export AZURE_DEVOPS_EXT_PAT="your-pat-here"
```

If either variable is missing, `agent.py` prints a warning and starts **without** Azure DevOps tools instead of failing.

### Optional override

| Variable | Description |
|---|---|
| `ADO_MCP_SERVER_PATH` | Absolute path to the Azure DevOps MCP server's `dist/index.js`, if you want to point to a different install instead of this project's `node_modules/`. |

## Run

```bash
./run_agent.sh
```

or, with the venv activated:

```bash
python agent.py
```

Type your messages at the `Tú:` prompt; the agent streams its response and remembers the conversation. Type `salir`, `exit`, or `quit` (or `Ctrl+C`) to stop, or `reiniciar`/`reset` to clear the conversation history without restarting the process.

## Notes on local model + tool context

Ollama's default context window (`num_ctx`) is 4096 tokens, but the Azure DevOps MCP server exposes ~70 tools whose definitions alone take up roughly 20k tokens. `agent.py`:

- limits the connected tools to a curated subset (`ADO_MCP_ALLOWED_TOOLS` in `agent.py`: work items, projects/teams, sprints, and read-only repos/pipelines) to keep that fixed per-request overhead down (~7k tokens instead of ~20k), and
- sets `num_ctx=32768` and a lower `temperature=0.3` on the Ollama model, so more context is actually available for multi-step tool-calling conversations and the model is less likely to go on long speculative tool-call chains.

Even so, a long back-and-forth (many tool calls in one conversation) can still exceed the context window. When that happens, Ollama truncates the oldest messages and the model may reply with an error instead of text (`ollama._types.ResponseError: no user query found in messages`). `agent.py` catches this per-turn instead of crashing the whole REPL — type `reiniciar` to clear the conversation history and keep going. If you add many more MCP servers/tools, you may need to raise `num_ctx` further — watch your GPU/RAM headroom (`ollama ps` shows live `context_length` and `size_vram`).

## Built-in defaults and business rules

Embedded by default in `system_instructions.py` (override by asking explicitly):

- organization: `ATHINA-HADEA`
- project: `ATHINA LOT1`
- team: `DevSecOps`
- area path: `ATHINA LOT1\DevSecOps`
- assigned to: `durbanod@emeal.nttdata.com`
- repository: `athina-core-infrastructure`

Also included:

- dynamic sprint calculation based on a Sprint 29 anchor and a 15-day cadence
- mandatory validation for `story_points` on User Stories, and `original_estimate`/`remaining_work`/`completed_work` on Tasks assigned to Daniel
- a rule telling the model to always prefer the connected Azure DevOps MCP tools over hand-written `curl`/`az`/PAT-based scripts
