# Local Agent with Strands + Ollama

Base local agent built in Python using the Strands Agents SDK and Ollama.

## Objective

This project provides the initial core for a local agent that:

- uses **Ollama** as the LLM backend
- runs with model **`qwen3.8:latest`**
- is designed to grow with **Azure DevOps / Azure** tools
- centralizes custom operating instructions in a base system prompt
- includes a first real Azure DevOps integration layer using the installed **`azure-devops-mcp`** package client

## Current structure

- `requirements.txt`: Python dependencies
- `agent.py`: initial local agent implementation
- `system_instructions.py`: consolidated operating instructions and defaults

## Requirements

- Python 3.10+
- Ollama installed and running locally
- Model available locally in Ollama:
  - `qwen3.8:latest`
- Azure DevOps Personal Access Token (PAT) for real Azure DevOps operations

## Install

```bash
pip install -r requirements.txt
```

## Prepare Ollama

Make sure Ollama is installed and the model is available:

```bash
ollama pull qwen3.8:latest
```

## Azure DevOps configuration

The current implementation uses the Python client included in `azure-devops-mcp`.

Set these environment variables before running the agent:

### Required for Azure DevOps actions

```powershell
$env:AZURE_DEVOPS_PAT="your-pat"
```

### Optional overrides

If not provided, these defaults are already embedded in the agent:

- `AZURE_DEVOPS_ORG_URL=https://dev.azure.com/ATHINA-HADEA`
- `AZURE_DEVOPS_PROJECT=ATHINA LOT1`
- `AZURE_DEVOPS_API_VERSION=7.1`

Optional PowerShell example:

```powershell
$env:AZURE_DEVOPS_ORG_URL="https://dev.azure.com/ATHINA-HADEA"
$env:AZURE_DEVOPS_PROJECT="ATHINA LOT1"
$env:AZURE_DEVOPS_API_VERSION="7.1"
```

## Run

```bash
python agent.py
```

Then type messages in the terminal. To exit:

```text
exit
```

## Current Azure DevOps tool commands

The Azure DevOps tool in this first core supports these direct command patterns:

### List projects

```text
get_projects
```

### Get a work item by ID

```text
get_work_item 12345
```

### Search work items by text

```text
search_work_items terraform backend
```

### Get available work item types

```text
get_work_item_types
```

### Create a task

```text
create_task title=Preparar pipeline; description=Crear task inicial; original_estimate=4; remaining_work=4; completed_work=0
```

### Create a user story

```text
create_user_story title=Automatizar despliegue; description=Story base; story_points=5
```

## Built-in defaults and business rules

This first version already applies your main defaults:

- organization: `ATHINA-HADEA`
- project: `ATHINA LOT1`
- team: `DevSecOps`
- area path: `ATHINA LOT1\DevSecOps`
- assigned to: `durbanod@emeal.nttdata.com`
- repository: `athina-core-infrastructure`

It also includes:

- dynamic sprint calculation based on Sprint 29 anchor and 15-day cadence
- mandatory validation for:
  - `story_points` on User Stories assigned to Daniel
  - `original_estimate`, `remaining_work`, `completed_work` on Tasks assigned to Daniel

## Current status

Implemented in this version:

- base Python project
- Strands-based agent bootstrap
- Ollama model configuration
- consolidated system instructions
- real Azure DevOps integration through `AzureDevOpsClient` from `azure-devops-mcp`
- default ADO business rules and sprint logic embedded in the tool

## Important implementation note

Even though the package is named `azure-devops-mcp`, the current agent integration does **not** yet launch or attach to the MCP server process itself.

For this iteration, the safest and cleanest approach was:

- install `azure-devops-mcp`
- reuse its bundled `AzureDevOpsClient`
- integrate real Azure DevOps calls directly inside the local tool

This gives you a working core now, while keeping the door open to evolve later into a full MCP-process-based architecture if needed.

## Planned next steps

Next iterations should include:

1. validate Strands SDK exact tool-calling behavior with richer natural language routing
2. replace command-style ADO usage with structured tool invocation and intent parsing
3. add update work item support
4. add comments support
5. add pipeline/runs/logs support
6. add `.env` file support for local configuration
7. optionally run the official Azure DevOps MCP server as a separate process and connect through MCP transport instead of direct client usage
8. add Azure CLI integration through WSL where applicable
9. modularize tool registry and configuration layers

## Notes

This is the initial core only. The Azure DevOps integration is now real for basic scenarios, but still intentionally narrow and conservative so we can evolve it safely in following iterations.
