"""Cross-platform shell command execution."""

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from deepagent_runner.config import ShellType, SystemInfo
from rich.console import Console

console = Console()

@dataclass
class CommandResult:
    """Result of command execution."""

    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    truncated: bool = False
    timed_out: bool = False


class ShellExecutor:
    """Execute shell commands in a workspace directory."""

    def __init__(
        self,
        workspace: Path,
        max_output_size: int = 1024 * 1024,  # 1MB default
        default_timeout: int = 300,  # 5 minutes default
    ):
        """
        Initialize shell executor.

        Args:
            workspace: Working directory for command execution
            max_output_size: Maximum output size in bytes
            default_timeout: Default timeout in seconds
        """
        self.workspace = workspace.resolve()
        self.max_output_size = max_output_size
        self.default_timeout = default_timeout

        # Detect system and available shells
        self.system_info = SystemInfo.detect()
        self.shell_type = self._determine_shell()

    def _determine_shell(self) -> ShellType:
        """
        Determine which shell to use based on system and availability.

        Priority:
        1. POSIX shells (bash → zsh → sh) - PREFERRED
        2. Windows shells (PowerShell → cmd) - FALLBACK

        Returns:
            ShellType to use for execution
        """
        # Use system info's preferred shell if available
        if self.system_info.preferred_shell:
            return self.system_info.preferred_shell

        # Fallback logic if no preferred shell detected
        # Try POSIX shells first
        if shutil.which("bash"):
            return ShellType.BASH
        elif shutil.which("zsh"):
            return ShellType.ZSH
        elif shutil.which("sh"):
            return ShellType.SH
        # Fallback to Windows shells
        elif shutil.which("powershell") or shutil.which("pwsh"):
            return ShellType.POWERSHELL
        elif shutil.which("cmd"):
            return ShellType.CMD
        else:
            raise RuntimeError("No compatible shell found on this system")

    def _build_command_args(self, command: str) -> list[str]:
        """
        Build command arguments for subprocess based on shell type.

        Args:
            command: Command string to execute

        Returns:
            List of arguments for subprocess.run()
        """
        if self.shell_type == ShellType.BASH:
            # Use login shell to load profile
            return ["/bin/bash", "-lc", command]

        elif self.shell_type == ShellType.ZSH:
            return ["/bin/zsh", "-lc", command]

        elif self.shell_type == ShellType.SH:
            return ["/bin/sh", "-c", command]

        elif self.shell_type == ShellType.POWERSHELL:
            # Try pwsh (PowerShell Core) first, fallback to powershell
            pwsh = shutil.which("pwsh") or shutil.which("powershell")
            return [pwsh, "-Command", command]

        elif self.shell_type == ShellType.CMD:
            return ["cmd.exe", "/C", command]

        else:
            raise RuntimeError(f"Unsupported shell type: {self.shell_type}")

    def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        env: Optional[dict] = None,
    ) -> CommandResult:
        """
        Execute a shell command in the workspace.

        Args:
            command: Command string to execute
            timeout: Timeout in seconds (uses default if None)
            env: Additional environment variables

        Returns:
            CommandResult with execution details

        Raises:
            ValueError: If command is invalid or dangerous
        """
        # Validate command
        self._validate_command(command)

        # Use default timeout if not specified
        if timeout is None:
            timeout = self.default_timeout

        # Build command arguments
        cmd_args = self._build_command_args(command)

        # Start timing
        start_time = time.time()

        # Execute command
        try:
            console.print(f"[Agent] Command cmd_args: {cmd_args}")
            result = subprocess.run(
                cmd_args,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Truncate output if too large
            stdout = result.stdout
            stderr = result.stderr
            truncated = False

            if len(stdout) > self.max_output_size:
                stdout = stdout[: self.max_output_size]
                stdout += f"\n\n[Output truncated at {self.max_output_size} bytes]"
                truncated = True

            if len(stderr) > self.max_output_size:
                stderr = stderr[: self.max_output_size]
                stderr += f"\n\n[Error output truncated at {self.max_output_size} bytes]"
                truncated = True

            return CommandResult(
                command=command,
                exit_code=result.returncode,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                truncated=truncated,
                timed_out=False,
            )

        except subprocess.TimeoutExpired as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Get partial output if available
            stdout = e.stdout.decode("utf-8", errors="replace") if e.stdout else ""
            stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""

            return CommandResult(
                command=command,
                exit_code=-1,
                stdout=stdout,
                stderr=f"Command timed out after {timeout} seconds\n{stderr}",
                duration_ms=duration_ms,
                truncated=False,
                timed_out=True,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                duration_ms=duration_ms,
                truncated=False,
                timed_out=False,
            )

    def _validate_command(self, command: str) -> None:
        """
        Validate command for basic safety checks.

        Args:
            command: Command to validate

        Raises:
            ValueError: If command is invalid or potentially dangerous
        """
        if not command or not command.strip():
            raise ValueError("Command cannot be empty")

        if len(command) > 10000:
            raise ValueError("Command is too long (max 10000 characters)")

        # Optional: Add deny-list for dangerous commands
        # This is a basic check, not foolproof
        dangerous_patterns = [
            "rm -rf /",
            "rm -rf /*",
            "mkfs",
            "dd if=/dev/zero",
            "> /dev/sda",
        ]

        command_lower = command.lower().strip()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                raise ValueError(
                    f"Command contains potentially dangerous pattern: {pattern}"
                )


def create_executor(
    workspace: Path,
    max_output_size: int = 1024 * 1024,
    default_timeout: int = 300,
) -> ShellExecutor:
    """
    Create a shell executor for a workspace.

    Args:
        workspace: Working directory for command execution
        max_output_size: Maximum output size in bytes
        default_timeout: Default timeout in seconds

    Returns:
        Configured ShellExecutor
    """
    return ShellExecutor(
        workspace=workspace,
        max_output_size=max_output_size,
        default_timeout=default_timeout,
    )

