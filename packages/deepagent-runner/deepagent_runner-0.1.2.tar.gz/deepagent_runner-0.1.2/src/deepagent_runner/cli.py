"""CLI entrypoint for DeepAgent Runner."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from deepagent_runner.config import (
    SystemInfo,
    WorkspaceConfig,
    get_default_model,
    validate_api_keys,
)
from deepagent_runner.session import start_session
from deepagent_runner.session_manager import get_session_manager

app = typer.Typer(
    name="deepagent-runner",
    help="Terminal application for running DeepAgent in a workspace directory",
    add_completion=False,
)

console = Console()


def print_error(message: str) -> None:
    """Print error message and exit."""
    console.print(f"[bold red]Error:[/bold red] {message}")
    raise typer.Exit(code=1)


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def prompt_workspace() -> Path:
    """Interactively prompt user for workspace directory."""
    console.print("\n[bold]Select workspace directory:[/bold]")
    console.print("  1. Use current directory")
    console.print("  2. Enter custom path")

    choice = typer.prompt("\nYour choice", type=int, default=1)

    if choice == 1:
        return Path.cwd()
    elif choice == 2:
        path_str = typer.prompt("Enter workspace path")
        return Path(path_str)
    else:
        print_error("Invalid choice. Please select 1 or 2.")
        sys.exit(1)


def display_system_info(system_info: SystemInfo) -> None:
    """Display system information in a nice table."""
    table = Table(title="System Information", show_header=True)
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Operating System", system_info.os_type.value.upper())
    table.add_row(
        "Available Shells",
        ", ".join([s.value for s in system_info.available_shells]) or "None",
    )
    table.add_row(
        "Preferred Shell",
        system_info.preferred_shell.value if system_info.preferred_shell else "None",
    )

    console.print("\n")
    console.print(table)


def display_workspace_config(config: WorkspaceConfig) -> None:
    """Display workspace configuration."""
    panel_content = f"""[bold]Workspace:[/bold] {config.path}
[bold]Model:[/bold] {config.model}
[bold]Max Runtime:[/bold] {config.max_runtime}s
[bold]Verbose:[/bold] {config.verbose}
[bold]Log File:[/bold] {config.log_file or 'None'}"""

    console.print("\n")
    console.print(Panel(panel_content, title="Configuration", border_style="blue"))


@app.command()
def run(
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Path to workspace directory (current dir if not specified)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Model identifier (e.g., 'openai:gpt-4.1-mini')",
    ),
    session: Optional[str] = typer.Option(
        None,
        "--session",
        "-s",
        help="Resume an existing session by ID",
    ),
    max_runtime: int = typer.Option(
        300,
        "--max-runtime",
        help="Maximum command execution time in seconds",
    ),
    log_file: Optional[str] = typer.Option(
        None,
        "--log-file",
        help="Path to log file for debugging",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """Run DeepAgent in the specified workspace."""
    console.print("\n[bold blue]DeepAgent Runner[/bold blue] 🤖\n")

    # Detect system
    print_info("Detecting system configuration...")
    system_info = SystemInfo.detect()
    display_system_info(system_info)

    # Validate API keys
    try:
        print_info("Validating API keys...")
        validate_api_keys()
        print_success("API keys validated")
    except ValueError as e:
        print_error(str(e))

    # Handle session resume
    if session:
        session_manager = get_session_manager()
        session_info = session_manager.get_session(session)
        if not session_info:
            print_error(f"Session '{session[:8]}...' not found. Use 'deepagent-runner sessions' to list sessions.")
        
        # Use workspace from session if not provided
        if not workspace:
            workspace_path = Path(session_info.workspace)
        else:
            workspace_path = Path(workspace)
        
        # Use model from session if not provided
        if not model:
            model = session_info.model
    else:
        # Get workspace path
        if workspace:
            workspace_path = Path(workspace)
        else:
            workspace_path = prompt_workspace()

    # Get model
    if not model:
        model = get_default_model()

    # Build config
    try:
        config = WorkspaceConfig(
            path=workspace_path,
            model=model,
            max_runtime=max_runtime,
            verbose=verbose,
            log_file=Path(log_file) if log_file else None,
        )
        print_success(f"Workspace validated: {config.path}")
    except ValueError as e:
        print_error(str(e))

    display_workspace_config(config)

    # Start interactive session
    if session:
        console.print("\n[bold green]Resuming session...[/bold green]\n")
    else:
        console.print("\n[bold green]Starting interactive session...[/bold green]\n")
    
    try:
        start_session(config, session_id=session)
    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted by user.[/yellow]\n")
    except Exception as e:
        print_error(f"Session failed: {str(e)}")


@app.command()
def version() -> None:
    """Show version information."""
    from deepagent_runner import __version__

    console.print(f"DeepAgent Runner version: [bold]{__version__}[/bold]")


@app.command()
def check() -> None:
    """Check system requirements and configuration."""
    console.print("\n[bold]System Check[/bold]\n")

    # System info
    system_info = SystemInfo.detect()
    display_system_info(system_info)

    # Check API keys
    console.print("\n[bold]API Keys:[/bold]")
    try:
        keys = validate_api_keys()
        for key_name, key_value in keys.items():
            if key_value:
                console.print(f"  ✓ {key_name}: [green]Set[/green]")
            else:
                console.print(f"  ✗ {key_name}: [yellow]Not set (optional)[/yellow]")
    except ValueError as e:
        console.print(f"  [red]✗ {e}[/red]")

    console.print()


@app.command()
def sessions(
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Filter sessions by workspace path",
    ),
) -> None:
    """List all saved sessions."""
    session_manager = get_session_manager()
    
    workspace_path = Path(workspace).resolve() if workspace else None
    sessions_list = session_manager.list_sessions(workspace=workspace_path)
    
    if not sessions_list:
        console.print("\n[yellow]No saved sessions found.[/yellow]\n")
        return
    
    table = Table(title="Saved Sessions", show_header=True)
    table.add_column("Session ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Workspace", style="blue")
    table.add_column("Model", style="yellow")
    table.add_column("Messages", justify="right", style="magenta")
    table.add_column("Last Used", style="dim")
    
    for session in sessions_list:
        session_id_short = session.session_id + "..."
        name = session.name or "(unnamed)"
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
    console.print("\n[dim]Resume a session: deepagent-runner --session <id>[/dim]\n")


if __name__ == "__main__":
    app()

