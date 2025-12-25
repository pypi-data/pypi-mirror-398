# DeepAgent Runner 🤖

A cross-platform terminal application that runs a DeepAgent in your workspace directory to help you write code, fix bugs, and execute shell commands.

## Features

- 🗂️ **Workspace Sandbox**: Agent operates only within your selected directory
- 🐚 **Cross-platform Shell Execution**: Prefers Linux-style shells (bash), falls back to PowerShell on Windows
- 🤖 **DeepAgent Integration**: Full planning, filesystem tools, and subagent capabilities
- 🎨 **Rich Terminal UI**: Colorful, intuitive command-line interface with Markdown rendering
- 🔒 **Human-in-the-loop**: Approve/edit/reject sensitive operations before execution
- 💬 **Interactive REPL**: Natural conversation with multi-turn context
- 💾 **Session Management**: Persistent sessions with metadata, resume across restarts, multiple concurrent sessions

## Prerequisites

- Python 3.11 or higher
- OpenAI API key

## Installation

### Quick Install (from PyPI - Recommended)

Nếu package đã được publish lên PyPI:

```bash
# 1. Cài đặt trực tiếp từ PyPI (không cần source code)
python3.11 install deepagent-runner

# Hoặc với uv (nhanh hơn)
uv pip install deepagent-runner

# Với optional dependencies (web research)
python3.11 install "deepagent-runner[tavily]"
```

