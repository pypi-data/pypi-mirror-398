# Usage Guide - DeepAgent Runner

Complete guide with practical examples for using DeepAgent Runner.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [REPL Commands](#repl-commands)
- [Human-in-the-Loop](#human-in-the-loop)
- [Practical Examples](#practical-examples)
- [Tips & Best Practices](#tips--best-practices)
- [Troubleshooting](#troubleshooting)

## Installation

### 1. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using uv (faster, recommended)
# First install deepagents (required dependency)
uv add deepagents

# Then install other dependencies
uv pip install -r requirements.txt
```

### 2. Set Up API Keys

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your keys
nano .env
```

Required in `.env`:
```env
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=openai:gpt-4o  # Optional, defaults to gpt-4o
```

Optional:
```env
TAVILY_API_KEY=your-tavily-key  # For web search capabilities
```

### 3. Verify Installation

```bash
# Make sure virtual environment is activated first!
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

deepagent-runner check
```

You should see:
- ✓ System information
- ✓ API keys validated
- ✓ Shell detected

## Quick Start

```bash
# Start in current directory
deepagent-runner --workspace .

# Or specify a project
deepagent-runner --workspace /path/to/your/project
```

The agent will start and you can begin chatting!

## Basic Usage

### Starting the Agent

```bash
# Basic usage
deepagent-runner --workspace /path/to/project

# With options
deepagent-runner \
  --workspace /path/to/project \
  --model openai:gpt-4o \
  --verbose \
  --max-runtime 600
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--workspace`, `-w` | Workspace directory | Interactive prompt |
| `--model`, `-m` | Model identifier | `openai:gpt-4o` |
| `--max-runtime` | Command timeout (seconds) | 300 |
| `--verbose`, `-v` | Verbose output | False |
| `--log-file` | Log file path | None |

## REPL Commands

Once in the interactive session, you can use these commands:

### `/help`
Show help message with examples.

```
You: /help
[Shows: Commands list, example requests, tips]
```

### `/workspace`
Display current workspace information.

```
You: /workspace

Workspace Info:
  Workspace: /path/to/project
  Absolute path: /home/user/project
  Exists: True
  Is directory: True
```

### `/config`
Show agent configuration.

```
You: /config

Configuration:
  Model: openai:gpt-4o
  Session ID: abc123-...
  Workspace: /path/to/project
  Max Command Timeout: 300s
  Message Count: 5
  Verbose: False
```

### `/clear`
Clear conversation history and start fresh.

```
You: /clear
Clearing conversation history...
✓ Conversation cleared!
```

### `/exit` or `/quit`
Exit the session gracefully.

```
You: /exit
Exiting session. Goodbye! 👋
```

## Human-in-the-Loop

The agent asks for approval before performing sensitive operations:
- **Writing files** (`write_file`)
- **Editing files** (`edit_file`)
- **Executing commands** (`execute`)

### Example: File Write Approval

```
You: Create a README.md file

Agent thinking...

⚠️ Agent wants to perform sensitive operations

Action 1/1:
Tool: write_file
path: README.md
content: # My Project
...

Decision (approve/edit/reject): approve
✓ Approved

Agent: I've created the README.md file with the requested content.
```

### Approval Options

1. **Approve** - Execute as proposed
   ```
   Decision: approve  (or just 'a')
   ```

2. **Edit** - Modify arguments before execution
   ```
   Decision: edit  (or just 'e')
   
   Edit arguments (JSON format):
   Current: {'path': 'README.md', 'content': '...'}
     path [README.md]: docs/README.md
     content [...]: # Updated content
   
   ✓ Edited
   ```

3. **Reject** - Skip this operation
   ```
   Decision: reject  (or just 'r')
   ✗ Rejected
   ```

## Practical Examples

### Example 1: List Files

```
You: List all Python files in src/

Agent: I'll search for Python files in the src/ directory.

[Uses glob tool: src/**/*.py]

Found 5 Python files:
- src/main.py (245 lines)
- src/utils.py (120 lines)
- src/config.py (89 lines)
- src/models.py (310 lines)
- src/api.py (156 lines)
```

### Example 2: Run Tests

```
You: Run the tests

Agent: I'll execute pytest with verbose output.

⚠️ Agent wants to perform sensitive operations

Action 1/1:
Tool: execute
command: pytest tests/ -v
timeout: None

Decision: approve

[Executes command]

Command: pytest tests/ -v
Exit Code: 0
Duration: 1523ms

===== test session starts =====
tests/test_main.py::test_function PASSED
tests/test_utils.py::test_helper PASSED
===== 2 passed in 1.52s =====

All tests passed! ✓
```

### Example 3: Fix a Bug

```
You: Fix the division by zero bug in utils.py line 42

Agent: I'll examine the issue and fix it.

[Reads utils.py]

I found the bug on line 42. The calculate() function doesn't check
if the denominator is zero. I'll add a check.

⚠️ Agent wants to perform sensitive operations

Action 1/1:
Tool: edit_file
path: utils.py
old_string: def calculate(a, b):
    return a / b
new_string: def calculate(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

Decision: approve

✓ Fixed the division by zero bug in utils.py
```

### Example 4: Add Type Hints

```
You: Add type hints to all functions in main.py

Agent: I'll read main.py and add type hints.

[Reads and analyzes main.py]

Found 8 functions without type hints. I'll add them.

⚠️ Agent wants to perform sensitive operations

Action 1/8:
Tool: edit_file
path: main.py
old_string: def process_data(data):
new_string: def process_data(data: dict) -> list:

Decision: approve
✓ Approved

[Continues for remaining functions]

✓ Added type hints to all 8 functions in main.py
```

### Example 5: Create New Module

```
You: Create a new database.py module with a Database class

Agent: I'll create a database module with a Database class.

⚠️ Agent wants to perform sensitive operations

Action 1/1:
Tool: write_file
path: database.py
content: """Database module for handling DB operations."""

class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    ...

Decision: approve

✓ Created database.py with Database class
```

### Example 6: Refactor Code

```
You: Refactor the UserManager class to use dependency injection

Agent: I'll refactor UserManager to accept dependencies through the constructor.

[Reads current implementation]

Current implementation has hard-coded dependencies. I'll:
1. Update __init__ to accept dependencies
2. Update all methods to use injected dependencies
3. Update tests (if they exist)

⚠️ Agent wants to perform sensitive operations

Action 1/1:
Tool: edit_file
path: src/user_manager.py
old_string: class UserManager:
    def __init__(self):
        self.db = Database()
        self.cache = Cache()
new_string: class UserManager:
    def __init__(self, db: Database, cache: Cache):
        self.db = db
        self.cache = cache

Decision: approve

✓ Refactored UserManager to use dependency injection
```

## Tips & Best Practices

### 1. Be Specific

❌ Bad: "Fix the code"
✅ Good: "Fix the division by zero error in utils.py calculate() function"

### 2. One Task at a Time

❌ Bad: "Add tests, fix bugs, refactor, and update docs"
✅ Good: "Add unit tests for the UserManager class"

Then continue with next task after completion.

### 3. Review Before Approving

When the agent asks for approval:
- Read the proposed changes carefully
- Use "edit" if you want to modify the action
- Use "reject" if you don't want it executed

### 4. Use `/clear` for New Topics

If you're switching to a completely different task:
```
You: /clear
[New conversation starts]

You: Now let's work on the API module
```

### 5. Let the Agent Plan

For complex tasks, the agent will:
1. Create a todo list
2. Break down the task
3. Execute step by step
4. Mark items complete

Trust this process!

### 6. Provide Context

If the agent seems confused:
```
You: The login function in auth.py isn't validating email formats properly.
It's on line 156. It should check for @ symbol and domain.
```

## Troubleshooting

### Agent Not Starting

**Problem**: "Missing required environment variables"

**Solution**: Set `OPENAI_API_KEY` in `.env` file:
```bash
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### Commands Timing Out

**Problem**: Commands take too long and timeout

**Solution**: Increase timeout:
```bash
deepagent-runner --workspace . --max-runtime 600
```

### Agent Making Wrong Changes

**Problem**: Agent proposed incorrect changes

**Solution**: 
1. Use "reject" when asked for approval
2. Clarify what you want
3. Let it try again

### Want to Undo Changes

**Problem**: Approved a change but want to revert

**Solution**: Ask the agent:
```
You: Undo the last change to utils.py
```

Or use git:
```
You: Run git diff to show recent changes
You: Run git checkout utils.py to revert
```

### Files Not Found

**Problem**: "File does not exist"

**Solution**: Check path is relative to workspace:
```
You: /workspace  # Check workspace path

You: List all files to see structure
You: Read src/utils.py  # Use correct relative path
```

### Conversation Getting Long

**Problem**: Agent responses slow or context too large

**Solution**: Clear conversation:
```
You: /clear
You: [Start fresh with new request]
```

## Advanced Usage

### Custom Models

Use different models:
```bash
# GPT-4
deepagent-runner --workspace . --model openai:gpt-4

# Claude
deepagent-runner --workspace . --model anthropic:claude-sonnet-4
```

### Verbose Mode

See detailed tool calls:
```bash
deepagent-runner --workspace . --verbose
```

### Logging

Save session to log file:
```bash
deepagent-runner --workspace . --log-file session.log
```

## Getting Help

- **In session**: Type `/help`
- **Documentation**: See [README.md](README.md)
- **Issues**: Check [GitHub Issues](https://github.com/...)

## Example Session

Here's a complete example session:

```
$ deepagent-runner --workspace my-project

Initializing agent...
✓ Agent ready!

Welcome to DeepAgent Runner! 🤖

You: List Python files

Agent: Found 12 Python files in src/

You: Run the tests

⚠️ Agent wants to execute: pytest tests/
Decision: approve

[Tests run, all pass]

You: There's a bug in utils.py - the parse_date function 
     crashes on invalid dates

Agent: I'll examine utils.py and fix the bug

[Reads file, identifies issue]

⚠️ Agent wants to edit utils.py
Decision: approve

✓ Fixed! Added try-except for invalid dates

You: Run the tests again to verify

⚠️ Agent wants to execute: pytest tests/
Decision: approve

[Tests pass]

You: Great! Now add a docstring to the parse_date function

⚠️ Agent wants to edit utils.py
Decision: approve

✓ Added docstring with examples

You: /exit
Goodbye! 👋
```

---

Happy coding with DeepAgent! 🚀

