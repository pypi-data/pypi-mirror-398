## Project Plan: DeepAgent Terminal Workspace Runner

### 1. Goal & Scope

**Goal**: Build a cross‑platform terminal application that lets the user pick a *workspace directory* and then run a DeepAgent that can:
- **Inspect and modify code** (read, write, edit files inside the workspace)
- **Fix bugs** (edit existing files, create new ones, run tests)
- **Execute shell commands** inside the workspace on:
  - **Linux / macOS** (POSIX shells like `bash`, `zsh`, etc.)
  - **Windows** (PowerShell / `cmd.exe`)

**Out of scope (for v1)**:
- GUI / TUI (we focus on CLI first)
- Multi‑project orchestration
- Remote execution over SSH

### 2. High‑Level Architecture

- **CLI entrypoint**: `deepagent-runner` (or `python -m deepagent_runner`)
- **Core modules**:
  - `config`: parse CLI args / env, detect OS, resolve workspace path
  - `backend`: filesystem + sandboxed execution backend, rooted at the selected workspace
  - `agent`: DeepAgent creation and configuration (tools, middleware, system prompt)
  - `shell_exec`: OS‑specific command execution helpers
  - `session`: conversation loop (streaming or turn‑based)
- Uses **DeepAgents** as the agent harness (planning, filesystem tools, subagents).
- Uses **LangGraph / LangChain** under the hood via DeepAgents.

### 3. Functional Requirements

- **FR1 – Workspace selection**
  - CLI flag `--workspace /path/to/project`
  - If not provided, prompt the user to:
    - use the **current directory**, or
    - input a path manually.
  - Validate that the path exists and is a directory.

- **FR2 – Sandboxed filesystem tools**
  - Use `FilesystemBackend` or `CompositeBackend` with `root_dir=<workspace>`.
  - Agent must only be able to:
    - `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`
    - **within** the workspace directory.
  - Prevent directory traversal outside workspace (`..`, symlinks, absolute paths).

- **FR3 – Cross‑platform command execution**
  - Provide an `execute` tool that:
    - Accepts a command string and optional timeout.
    - **Default execution environment is a Linux‑style shell**:
      - When a POSIX shell (e.g. `/bin/bash`) is available, always prefer it.
      - **Only when a POSIX shell is not available** (e.g. native Windows environment) fall back to a Windows shell.
    - On **Linux/macOS**: runs via `/bin/bash -lc` (or configurable POSIX shell).
    - On **Windows**: runs via `powershell.exe -Command` (default) or `cmd.exe /C` as a fallback.
    - Executes with `cwd = workspace`.
    - Captures `stdout`, `stderr`, `exit_code`.
  - Enforce safety limits: max output size, max runtime, and simple command length checks.

- **FR4 – DeepAgent configuration**
  - Configure `create_deep_agent` with:
    - Custom **system prompt**: “You are a coding assistant working **only** inside the selected workspace…”
    - Tools:
      - Filesystem tools from DeepAgents.
      - Custom `execute` tool for shell commands.
    - Optional: `interrupt_on` for sensitive operations (e.g., dangerous shell commands).
  - Support configurable model (e.g., `--model` CLI flag).

- **FR5 – Interactive session**
  - Start an interactive REPL:
    - User types natural‑language instructions.
    - Agent plans, calls tools (filesystem, execute), and responds.
  - Basic commands in the REPL:
    - `/exit` – terminate session.
    - `/workspace` – show current workspace path.
    - `/config` – show current model + options.

- **FR6 – Logging**
  - Optional `--log-file` and `--verbose` for debugging.
  - Log:
    - Shell commands executed.
    - Files written/edited (paths only, not full contents by default).

### 4. Non‑Functional Requirements

- **NFR1 – Cross‑platform**
  - Implement `shell_exec` with **explicit OS detection**:
    - Use `platform.system()` or similar.
    - **Prioritize a Linux‑style / POSIX shell** when available:
      - Try to use `/bin/bash` (or another configured POSIX shell) even when running in containerized or WSL contexts on Windows.
      - If no POSIX shell is available, fall back to the native Windows shell (PowerShell, then optionally `cmd.exe`).
    - Abstract differences in shell invocation and quoting.

- **NFR2 – Security / Safety**
  - Hard sandbox to workspace root.
  - Reject obviously dangerous commands if needed (e.g., configurable deny‑list).
  - Timeouts and output size limits for `execute`.

- **NFR3 – UX**
  - Clear, colorful CLI messages (e.g., using `rich`) but **no GUI**.
  - Helpful error explanations (invalid workspace, missing env vars, etc.).

- **NFR4 – Extensibility**
  - Easy to plug in:
    - different models,
    - more tools (e.g. HTTP, DB),
    - custom system prompts per project.

### 5. Technical Design

#### 5.1. Tech Stack

- **Language**: Python 3.11+
- **Core deps**:
  - `deepagents` – core agent harness (planning, filesystem, subagents)
  - `langgraph`, `langchain` – used transitively via DeepAgents
  - `typer` (preferred) or `click` for CLI
  - `rich` for pretty terminal output and structured logs (optional but recommended)

#### 5.2. CLI Interface

- Command: `deepagent-runner`
- Example usage:
  - `deepagent-runner --workspace /path/to/project`
  - `deepagent-runner --workspace . --model openai:gpt-4o`
  - `deepagent-runner --workspace . --log-file agent.log --verbose`

- CLI options (initial):
  - `--workspace TEXT` (required or interactive prompt)
  - `--model TEXT` (default from env or built‑in default)
    - default from `OPENAI_MODEL` env var or a hardcoded fallback (e.g. `openai:gpt-4o`)
  - `--max-runtime INT` (per command execution)
  - `--log-file PATH` (optional)
  - `--verbose / -v` (bool)

