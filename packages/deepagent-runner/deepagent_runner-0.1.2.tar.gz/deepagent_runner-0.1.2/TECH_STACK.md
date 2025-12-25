## Tech Stack Overview

This project builds a **terminal application** that lets the user:

- Choose a **working directory** for a project
- Give that directory to a **Deep Agent** which can:
  - Write new code
  - Edit / refactor existing code
  - Fix bugs
  - Execute shell commands inside that working directory

The app must support **Linux** and **Windows** environments.

---

## Core Language & Runtime

- **Language**: **Python 3.11+**
  - Strong ecosystem around LangChain / LangGraph / DeepAgents
  - Good cross‑platform support (Linux & Windows)
- **Package manager**: `uv` or `pip` (with `virtualenv`)
  - Recommended: `uv` for reproducible and fast installs

---

## AI / Agent Stack

- **Deep Agents**
  - Library: `deepagents`
  - Used to create the **DeepAgent** that can:
    - Plan work using its internal todo system
    - Read/write/edit files inside the selected working directory
    - Spawn subagents for complex tasks (optional)
    - Run shell commands via its `execute` / shell-related tools
- **Agent framework base**
  - Library: `langgraph` (used indirectly via `deepagents`)
  - Reason: provides the stateful graph execution and memory model
- **LLM client / model layer**
  - Library: `langchain` (and `langchain-community` if needed)
  - Primary provider: **OpenAI**
    - Models: `gpt-4.1`, `gpt-4o` (or newer compatible OpenAI chat models)
    - Initialization via `init_chat_model("openai:gpt-4o")` (or configurable string)
  - Optional secondary providers (future):
    - `anthropic` (e.g. `claude-sonnet-4-5-20250929`)
  - Model choice is controlled by configuration / environment variables:
    - `OPENAI_API_KEY` (required)
    - Optional `OPENAI_MODEL` (default: `gpt-4o`)
- **Optional web research**
  - Library: `tavily-python`
  - Use: provide an `internet_search` tool when the agent needs external sources:

    ```python
    from tavily import TavilyClient
    from deepagents import create_deep_agent
    import os

    tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    def internet_search(query: str, max_results: int = 5):
        """Run a web search using Tavily."""
        return tavily_client.search(query, max_results=max_results)

    agent = create_deep_agent(
        tools=[internet_search],
        # model is an OpenAI LLM, configured via env:
        # OPENAI_API_KEY, optional OPENAI_MODEL
    )
    ```

---

## Terminal Application Layer

- **CLI / UX Framework**
  - Option A (default): `typer`
    - Simple, modern CLI with good help messages and subcommands
  - Option B (for richer TUI, if needed later): `textual` or `rich` TUI
    - For interactive directory picker, live logs, etc.
- **Terminal Output Styling**
  - Library: `rich`
  - Use: colored logs, nicely formatted panels for:
    - Current working directory
    - Agent status / steps
    - Shell command outputs

---

## Filesystem & Execution

- **Filesystem operations**
  - Use Python stdlib: `pathlib`, `os`, `shutil`
  - Working directory selection:
    - Accept absolute path argument
    - Or interactively prompt the user
    - Validate existence, permissions, and safety (no traversal outside root when sandboxing)
  - Integrate with DeepAgents filesystem backend so the agent:
    - Reads / writes code within the chosen path
    - Uses `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep` tools

- **Shell command execution (Linux & Windows)**
  - Library: Python `subprocess`
  - Strategy:
    - Detect OS via `platform.system()`
    - On **Linux / macOS**:
      - Default to `/bin/bash` or system shell for `execute` commands
    - On **Windows**:
      - Default to `powershell` for better scripting support
    - Ensure:
      - All commands run inside the **selected working directory**
      - Capture stdout, stderr, and exit codes
      - Stream or page long outputs in the terminal UI
  - Integrate with DeepAgents `execute` / sandbox backend so the agent can safely run commands.

---

## Human-in-the-loop (HITL) for Sensitive Operations

All **destructive or high‑impact operations** must go through **Human-in-the-loop (HITL)** before execution:

- Operations requiring approval:
  - Creating / overwriting files (`write_file`)
  - Editing files (`edit_file`)
  - Running shell commands (`execute` / shell tools)
- Implementation:
  - Use LangGraph **interrupts** via `interrupt_on` when creating the DeepAgent.
  - Require a **checkpointer** (e.g. `MemorySaver`) so the agent can pause and resume.

Example (Python, concept-level):

```python
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

agent = create_deep_agent(
    tools=[internet_search],
    # LLM config: OpenAI (see LLM section)
    interrupt_on={
        # File creation / overwrite
        "write_file": {"allowed_decisions": ["approve", "edit", "reject"]},
        # Editing existing files
        "edit_file": {"allowed_decisions": ["approve", "edit", "reject"]},
        # Shell / bash / PowerShell execution
        "execute": {"allowed_decisions": ["approve", "edit", "reject"]},
    },
    checkpointer=checkpointer,
)
```

The terminal application will:

- Surface pending actions (tool name + args) to the user
- Let the user **approve**, **edit arguments**, or **reject** each operation
- Only then resume agent execution with the selected decisions.

---

## Configuration & Secrets

- **Config management**
  - Library: `pydantic-settings` or `dynaconf` (optional but recommended)
  - Use:
    - Model provider keys (e.g. `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`)
    - Default model choice
    - Optional limits (max steps, max tokens, timeout per command)
- **Secrets**
  - Load from environment variables (e.g. `.env` + `python-dotenv` in dev)
  - Never commit real keys to the repo

---

## Tooling & Quality

- **Dependency management**
  - `pyproject.toml` with `uv` or `poetry`, or a minimal `requirements.txt`
- **Formatting & Linting**
  - `black` – code formatting
  - `ruff` – linting (and simple fixes)
  - `isort` – import sorting (or use `ruff`’s built‑in support)
- **Testing**
  - `pytest`
  - Focus tests:
    - Directory selection & validation
    - Cross‑platform shell execution wrapper
    - Integration tests for DeepAgent working against a temp project dir
- **Type checking**
  - `mypy` or `pyright` (optional but recommended)

---

## Future Extensions

- Add a **skills layer** (predefined tasks) on top of the DeepAgent:
  - “Initialize a new Python project”
  - “Add unit tests for failing module”
  - “Refactor module X for readability”
- Add **session persistence**:
  - Remember previous working directories
  - Store long‑term notes via DeepAgents `/memories/` backend
- Add **remote / container targets**:
  - Instead of only local paths, support SSH or containerized environments (e.g. Docker) as working directories.


