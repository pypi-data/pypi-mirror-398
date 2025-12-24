# CA Scaffold Python - MCP & Agent Generator

A CLI tool and Scaffolder to generate Python projects based on Clean Architecture. It specializes in creating MCP (Model Context Protocol) Servers and Pro-code Agents with built-in support for LangGraph, Kafka, and A2A (Agent-to-Agent) communication.

## Key Features

* **Clean Architecture:** Generates projects with separation of concerns (Domain, Use Cases, Infrastructure, Adapters).
* **Dual Project Types:**
    * **MCP Server:** Standard server implementing tools, resources, and prompts.
    * **Agent Pro-code:** Orchestrator agent using LangGraph and A2A protocol.
* **Dynamic Injection:** Add new Tools, Prompts, or Resources to existing projects without breaking the structure.
* **Safety:** Includes a backup and restore mechanism before modifying existing code.
* **Backstage Ready:** Designed to work as the backend for Backstage Software Templates.

## Prerequisites

* Python 3.12+
* `uv` installed (recommended for dependency management)

## Installation

1.  **Clone the repository:**
    ```sh
    git clone <your-repo-url>
    cd ca-scaffold-py
    ```

2.  **Install dependencies using `uv`:**
    ```sh
    uv sync
    ```

3.  **Build and Install the CLI:**
    ```sh
    uv run python -m build
    uv pip install dist/ca_scaffold_py-1.0.0-py3-none-any.whl
    ```

    *Alternatively, for local development run commands using `uv run scaffold-py ...`*

## CLI Usage

The generator exposes a CLI named `scaffold-py` (or configured as `mcp-generator`).

### 1. Create a New Project

You can create two types of projects: `mcp_server` (default) or `agent_procode`.

#### Interactive Mode (Recommended)
The easiest way to start. It guides you through the configuration.
```sh
scaffold-py interactive
````

#### Direct Creation (MCP Server)

Creates a project with Tools, Prompts, and Resources. Note: MCP Server names must end with `_smcp`.

```sh
scaffold-py create "my_project_smcp" \
  --type mcp_server \
  --tool "calculate_tax|Calculate taxes|amount: float, rate: float = 0.19|float" \
  --resource "get_logs|logs://{date}|Get system logs|date: str|str"
```

#### Direct Creation (Agent Pro-code)

Creates an agent capable of connecting to other MCP servers.

```sh
scaffold-py create "my_orchestrator_agent" \
  --type agent_procode \
  --mcp-connections "sales_mcp|http://sales-mcp:8000" \
  --mcp-connections "inventory_mcp|http://inventory-mcp:8000"
```

### 2\. Add Components to Existing Projects

Navigate to the root of a generated project and inject new components dynamically. The tool automatically updates `container.py`, `settings.py`, and entry points.

```sh
cd my_project_smcp

# Add a new tool
scaffold-py add --tool "send_email|Sends an email|to: str, subject: str|bool"

# Add a new prompt
scaffold-py add --prompt "summarize_text|Summarizes long text inputs"
```

### 3\. Backup & Restore

The tool creates automatic backups in `.mcp_backups/` before injecting code.

**List available backups:**

```sh
scaffold-py restore-backup
```

**Restore a specific backup:**

```sh
scaffold-py restore-backup backup_20231027_100000
```

-----

## Project Types

### MCP Server (`mcp_server`)

Implements the Model Context Protocol.

  * **Infrastructure:** FastMCP.
  * **Components:** Tools, Prompts, Resources.
  * **Use Cases:** Automates business logic exposed via MCP.

### Agent Pro-code (`agent_procode`)

An intelligent agent template.

  * **Core:** LangGraph for orchestration.
  * **Communication:**
      * **MCP Client:** Consumes other MCP servers.
      * **A2A (Agent-to-Agent):** Google's protocol for inter-agent communication.
      * **Kafka:** Asynchronous event-driven communication (Optional).

## Component Definition Format

When using the CLI, components are defined using pipe-separated strings:

| Component | Format | Example |
| :--- | :--- | :--- |
| **Tool** | `name|desc|params|return` | `sum|Sum values|a:int, b:int|int` |
| **Prompt** | `name|desc` | `code_review|Review python code` |
| **Resource**| `name|uri|desc|params|return` | `get_user|user://{id}|Get User|id:str|dict` |
| **Connection**| `name|endpoint` | `users_mcp|http://localhost:8080` |

-----

## Testing

1.  Install development dependencies: `uv sync --dev`
2.  Run tests: `uv run pytest`