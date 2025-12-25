"""Configuration and OS detection module."""

import os
import platform
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Load environment variables from .env file
load_dotenv()


class OSType(str, Enum):
    """Supported operating system types."""

    LINUX = "linux"
    DARWIN = "darwin"  # macOS
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class ShellType(str, Enum):
    """Available shell types."""

    BASH = "bash"
    ZSH = "zsh"
    SH = "sh"
    POWERSHELL = "powershell"
    CMD = "cmd"


class SystemInfo(BaseModel):
    """System information including OS and available shells."""

    os_type: OSType
    available_shells: list[ShellType] = Field(default_factory=list)
    preferred_shell: Optional[ShellType] = None
    os_version: Optional[str] = None  # OS version (e.g., "13.0" for macOS Ventura)
    os_release: Optional[str] = None  # OS release name (e.g., "Darwin 22.1.0")

    @staticmethod
    def detect() -> "SystemInfo":
        """Detect current system OS and available shells."""
        system = platform.system().lower()

        if system == "linux":
            os_type = OSType.LINUX
        elif system == "darwin":
            os_type = OSType.DARWIN  # macOS
        elif system == "windows":
            os_type = OSType.WINDOWS
        else:
            os_type = OSType.UNKNOWN

        available_shells = []
        preferred_shell = None

        # macOS-specific: zsh is the default shell since macOS Catalina (10.15)
        # Prefer zsh for macOS, but also support bash
        if os_type == OSType.DARWIN:
            # Check for zsh first (macOS default since Catalina)
            if shutil.which("zsh"):
                available_shells.append(ShellType.ZSH)
                preferred_shell = ShellType.ZSH
            # Also add bash if available (macOS includes bash but zsh is preferred)
            if shutil.which("bash"):
                available_shells.append(ShellType.BASH)
                if not preferred_shell:
                    preferred_shell = ShellType.BASH
            # Fallback to sh if neither zsh nor bash available
            if shutil.which("sh") and not preferred_shell:
                available_shells.append(ShellType.SH)
                preferred_shell = ShellType.SH
        else:
            # For Linux and other POSIX systems, prefer bash
            if shutil.which("bash"):
                available_shells.append(ShellType.BASH)
                preferred_shell = ShellType.BASH
            elif shutil.which("zsh"):
                available_shells.append(ShellType.ZSH)
                preferred_shell = ShellType.ZSH
            elif shutil.which("sh"):
                available_shells.append(ShellType.SH)
                preferred_shell = ShellType.SH

        # Check for Windows shells (fallback for Windows or if no POSIX shell found)
        if os_type == OSType.WINDOWS or not preferred_shell:
            if shutil.which("powershell") or shutil.which("pwsh"):
                available_shells.append(ShellType.POWERSHELL)
                if not preferred_shell:
                    preferred_shell = ShellType.POWERSHELL

            if shutil.which("cmd"):
                available_shells.append(ShellType.CMD)
                if not preferred_shell:
                    preferred_shell = ShellType.CMD

        # Get OS version information
        os_version = None
        os_release = None
        
        if os_type == OSType.DARWIN:
            # macOS version info
            os_release = platform.release()  # Darwin kernel version
            # Try to get macOS version (e.g., "13.0" for Ventura)
            try:
                # Use sw_vers command on macOS to get version
                result = subprocess.run(
                    ["sw_vers", "-productVersion"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    os_version = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                # Fallback to platform.mac_ver() if sw_vers not available
                try:
                    mac_version = platform.mac_ver()[0]
                    if mac_version:
                        os_version = mac_version
                except Exception:
                    pass
        elif os_type == OSType.LINUX:
            os_release = platform.release()
            # Try to get Linux distribution info
            try:
                # Try common methods to get distro info
                for cmd in [["lsb_release", "-d"], ["cat", "/etc/os-release"]]:
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=1
                        )
                        if result.returncode == 0:
                            os_version = result.stdout.strip()[:100]  # Limit length
                            break
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue
            except Exception:
                pass
        elif os_type == OSType.WINDOWS:
            os_version = platform.version()
            os_release = platform.release()

        return SystemInfo(
            os_type=os_type,
            available_shells=available_shells,
            preferred_shell=preferred_shell,
            os_version=os_version,
            os_release=os_release,
        )


class WorkspaceConfig(BaseModel):
    """Configuration for workspace directory."""

    path: Path
    model: str = Field(default="openai:gpt-4.1-mini")
    max_runtime: int = Field(default=300, description="Max command execution time in seconds")
    verbose: bool = Field(default=False)
    log_file: Optional[Path] = None

    @field_validator("path")
    @classmethod
    def validate_workspace_path(cls, v: Path) -> Path:
        """Validate that workspace path exists and is a directory."""
        resolved = v.resolve()

        if not resolved.exists():
            raise ValueError(f"Workspace path does not exist: {resolved}")

        if not resolved.is_dir():
            raise ValueError(f"Workspace path is not a directory: {resolved}")

        # Check if we have read/write permissions
        if not os.access(resolved, os.R_OK | os.W_OK):
            raise ValueError(f"Insufficient permissions for workspace: {resolved}")

        return resolved

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model identifier format."""
        if ":" not in v:
            raise ValueError(
                f"Model identifier must be in format 'provider:model', got: {v}"
            )
        return v


def get_default_model() -> str:
    """Get default model from environment or return hardcoded default."""
    return os.getenv("OPENAI_MODEL", "openai:gpt-4.1-mini")


def validate_api_keys() -> dict[str, str]:
    """Validate required API keys are present in environment."""
    required_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    }

    optional_keys = {
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
    }

    missing = [key for key, value in required_keys.items() if not value]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please set them in your environment or .env file."
        )

    return {**required_keys, **optional_keys}

