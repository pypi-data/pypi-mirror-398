# Session Management

Complete guide to managing multiple agent sessions.

## Overview

DeepAgent Runner now supports **multiple persistent sessions**. Each session maintains its own:
- Conversation history
- Message count
- Metadata (name, description)
- Timestamps (created, last used)

Sessions are stored at: `~/.deepagent/sessions/`

## Features

### ✅ Session Persistence
- Sessions save automatically on every message
- Resume sessions across restarts
- Metadata stored in SQLite database

### ✅ Multiple Sessions
- Create unlimited sessions
- Run multiple sessions concurrently (different terminals)
- Each session isolated from others

### ✅ Session Organization
- Name sessions for easy identification
- Search sessions by name or description
- List all sessions or filter by workspace

### ✅ CLI Commands
- `deepagent-runner sessions` - List all sessions
- `deepagent-runner --session <id>` - Resume a session
- `deepagent-runner sessions --workspace <path>` - Filter by workspace

### ✅ REPL Commands
- `/sessions` - List all sessions
- `/rename <name>` - Rename current session
- `/config` - Show session info (ID, name, messages)
- `/clear` - Clear and create new session

## Quick Start

### 1. Start New Session

```bash
deepagent-runner --workspace /path/to/project
```

A new session is automatically created. You'll see:
```
Session ID: abc12345...
```

### 2. List All Sessions

```bash
deepagent-runner sessions
```

Output:
```
Saved Sessions

Session ID        Name        Workspace    Model             Messages    Last Used
abc12345...       (unnamed)   my-project   gpt-5.1-codex-mini   5           2025-12-18 10:30
def67890...       Bug Fix     my-project   gpt-5.1-codex-mini   12          2025-12-18 09:15
```

### 3. Resume a Session

```bash
deepagent-runner --workspace /path/to/project --session abc12345
```

Or if the session stores the workspace:
```bash
deepagent-runner --session abc12345
```

## Usage Examples

### Example 1: Bug Fix Session

```bash
# Start new session
$ deepagent-runner --workspace my-project

You: /rename Bug Fix - Login Issue
✓ Session renamed

You: Fix the login validation bug

Agent: [Fixes bug]

You: /exit
Session saved: abc12345...
```

Later:
```bash
# Resume same session
$ deepagent-runner --session abc12345

Resuming session: abc12345...
✓ Loaded session: Bug Fix - Login Issue
  Messages: 5

You: Run the tests to verify the fix

Agent: [Runs tests]
```

### Example 2: Multiple Concurrent Sessions

Terminal 1:
```bash
$ deepagent-runner --workspace frontend
You: /rename Frontend Work
You: Update the navbar component
```

Terminal 2 (same time):
```bash
$ deepagent-runner --workspace backend  
You: /rename Backend API
You: Add authentication endpoint
```

Both sessions run independently!

### Example 3: Organize Sessions

```bash
# Create named sessions for different tasks
$ deepagent-runner --workspace my-project

You: /rename Feature: User Profiles
You: Implement user profile page
...
You: /exit

# Next session
$ deepagent-runner --workspace my-project

You: /rename Bug: Memory Leak
You: Investigate memory usage
...
You: /exit

# List all
$ deepagent-runner sessions

Session ID        Name                   Workspace    Messages
abc123...         Feature: User Profiles my-project   15
def456...         Bug: Memory Leak       my-project   8
```

## REPL Commands

### `/sessions`
List all sessions from within a session:

```
You: /sessions

Sessions
ID          Name              Workspace    Messages    Last Used
abc123...   Current ←         my-project   5           2025-12-18 10:30
def456...   Bug Fix           my-project   12          2025-12-18 09:15
```

The current session is marked with `←`.

### `/rename <name>`
Rename the current session:

```
You: /rename My Important Work
✓ Session renamed to: My Important Work
```

### `/config`
Show current session details:

