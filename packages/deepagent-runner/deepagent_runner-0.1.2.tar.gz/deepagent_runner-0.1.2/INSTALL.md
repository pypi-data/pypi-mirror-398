# Installation Guide

## Quick Start

### Option 1: Using uv (Recommended - Fast)

```bash
# Install uv if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

# Install deepagents first (required dependency)
uv add deepagents

# Then install other dependencies
uv pip install -r requirements.txt
```

### Option 2: Using pip

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Editable Install

```bash
# After activating venv
# First install deepagents (required dependency)
uv add deepagents  # or: pip install deepagents

# Then install the package in editable mode
pip install -e .
```

## Configuration

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=openai:gpt-4o  # Optional

# Optional: for web research
TAVILY_API_KEY=your-tavily-key-here
```

## Verify Installation

Run the system check:

```bash
# Make sure virtual environment is activated first!
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

# If installed with pip install -e .
deepagent-runner check

# Or run directly without activating venv
PYTHONPATH=src python3 -m deepagent_runner.cli check
```

You should see:
- System information (OS, available shells)
- API key status

## Troubleshooting

### Command not found: deepagent-runner

If you get `zsh: command not found: deepagent-runner`:

**Solution:** Activate your virtual environment first:

```bash
# On Linux/macOS
source .venv/bin/activate

# On Windows
.venv\Scripts\activate

# Then run the command
deepagent-runner check
```

**Alternative:** Run directly without activating venv:
```bash
PYTHONPATH=src python3 -m deepagent_runner.cli check
```

### Missing deepagents package

If you get `ModuleNotFoundError: No module named 'deepagents'`:

**Using uv (recommended):**
```bash
uv add deepagents
```

**Using pip:**
```bash
pip install deepagents
```

### ModuleNotFoundError

If you get `ModuleNotFoundError`, make sure:
1. Virtual environment is activated
2. `deepagents` is installed: `uv add deepagents` or `pip install deepagents`
3. Other dependencies are installed: `pip install -r requirements.txt`
4. Or set PYTHONPATH: `PYTHONPATH=src python3 -m deepagent_runner.cli`

### Missing API Keys

If you get "Missing required environment variables":
1. Create `.env` file from `.env.example`
2. Add your `OPENAI_API_KEY`
3. Make sure you're in the project root directory

### Shell Not Found

On Windows, if you prefer bash:
1. Install Git Bash or WSL2
2. Make sure `bash` is in your PATH
3. The tool will auto-detect and prefer POSIX shells