#### 5.3. Backend & Execution

- Implement a **custom backend** based on `FilesystemBackend`:
  - `root_dir = workspace`
  - Disallow paths outside root.
- Implement an `execute` tool that:
  - Preferred path (Linux‑style shell):
    - When a POSIX shell is present (typically `/bin/bash`): 
      - `subprocess.run(["/bin/bash", "-lc", command], cwd=workspace, ...)`
  - Fallback path (native Windows shell):
    - If no POSIX shell is detected/usable:
      - Prefer `powershell.exe -Command <command>`; fallback to `cmd.exe /C`.
  - Return structured result dict with:
    - `command`, `exit_code`, `stdout`, `stderr`, `duration_ms`.

#### 5.4. DeepAgent Setup

- Create helper `build_agent(workspace: Path, model_id: str, log_config: ...)`.
- Configure:
  - `backend=FilesystemBackend(root_dir=workspace)` or `CompositeBackend` if we want `/memories/`.
  - `tools`:
    - `execute` (custom).
    - All filesystem tools from DeepAgents.
  - `system_prompt` outlining:
    - Only touch files within workspace.
    - Use `write_todos` for multi‑step tasks.
    - Prefer running tests / linters via `execute` when modifying code.

#### 5.5. AI / Agent Stack & Models

- Use `deepagents.create_deep_agent` as the main factory:
  - Attach default middleware: `TodoListMiddleware`, `FilesystemMiddleware`, `SubAgentMiddleware`, summarization, Anthropic prompt caching (where relevant), HITL.
  - Provide custom tools list including:
    - `execute` (shell command runner).
    - Optional `internet_search` (via `tavily-python`) for web research.
- Model selection:
  - Primary: OpenAI models via `langchain`'s `init_chat_model`, e.g. `init_chat_model("openai:gpt-4o")`.
  - Configure via env:
    - `OPENAI_API_KEY` (required).
    - `OPENAI_MODEL` (optional, default `openai:gpt-4o`).
  - Keep room for future Anthropic models (e.g. `claude-sonnet-4-5-20250929`) as alternates.

#### 5.6. Human‑in‑the‑loop (HITL)

- Use LangGraph interrupts via DeepAgents `interrupt_on` configuration.
- Require a checkpointer (e.g. `MemorySaver`) so the agent can pause and resume.
- For v1, enable HITL for **sensitive tools**:
  - `write_file` – creating/overwriting files.
  - `edit_file` – modifying existing files.
  - `execute` – running shell / bash / PowerShell commands.
- Terminal app responsibilities:
  - When an interrupt occurs, show:
    - Tool name.
    - Arguments (e.g. file path, command string).
    - Allowed decisions (`approve`, `edit`, `reject`).
  - Allow user to:
    - Approve (run as‑is).
    - Edit arguments (e.g. adjust command or path).
    - Reject (skip this tool call).

#### 5.7. Configuration & Secrets

- Config management:
  - Read minimal configuration from environment and CLI flags.
  - Optional: use `pydantic-settings` later if config grows.
- Environment variables:
  - `OPENAI_API_KEY` – required.
  - `OPENAI_MODEL` – optional model identifier.
  - `TAVILY_API_KEY` – optional, if `internet_search` is enabled.
- Rules:
  - Never log raw API keys.
  - In dev, allow `.env` + `python-dotenv`; in prod, rely on environment.

#### 5.8. Tooling, Quality & Testing

- Dependency & project layout:
  - Use `pyproject.toml` with `uv` or `poetry`, or minimal `requirements.txt` if simpler.
  - Source layout: `src/deepagent_runner/`.
- Code quality:
  - Formatting: `black`.
  - Linting: `ruff` (can also handle import sorting instead of `isort`).
  - Optional type checking: `mypy` or `pyright`.
- Testing:
  - Use `pytest`.
  - High‑value tests:
    - Workspace selection & validation (correctly rejects invalid paths).
    - Sandbox behavior (no writes outside workspace, symlink handling).
    - Cross‑platform `shell_exec` wrapper on POSIX and Windows (CI matrix).
    - DeepAgent integration tests with a temporary workspace (create/edit files, run a simple command like `echo` or `pytest -q` against dummy tests).

### 6. Implementation Milestones

- **Milestone 1 – Skeleton**
  - Set up project structure (`src/deepagent_runner`, `pyproject.toml` or `setup.cfg`).
  - Basic CLI with `--workspace` and OS detection.

- **Milestone 2 – Filesystem sandbox**
  - Integrate DeepAgents with `FilesystemBackend` rooted at workspace.
  - Verify `ls`, `read_file`, `write_file`, `edit_file` work only inside workspace.

- **Milestone 3 – Cross‑platform `execute`**
  - Implement and test `execute` tool on Linux and Windows.
  - Add timeout and output truncation.

- **Milestone 4 – Agent wiring**
  - Implement `build_agent(...)`.
  - Add custom system prompt and model selection.

- **Milestone 5 – Interactive REPL**
  - Implement conversational loop.
  - Add `/exit`, `/workspace`, `/config` commands.

- **Milestone 6 – Hardening & DX**
  - Improve errors, logging, colored output.
  - Add minimal README and examples.
  - Add basic tests for CLI and shell execution.
  - Wire HITL flows in the terminal UI (approve/edit/reject).

### 7. Open Questions / Decisions

- Which default model identifier to ship with (Anthropic vs OpenAI)?
- Default shell on Windows: PowerShell only, or support switching between PowerShell and `cmd.exe`?
- Whether to add optional **human‑in‑the‑loop** interrupts for:
  - destructive shell commands,
  - mass file edits.