```
You: /config

Configuration
  Model: openai:gpt-5.1-codex-mini
  Session ID: abc123...
  Workspace: /path/to/project
  Max Command Timeout: 300s
  Message Count: 5
  Session Name: My Important Work
```

### `/clear`
Clear conversation and create new session:

```
You: /clear

Clearing conversation history...
✓ Conversation cleared! New session created.
```

This creates a new session with name "{old_name} (cleared)".

## Storage

### Location
```
~/.deepagent/sessions/
├── sessions.db          # Session metadata
└── checkpoints.db       # Conversation state
```

### Metadata Stored
- Session ID (UUID)
- Workspace path
- Model used
- Created timestamp
- Last used timestamp
- Message count
- Name (optional)
- Description (optional)

### Backup
To backup sessions, copy the entire directory:

```bash
cp -r ~/.deepagent/sessions ~/.deepagent/sessions.backup
```

## Advanced Usage

### Filter by Workspace

List only sessions for a specific workspace:

```bash
deepagent-runner sessions --workspace /path/to/my-project
```

### Search Sessions

Use `grep` or search within the REPL:

```bash
# Show all session with "bug" in name
$ deepagent-runner sessions | grep -i bug
```

### Delete Old Sessions

Currently manual:
```bash
# Interactive Python
$ python3
>>> from deepagent_runner.session_manager import get_session_manager
>>> sm = get_session_manager()
>>> sessions = sm.list_sessions()
>>> for s in sessions:
...     if s.message_count == 0:  # Delete empty sessions
...         sm.delete_session(s.session_id)
```

Or delete database:
```bash
rm ~/.deepagent/sessions/sessions.db
```

## Tips & Best Practices

### 1. Name Your Sessions
```
You: /rename Feature: Add OAuth
```

Easier to find later than "abc123...".

### 2. One Session Per Task
- Bug fixes
- Features
- Refactoring
- Experiments

### 3. Use `/clear` for New Topics
Within same workspace but different topic:
```
You: /clear
You: Now let's work on the API
```

### 4. Check `/sessions` Regularly
See all your work:
```
You: /sessions
```

### 5. Resume Recent Sessions
```bash
# List recent first
deepagent-runner sessions

# Resume most recent
deepagent-runner --session <id>
```

## Limitations

### Current Limitations:

1. **No session switching in REPL**
   - Must exit and restart to switch sessions
   - Could add `/switch` command in future

2. **No session export/import**
   - Can't export conversation to markdown
   - Database is SQLite (can query directly)

3. **No session merging**
   - Can't combine two sessions
   - Would need custom script

4. **Checkpointer persistence**
   - Currently uses MemorySaver (in-memory)
   - SqliteSaver requires langgraph update
   - Metadata persists, but conversation state may not

## Troubleshooting

### Session Not Found

```
Error: Session 'abc123' not found
```

**Solution**: List sessions and use correct ID:
```bash
deepagent-runner sessions
```

### Can't Resume Session

**Problem**: Different workspace

**Solution**: Sessions store workspace. Either:
1. Use stored workspace (don't pass `--workspace`)
2. Session may be for different workspace

### Too Many Sessions

**Problem**: Database getting large

**Solution**: Manually clean up:
```bash
rm ~/.deepagent/sessions/sessions.db
rm ~/.deepagent/sessions/checkpoints.db
```

This deletes ALL sessions. Backup first if needed.

## Future Enhancements

Potential improvements:
- `/switch <id>` - Switch session in REPL
- `--delete-session <id>` - Delete from CLI
- `--export-session <id>` - Export to markdown
- Auto-cleanup old sessions
- Session tags/categories
- Session search UI

## Summary

Session management enables:
- ✅ Multiple isolated conversations
- ✅ Resume work across restarts
- ✅ Organize work by topic
- ✅ Concurrent agent sessions
- ✅ Persistent metadata

**Storage**: `~/.deepagent/sessions/`
**CLI**: `deepagent-runner sessions`
**REPL**: `/sessions`, `/rename`, `/config`

Enjoy organized agent workflows! 🎉

