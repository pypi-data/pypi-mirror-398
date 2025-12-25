"""Interactive session management for DeepAgent."""

import uuid
from pathlib import Path
from typing import Optional

from langgraph.types import Command
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
import questionary
from questionary import Style

from deepagent_runner.agent import build_agent, create_session_config
from deepagent_runner.config import WorkspaceConfig
from deepagent_runner.session_manager import get_session_manager
from langchain.chat_models import init_chat_model

console = Console()

# Custom style for HITL buttons
HITL_STYLE = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
    ('disabled', 'fg:#858585 italic')
])

# Custom style for HITL buttons
HITL_STYLE = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
    ('disabled', 'fg:#858585 italic')
])


class REPLSession:
    """Interactive REPL session for DeepAgent."""

    def __init__(
        self,
        workspace: Path,
        model_id: str = "openai:gpt-4.1-mini",
        verbose: bool = False,
        max_command_timeout: int = 15,
        enable_hitl: bool = True,
        session_id: Optional[str] = None,
    ):
        """
        Initialize REPL session.

        Args:
            workspace: Workspace directory path
            model_id: Model identifier
            verbose: Enable verbose output
            max_command_timeout: Max timeout for shell commands
            enable_hitl: Enable human-in-the-loop approval
            session_id: Optional session ID to resume (creates new if None)
        """
        self.workspace = workspace
        self.model_id = model_id
        self.verbose = verbose
        self.max_command_timeout = max_command_timeout
        self.enable_hitl = enable_hitl
        
        # Initialize session manager
        self.session_manager = get_session_manager()
        
        # Resume existing session or create new
        if session_id:
            session_info = self.session_manager.get_session(session_id)
            if session_info:
                self.session_id = session_id
                self.message_count = session_info.message_count
                console.print(f"\n[yellow]Resuming session: {session_id}[/yellow]")
                if session_info.name:
                    console.print(f"[green]✓ Loaded session: {session_info.name}[/green]")
                console.print(f"  Messages: {session_info.message_count}\n")
            else:
                console.print(f"[yellow]Session {session_id}... not found, creating new session[/yellow]\n")
                self.session_id = str(uuid.uuid4())
                self.message_count = 0
                self.session_manager.create_session(
                    self.session_id,
                    workspace,
                    model_id,
                )
        else:
            # Create new session
            self.session_id = str(uuid.uuid4())
            self.message_count = 0
            self.session_manager.create_session(
                self.session_id,
                workspace,
                model_id,
            )

        # Create agent
        console.print("\n[yellow]Initializing agent...[/yellow]")
        self.agent = build_agent(
            workspace=workspace,
            model_id=model_id,
            verbose=verbose,
            max_command_timeout=max_command_timeout,
            enable_hitl=enable_hitl,
        )

        # Create session config
        self.config = create_session_config(thread_id=self.session_id)

        # Track conversation state
        self.running = True
        self.displayed_message_count = 0  # Track how many messages we've displayed
        self._first_message_processed = False  # Track if first message has been processed

        console.print("[green]✓ Agent ready![/green]\n")

    def print_welcome(self) -> None:
        """Print welcome message and instructions."""
        welcome_text = f"""
# Welcome to DeepAgent Runner! 🤖

**Workspace**: `{self.workspace}`
**Model**: `{self.model_id}`
**Session ID**: `{self.session_id}`

## What I can do:

- 📁 **Read, write, edit files** in your workspace
- 🐚 **Execute shell commands** (tests, builds, etc.)
- 🔍 **Search and analyze code**
- 📝 **Plan multi-step tasks**
- 🐛 **Fix bugs and refactor**

## REPL Commands:

- `/help` - Show this help message
- `/workspace` - Show current workspace
- `/config` - Show configuration (including session info)
- `/sessions` - List all saved sessions
- `/rename <name>` - Rename current session
- `/clear` - Clear conversation history and create new session
- `/exit` or `/quit` - Exit the session

## Tips:

- Be specific about what you want to do
- I'll break down complex tasks into steps
- I'll show you what I'm doing as I work
- Check my work and give feedback!

Type your request or a command to begin.
"""
        console.print(Markdown(welcome_text))

    def print_help(self) -> None:
        """Print help message."""
        help_text = """
# REPL Commands

- `/help` - Show this help message
- `/workspace` - Show current workspace directory
- `/config` - Show agent configuration (including session info)
- `/sessions` - List all saved sessions
- `/rename <name>` - Rename current session for easy identification
- `/clear` - Clear conversation history and create new session
- `/exit`, `/quit` - Exit the session

# Example Requests

- "List all Python files in src/"
- "Run the tests"
- "Fix the bug in utils.py where division by zero happens"
- "Add type hints to all functions in main.py"
- "Create a new module for database operations"
"""
        console.print(Markdown(help_text))

    def print_workspace_info(self) -> None:
        """Print workspace information."""
        info = f"""
**Workspace**: `{self.workspace}`
**Absolute path**: `{self.workspace.resolve()}`
**Exists**: {self.workspace.exists()}
**Is directory**: {self.workspace.is_dir()}
"""
        console.print(Panel(info, title="Workspace Info", border_style="blue"))

    def print_config_info(self) -> None:
        """Print configuration information."""
        session_info = self.session_manager.get_session(self.session_id)
        session_name = session_info.name if session_info else None
        
        info = f"""
**Model**: `{self.model_id}`
**Session ID**: `{self.session_id}`
**Workspace**: `{self.workspace}`
**Max Command Timeout**: `{self.max_command_timeout}s`
**Message Count**: `{self.message_count}`
**Session Name**: `{session_name or '(unnamed)'}`
**Verbose**: `{self.verbose}`
"""
        console.print(Panel(info, title="Configuration", border_style="cyan"))

    def handle_repl_command(self, command: str) -> bool:
        """
        Handle REPL commands.

        Args:
            command: Command string (e.g., "/exit", "/help")

        Returns:
            True if should continue session, False if should exit
        """
        command = command.lower().strip()

        if command in ["/exit", "/quit"]:
            # Save session before exiting
            self.session_manager.update_session(
                self.session_id,
                message_count=self.message_count,
            )
            console.print(f"\n[yellow]Exiting session. Session saved: {self.session_id}[/yellow]")
            console.print("[yellow]Goodbye! 👋[/yellow]\n")
            return False

        elif command == "/help":
            self.print_help()

        elif command == "/workspace":
            self.print_workspace_info()

        elif command == "/config":
            self.print_config_info()

        elif command == "/clear":
            console.print("\n[yellow]Clearing conversation history...[/yellow]")
            # Get old session name for new session
            old_session = self.session_manager.get_session(self.session_id)
            old_name = old_session.name if old_session else None
            new_name = f"{old_name} (cleared)" if old_name else None
            
            # Create new session ID for fresh start
            self.session_id = str(uuid.uuid4())
            self.config = create_session_config(thread_id=self.session_id)
            self.message_count = 0
            self.displayed_message_count = 0  # Reset displayed message count
            
            # Create new session in database
            self.session_manager.create_session(
                self.session_id,
                self.workspace,
                self.model_id,
                name=new_name,
            )
            console.print("[green]✓ Conversation cleared! New session created.[/green]\n")
        
        elif command == "/sessions":
            self.print_sessions_list()
        
        elif command.startswith("/rename "):
            new_name = command[8:].strip()
            if new_name:
                self.session_manager.update_session(self.session_id, name=new_name)
                console.print(f"[green]✓ Session renamed to: {new_name}[/green]\n")
            else:
                console.print("[red]Error: Please provide a name. Usage: /rename <name>[/red]\n")

        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("Type [cyan]/help[/cyan] for available commands.")

        return True
    
    def print_sessions_list(self) -> None:
        """Print list of all sessions."""
        sessions = self.session_manager.list_sessions()
        
        if not sessions:
            console.print("\n[yellow]No saved sessions found.[/yellow]\n")
            return
        
        table = Table(title="Sessions", show_header=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Workspace", style="blue")
        table.add_column("Model", style="yellow")
        table.add_column("Messages", justify="right", style="magenta")
        table.add_column("Last Used", style="dim")
        
        for session in sessions:
            session_id_short = session.session_id
            is_current = session.session_id == self.session_id
            name = session.name or "(unnamed)"
            if is_current:
                name += " ←"
            
            workspace_short = Path(session.workspace).name
            last_used = session.last_used.strftime("%Y-%m-%d %H:%M")
            
            table.add_row(
                session_id_short,
                name,
                workspace_short,
                session.model,
                str(session.message_count),
                last_used,
            )
        
        console.print("\n")
        console.print(table)
        console.print()

    def handle_interrupt(self, result: dict) -> dict:
        """
        Handle agent interrupt for human-in-the-loop approval.
        
        Args:
            result: Agent result with interrupt
            
        Returns:
            Updated result after approval
        """
        if not result.get("__interrupt__"):
            return result
        
        # Extract interrupt information
        interrupts = result["__interrupt__"][0].value
        action_requests = interrupts["action_requests"]
        review_configs = interrupts["review_configs"]
        
        # Create lookup map
        config_map = {cfg["action_name"]: cfg for cfg in review_configs}
        
        console.print("\n[bold yellow]⚠️  Agent wants to perform sensitive operations[/bold yellow]\n")
        
        decisions = []
        
        for idx, action in enumerate(action_requests, 1):
            review_config = config_map[action["name"]]
            allowed_decisions = review_config["allowed_decisions"]
            
            # Display action details
            console.print(f"[bold cyan]Action {idx}/{len(action_requests)}:[/bold cyan]")
            
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Key", style="yellow")
            table.add_column("Value")
            
            table.add_row("Tool", f"[bold]{action['name']}[/bold]")
            
            # Format arguments nicely
            for key, value in action["args"].items():
                # Truncate long values
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                table.add_row(key, value_str)
            
            console.print(table)
            console.print()
            
            # Build choices based on allowed decisions
            choices = []
            if "approve" in allowed_decisions:
                choices.append(
                    questionary.Choice(
                        title="✅ Approve - Execute as proposed",
                        value="approve"
                    )
                )
            if "edit" in allowed_decisions:
                choices.append(
                    questionary.Choice(
                        title="✏️  Edit - Modify arguments first",
                        value="edit"
                    )
                )
            if "reject" in allowed_decisions:
                choices.append(
                    questionary.Choice(
                        title="❌ Reject - Skip this action",
                        value="reject"
                    )
                )
            
            # Get user decision using interactive buttons
            decision = questionary.select(
                "What would you like to do?",
                choices=choices,
                style=HITL_STYLE,
                use_shortcuts=True,
                use_arrow_keys=True,
                use_jk_keys=True
            ).ask()
            
            if decision == "approve":
                decisions.append({"type": "approve"})
                console.print("[green]✓ Approved[/green]\n")
            
            elif decision == "reject":
                decisions.append({"type": "reject"})
                console.print("[red]✗ Rejected[/red]\n")
            
            elif decision == "edit":
                console.print("[yellow]✏️  Edit mode:[/yellow]\n")
                
                # Edit each argument using questionary.text
                edited_args = {}
                for key, value in action["args"].items():
                    # Determine default value and type
                    default_str = str(value)
                    if isinstance(value, bool):
                        # For boolean, use confirm
                        new_value = questionary.confirm(
                            f"  {key}:",
                            default=value
                        ).ask()
                    elif isinstance(value, (int, float)):
                        # For numbers, try to parse
                        new_value_str = questionary.text(
                            f"  {key}:",
                            default=default_str
                        ).ask()
                        try:
                            if isinstance(value, int):
                                new_value = int(new_value_str)
                            else:
                                new_value = float(new_value_str)
                        except ValueError:
                            new_value = new_value_str
                    else:
                        # For strings and others, use text
                        new_value = questionary.text(
                            f"  {key}:",
                            default=default_str
                        ).ask()
                    
                    edited_args[key] = new_value
                
                decisions.append({
                    "type": "edit",
                    "edited_action": {
                        "name": action["name"],
                        "args": edited_args
                    }
                })
                console.print("[yellow]✓ Edited[/yellow]\n")
        
        # Resume agent with decisions (use streaming)
        console.print("[yellow]Resuming agent with your decisions...[/yellow]\n")
        
        # Use streaming for resume as well
        result = self._stream_agent_response(
            Command[tuple[()]](resume={"decisions": decisions}),
            is_resume=True
        )
        
        return result

    def _stream_agent_response(self, input_data: dict, is_resume: bool = False) -> dict:
        """
        Stream agent response and handle interrupts.
        
        Args:
            input_data: Input data for agent (messages or Command)
            is_resume: Whether this is a resume after interrupt
            
        Returns:
            Final result from agent
        """
        # Stream agent execution
        if not is_resume:
            console.print("\n[bold green]Agent:[/bold green] ", end="")
        
        # Use stream with multiple modes: 
        # - messages: LLM tokens
        # - updates: state updates
        # - values: full state (to get final result)
        # - custom: custom events from subagents
        stream = self.agent.stream(
            input_data,
            config=self.config,
            stream_mode=["messages", "updates", "values", "custom"],
            # subgraphs=True,  # Enable subgraph streaming
        )
        
        final_result = None
        last_node = None
        last_full_state = None
        current_subagent = None  # Track current subagent
        
        # Process stream chunks with error handling
        try:
            chunk_count = 0
            for chunk in stream:
                chunk_count += 1
                if self.verbose and chunk_count == 1:
                    console.print("[dim]Streaming started...[/dim]")
                
                
                # Handle different stream modes
                if isinstance(chunk, tuple):
                    # Check tuple length
                    if len(chunk) == 2:
                        # Multiple modes: (mode, data)
                        mode, data = chunk
                    elif len(chunk) == 3:
                        # Subgraph mode: (namespace, mode, data)
                        namespace, mode, data = chunk
                        # Process silently - namespace info already in langgraph_node metadata
                    else:
                        # Unknown tuple format
                        if self.verbose:
                            console.print(f"\n[dim]Unknown tuple format with {len(chunk)} elements[/dim]")
                        continue
                    
                    if mode == "messages":
                        # Stream LLM tokens
                        message_chunk, metadata = data
                        
                        # Always try to print content if available
                        if hasattr(message_chunk, 'content') and message_chunk.content:
                            # Check if this is from a subagent
                            langgraph_node = metadata.get("langgraph_node", "") if metadata else ""
                            
                            # Detect subagent execution (node contains task__)
                            if "task__" in langgraph_node and langgraph_node != current_subagent:
                                # Extract subagent name from node (e.g., "task__research-agent")
                                subagent_name = langgraph_node.replace("task__", "").split(":")[0]
                                current_subagent = langgraph_node
                                console.print(f"\n\n[bold yellow]🔍 {subagent_name}:[/bold yellow] ", end="")
                            elif current_subagent and langgraph_node and "task__" not in langgraph_node:
                                # Exiting subagent, back to main agent
                                current_subagent = None
                                console.print("\n\n[bold green]💬 Agent:[/bold green] ", end="")
                            
                            # Print token immediately (no newline, flush)
                            if current_subagent:
                                # Subagent output - different style
                                console.print(message_chunk.content, end="", style="yellow")
                            else:
                                # Main agent output
                                console.print(message_chunk.content, end="", style="green")
                            
                            # Track node for verbose output
                            if langgraph_node:
                                last_node = langgraph_node
                    
                    elif mode == "updates":
                        # Stream state updates (tool calls, etc.)
                        if self.verbose and data:
                            for node_name, update in data.items():
                                # Detect subagent tool calls
                                if "task__" in node_name:
                                    subagent_name = node_name.replace("task__", "").split(":")[0]
                                    if node_name != last_node:
                                        console.print(f"\n[dim yellow]  [{subagent_name} working...][/dim yellow]", end=" ")
                                        last_node = node_name
                                elif node_name != last_node:  # Avoid duplicate output
                                    console.print(f"\n[dim cyan][{node_name}][/dim cyan]", end=" ")
                                    last_node = node_name
                    
                    elif mode == "custom":
                        # Custom events (from subagents)
                        if data and self.verbose:
                            # Display custom events from subagents
                            event_type = data.get("type")
                            event_data = data.get("data")
                            
                            if event_type == "subagent_start":
                                subagent_name = event_data.get("name", "unknown")
                                console.print(f"\n[bold magenta]⚡ Starting subagent: {subagent_name}[/bold magenta]")
                            elif event_type == "subagent_end":
                                subagent_name = event_data.get("name", "unknown")
                                console.print(f"\n[bold magenta]✓ Subagent {subagent_name} completed[/bold magenta]")
                    
                    elif mode == "values":
                        # Full state after each step - store for final result
                        if data:
                            last_full_state = data
                
                elif isinstance(chunk, dict):
                    # Final result or interrupt (single mode)
                    if "__interrupt__" in chunk:
                        final_result = chunk
                        break
                    elif "messages" in chunk:
                        # Final state
                        final_result = chunk
                else:
                    # Unknown chunk type - log in verbose mode
                    if self.verbose:
                        console.print(f"\n[dim]Unknown chunk type: {type(chunk)}[/dim]")
        
        except PermissionError as e:
            # Handle filesystem permission errors gracefully
            error_msg = str(e)
            console.print("\n")  # Newline after streaming
            
            if "/proc" in error_msg or "/sys" in error_msg or "/dev" in error_msg:
                console.print("\n[red]Error:[/red] Cannot access system filesystem\n")
                console.print("[yellow]This may happen when searching through files that contain symlinks to system directories like /proc, /sys, or /dev.[/yellow]\n")
                console.print("[dim]Suggestion: Try being more specific with your search path or use a different approach.[/dim]\n")
            else:
                console.print(f"\n[red]Error:[/red] Permission denied: {error_msg}\n")
                console.print("[yellow]You may not have permission to access this file or directory.[/yellow]\n")
            
            # Return error result instead of crashing
            if last_full_state:
                final_result = last_full_state
            else:
                # Create a minimal error result
                final_result = {
                    "messages": [{"role": "assistant", "content": "I encountered a permission error while accessing the filesystem. Please try a more specific search path or check file permissions."}]
                }
            
            return final_result
        
        except Exception as e:
            # Handle other errors during streaming
            error_msg = str(e)
            console.print("\n")  # Newline after streaming
            
            if "Permission denied" in error_msg or "Errno 13" in error_msg:
                if "/proc" in error_msg or "/sys" in error_msg or "/dev" in error_msg:
                    console.print("\n[red]Error:[/red] Cannot access system filesystem\n")
                    console.print("[yellow]This may happen when searching through files that contain symlinks to system directories.[/yellow]\n")
                    console.print("[dim]Suggestion: Try being more specific with your search path.[/dim]\n")
                else:
                    console.print(f"\n[red]Error:[/red] Permission denied: {error_msg}\n")
            else:
                console.print(f"\n[red]Error during execution:[/red] {error_msg}\n")
            
            # Return error result instead of crashing
            if last_full_state:
                final_result = last_full_state
            else:
                final_result = {
                    "messages": [{"role": "assistant", "content": f"I encountered an error: {error_msg}. Please try a different approach."}]
                }
            
            return final_result
        
        # Print newline after streaming
        console.print("\n")
        
        if self.verbose:
            console.print(f"[dim]Received {chunk_count} stream chunks[/dim]")
        
        # Use last full state as final result if no explicit result
        if final_result is None and last_full_state:
            final_result = last_full_state
        
        return final_result

    def invoke_agent(self, user_message: str) -> None:
        """
        Invoke agent with user message and display response with streaming.

        Args:
            user_message: User's message/request
        """
        # Prepare input
        messages = [{"role": "user", "content": user_message}]

        try:
            # Stream agent execution
            result = self._stream_agent_response({"messages": messages})
            
            # Handle interrupts (HITL) - may need multiple rounds
            # handle_interrupt already handles streaming for resume
            while result and result.get("__interrupt__"):
                result = self.handle_interrupt(result)
            
            # Extract final agent response for message tracking
            if result and "messages" in result:
                agent_messages = result["messages"]
                
                # Only display new messages that weren't streamed
                new_messages = agent_messages[self.displayed_message_count:]
                
                for msg in new_messages:
                    if hasattr(msg, "content") and msg.content:
                        # Check message type
                        if hasattr(msg, "type"):
                            if msg.type == "tool":
                                # Tool result (show if verbose)
                                if self.verbose:
                                    console.print(f"[dim cyan]Tool result:[/dim cyan]")
                                    console.print(Panel(msg.content, border_style="dim"))
                
                # Update displayed message count
                self.displayed_message_count = len(agent_messages)

            # Increment message count
            self.message_count += 1
            
            # Auto-name session after first message if unnamed
            if not self._first_message_processed:
                self._first_message_processed = True
                self._auto_name_session(user_message)
            
            # Update session in database
            self.session_manager.update_session(
                self.session_id,
                message_count=self.message_count,
            )

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted by user[/yellow]")
            raise

        except PermissionError as e:
            error_msg = str(e)
            if "/proc" in error_msg or "/sys" in error_msg or "/dev" in error_msg:
                console.print(f"\n[red]Error:[/red] Permission denied accessing system filesystem ({error_msg.split('/')[-1]})\n")
                console.print("[yellow]This may happen when searching through files that contain symlinks to system directories.[/yellow]\n")
                console.print("[dim]Try being more specific with your search path or exclude system directories.[/dim]\n")
            else:
                console.print(f"\n[red]Error:[/red] Permission denied: {error_msg}\n")
                console.print("[yellow]You may not have permission to access this file or directory.[/yellow]\n")
            if self.verbose:
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
        
        except Exception as e:
            error_msg = str(e)
            # Check for common filesystem errors
            if "Permission denied" in error_msg or "Errno 13" in error_msg:
                if "/proc" in error_msg or "/sys" in error_msg or "/dev" in error_msg:
                    console.print(f"\n[red]Error:[/red] Cannot access system filesystem ({error_msg.split('/')[-1] if '/' in error_msg else 'unknown'})\n")
                    console.print("[yellow]This may happen when searching through files that contain symlinks to system directories like /proc, /sys, or /dev.[/yellow]\n")
                    console.print("[dim]Suggestion: Try being more specific with your search path or use a different approach.[/dim]\n")
                else:
                    console.print(f"\n[red]Error:[/red] Permission denied: {error_msg}\n")
            else:
                console.print(f"\n[red]Error:[/red] {error_msg}\n")
            
            if self.verbose:
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    def _auto_name_session(self, user_message: str) -> None:
        """
        Automatically generate and set session name based on first user message.
        
        Args:
            user_message: First user message to analyze
        """
        try:
            # Check if session already has a name
            session_info = self.session_manager.get_session(self.session_id)
            if session_info and session_info.name:
                return  # Already has a name, skip
            
            # Generate session name using LLM
            model = init_chat_model(self.model_id)
            
            prompt = f"""Based on this user request, generate a concise session name (max 50 characters) that describes the task or purpose.

User request: "{user_message}"

Generate a short, descriptive name. Examples:
- "Fix login bug" for bug fixes
- "Add user authentication" for features
- "Refactor API module" for refactoring
- "Update documentation" for docs
- "Run tests" for testing

Return ONLY the name, nothing else. Keep it under 50 characters."""

            response = model.invoke([{"role": "user", "content": prompt}])
            session_name = response.content.strip()
            
            # Clean up the name (remove quotes if present, limit length)
            session_name = session_name.strip('"\'')
            if len(session_name) > 50:
                session_name = session_name[:47] + "..."
            
            # Update session with generated name
            if session_name:
                self.session_manager.update_session(
                    self.session_id,
                    name=session_name,
                )
                if self.verbose:
                    console.print(f"[dim]✓ Session auto-named: {session_name}[/dim]\n")
        
        except Exception as e:
            # Silently fail - don't interrupt user experience
            if self.verbose:
                console.print(f"[dim]Failed to auto-name session: {e}[/dim]\n")

    def run(self) -> None:
        """Run the interactive REPL session."""
        # Print welcome
        self.print_welcome()

        # Main loop
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]").strip()

                # Skip empty input
                if not user_input:
                    continue

                # Check for REPL commands
                if user_input.startswith("/"):
                    self.running = self.handle_repl_command(user_input)
                    continue

                # Invoke agent
                self.invoke_agent(user_input)

            except KeyboardInterrupt:
                console.print("\n\n[yellow]Use /exit or /quit to exit properly[/yellow]")
                continue

            except EOFError:
                # End of input (Ctrl+D)
                console.print("\n[yellow]Exiting session. Goodbye! 👋[/yellow]\n")
                break

            except Exception as e:
                console.print(f"\n[red]Unexpected error:[/red] {str(e)}\n")
                if self.verbose:
                    import traceback
                    console.print(f"[dim]{traceback.format_exc()}[/dim]")
                continue


def start_session(config: WorkspaceConfig, session_id: Optional[str] = None) -> None:
    """
    Start an interactive REPL session.

    Args:
        config: Workspace configuration
        session_id: Optional session ID to resume
    """
    try:
        session = REPLSession(
            workspace=config.path,
            model_id=config.model,
            verbose=config.verbose,
            max_command_timeout=config.max_runtime,
            session_id=session_id,
        )
        session.run()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Session interrupted. Goodbye! 👋[/yellow]\n")

    except Exception as e:
        console.print(f"\n[red]Failed to start session:[/red] {str(e)}\n")
        raise