**Bước tiếp theo:** Sau khi cài đặt, bạn cần:
1. Tạo file `.env` với API keys (xem phần [Configuration](#configuration))
2. Chạy `deepagent-runner check` để kiểm tra cấu hình
3. Bắt đầu sử dụng: `deepagent-runner --workspace /path/to/project`

### Install from Git Repository

Nếu chưa publish lên PyPI, có thể cài từ Git:

```bash
# Cài trực tiếp từ Git repo (không cần clone)
pip install git+https://github.com/yourusername/CodeAgent.git

# Hoặc với uv
uv pip install git+https://github.com/yourusername/CodeAgent.git
```

### Install from Source (Development)

Nếu muốn develop hoặc modify code:

```bash
# Clone repository
git clone <repository-url>
cd CodeAgent

# Create virtual environment
uv venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

# First install deepagents (required dependency)
uv add deepagents

# Then install the package in editable mode
uv pip install -e .

# Optional: Install tavily-python for web research (research-agent subagent)
uv pip install tavily-python
```

**Hoặc với pip:**

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

# Install deepagents first (required dependency)
pip install deepagents

# Then install the package
pip install -e .

# Optional: Install tavily-python for web research (research-agent subagent)
pip install tavily-python
```

### Development installation

```bash
# After activating venv
pip install -e ".[dev]"

# Or with tavily support
pip install -e ".[dev,tavily]"
```

**Note:** Always activate your virtual environment before running commands. See [INSTALL.md](INSTALL.md) for detailed installation instructions.

### Uninstall

Để gỡ bỏ package:

```bash
# Gỡ package
python3.11 -m pip uninstall deepagent-runner

# Hoặc với uv
uv pip uninstall deepagent-runner
```

Khi được hỏi xác nhận, nhấn `y` hoặc `Enter`.

**Kiểm tra đã gỡ chưa:**
```bash
# Kiểm tra package còn tồn tại không
python3.11 -m pip show deepagent-runner 

# Hoặc kiểm tra trong danh sách đã cài
python3.11 -m pip list | grep deepagent-runner
```

Nếu không thấy output, package đã được gỡ thành công.

**Lưu ý:**
- Gỡ package không xóa file `.env` hoặc các cấu hình khác
- Nếu cài trong virtual environment, bạn có thể đơn giản deactivate hoặc xóa venv
- Nếu cài global (không dùng venv), cần chạy `pip uninstall` với quyền phù hợp

## Configuration

Sau khi cài đặt từ PyPI, bạn cần tạo file `.env` để cấu hình API keys.

### Tạo file .env

**Cách 1: Tạo trong workspace directory (khuyến nghị)**

Khi bạn chạy `deepagent-runner --workspace /path/to/project`, tool sẽ tự động tìm file `.env` trong thư mục workspace:

```bash
# Tạo file .env trong workspace của bạn
cd /path/to/your/workspace
nano .env  # hoặc vim, code, etc.
```

**Cách 2: Tạo trong home directory**

Tool cũng sẽ tìm file `.env` trong home directory (`~/.env` hoặc `%USERPROFILE%\.env` trên Windows):

```bash
# Linux/macOS
nano ~/.env

# Windows
notepad %USERPROFILE%\.env
```

### Nội dung file .env

Tạo file `.env` với nội dung sau:

```env
# Required: OpenAI API key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Model to use (default: openai:gpt-4.1-mini)
OPENAI_MODEL=openai:gpt-4.1-mini

# Optional: For web research capabilities
TAVILY_API_KEY=your-tavily-key-here

# Optional: For image analysis (read_image tool)
VISION_MODEL=openai:gpt-4o-mini
```

### Lấy API Keys

- **OpenAI API Key**: Đăng ký tại https://platform.openai.com/api-keys
- **Tavily API Key** (optional): Đăng ký tại https://www.tavily.com/
- **Vision Model**: Sử dụng model có vision capability như `openai:gpt-4.1-mini` hoặc `openai:gpt-4o-mini`

### Kiểm tra cấu hình

Sau khi tạo file `.env`, kiểm tra cấu hình:

```bash
deepagent-runner check
```

Bạn sẽ thấy thông tin về API keys đã được cấu hình.

## Usage

**Important:** Make sure your virtual environment is activated before running commands:

```bash
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows
```

### Basic usage

Run in current directory:

```bash
deepagent-runner --workspace .
```

Specify workspace:

```bash
deepagent-runner --workspace /path/to/project
```

### Example Session

```
$ deepagent-runner --workspace my-project

Welcome to DeepAgent Runner! 🤖

You: List all Python files in src/

Agent: Found 5 Python files:
- src/main.py
- src/utils.py
...

You: Run the tests

⚠️ Agent wants to execute: pytest tests/
Decision (approve/edit/reject): approve

✓ All tests passed!

You: /exit
Goodbye! 👋
```

### REPL Commands

- `/help` - Show help and examples
- `/workspace` - Display workspace info
- `/config` - Show configuration (including session info)
- `/sessions` - List all saved sessions
- `/rename <name>` - Rename current session for easy identification
- `/clear` - Clear conversation history and create new session
- `/exit` - Exit session

### Advanced options

```bash
deepagent-runner \
  --workspace /path/to/project \
  --model openai:gpt-4.1-mini \
  --max-runtime 600 \
  --log-file agent.log \
  --verbose
```

For detailed examples and workflows, see [USAGE.md](USAGE.md).

### Session Management

DeepAgent Runner supports **persistent sessions** that save automatically. Each session maintains its own conversation history and metadata.

#### List All Sessions

```bash
# List all saved sessions
deepagent-runner sessions

# Filter by workspace
deepagent-runner sessions --workspace /path/to/project
```

#### Resume a Session

```bash
# Resume a specific session
deepagent-runner --session abc12345

# Or with workspace (if different from session's workspace)
deepagent-runner --workspace /path/to/project --session abc12345
```

#### Session Commands in REPL

While in a session, you can manage it:

```
You: /sessions

Sessions
ID          Name              Workspace    Messages    Last Used
abc123...   Current ←         my-project   5           2025-12-18 10:30
def456...   Bug Fix            my-project   12          2025-12-18 09:15

You: /rename Feature: User Profiles
✓ Session renamed to: Feature: User Profiles

You: /config

Configuration
  Model: openai:gpt-4.1-mini
  Session ID: abc123...
  Workspace: /path/to/project
  Message Count: 5
  Session Name: Feature: User Profiles
```

#### Session Storage

Sessions are stored at: `~/.deepagent/sessions/`

- **sessions.db** - Session metadata (name, workspace, model, timestamps)
- **checkpoints.db** - Conversation state (if using persistent checkpointer)

#### Example: Multiple Sessions

```bash
# Terminal 1: Frontend work
$ deepagent-runner --workspace frontend
You: /rename Frontend Work
You: Update the navbar component

# Terminal 2: Backend work (concurrent)
$ deepagent-runner --workspace backend
You: /rename Backend API
You: Add authentication endpoint

# Both sessions run independently!
```

For complete session management guide, see [SESSION_MANAGEMENT.md](SESSION_MANAGEMENT.md).

### Check system configuration

```bash
# Make sure venv is activated first!
deepagent-runner check
```

### Show version

```bash
# Make sure venv is activated first!
deepagent-runner version
```

**Troubleshooting:** If you get `command not found: deepagent-runner`, make sure:
1. Virtual environment is activated: `source .venv/bin/activate`
2. Package is installed: `pip install -e .` or `uv pip install -e .`

See [INSTALL.md](INSTALL.md) for more troubleshooting tips.

## CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--workspace` | `-w` | Path to workspace directory | Current directory (interactive) |
| `--model` | `-m` | Model identifier (e.g., `openai:gpt-4.1-mini`) | From `OPENAI_MODEL` or `openai:gpt-4.1-mini` |
| `--session` | `-s` | Resume an existing session by ID | None (creates new session) |
| `--max-runtime` | | Max command execution time (seconds) | 300 |
| `--log-file` | | Path to log file | None |
| `--verbose` | `-v` | Enable verbose output | False |

### Additional Commands

| Command | Description |
|---------|-------------|
| `deepagent-runner sessions` | List all saved sessions |
| `deepagent-runner sessions --workspace <path>` | Filter sessions by workspace |
| `deepagent-runner check` | Check system configuration and API keys |
| `deepagent-runner version` | Show version information |

## Documentation

- **[USAGE.md](USAGE.md)** - Complete usage guide with examples
- **[INSTALL.md](INSTALL.md)** - Installation instructions
- **[SESSION_MANAGEMENT.md](SESSION_MANAGEMENT.md)** - Complete guide to session management

## What Can the Agent Do?

**Code Analysis & Navigation**:
- List and search files
- Read and analyze code structure
- Find patterns, TODOs, bugs

**Code Modification**:
- Write new files
- Edit existing files (with approval)
- Refactor code
- Add documentation

**Testing & Execution**:
- Run test suites
- Execute build scripts
- Run linters and formatters
- Any shell command (with approval)

**Project Management**:
- Plan multi-step tasks
- Track progress with todos
- Delegate to subagents

All within the safety of workspace sandboxing! 🔒

## License

MIT

