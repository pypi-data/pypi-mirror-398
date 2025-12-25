"""Filesystem backend with workspace sandboxing."""

import os
from pathlib import Path
from typing import Optional

from deepagents.backends import FilesystemBackend


class WorkspaceFilesystemBackend(FilesystemBackend):
    """
    Filesystem backend rooted at workspace directory.
    
    Ensures all file operations are sandboxed within the workspace.
    Prevents directory traversal and symlink attacks.
    """

    def __init__(self, workspace: Path):
        """
        Initialize workspace filesystem backend.
        
        Args:
            workspace: Absolute path to workspace directory
            virtual: If True, use virtual mode (no real filesystem access)
        """
        self.workspace = workspace.resolve()
        if not self.workspace.is_dir():
            raise ValueError(f"Workspace must be a directory: {self.workspace}")
        
        # Initialize parent FilesystemBackend with workspace as root
        super().__init__(root_dir=str(self.workspace))

    def _validate_path(self, path: str) -> Path:
        """
        Validate that path is within workspace and safe.
        
        Args:
            path: Path string to validate
            
        Returns:
            Resolved absolute Path object
            
        Raises:
            ValueError: If path escapes workspace or is unsafe
        """
        # Convert to Path object
        if path.startswith("/"):
            # Absolute path - treat as relative to workspace root
            path = path[1:]
        
        target = (self.workspace / path).resolve()
        
        # Check if resolved path is within workspace
        try:
            target.relative_to(self.workspace)
        except ValueError:
            raise ValueError(
                f"Path '{path}' escapes workspace. "
                f"All paths must be within {self.workspace}"
            )
        
        # Check for symlink attacks
        if target.is_symlink():
            # Follow symlink and check destination is still in workspace
            real_target = target.resolve()
            try:
                real_target.relative_to(self.workspace)
            except ValueError:
                raise ValueError(
                    f"Symlink '{path}' points outside workspace. "
                    f"Target: {real_target}"
                )
        
        return target

    def validate_operation(self, path: str, operation: str = "access") -> bool:
        """
        Validate that an operation on path is allowed.
        
        Args:
            path: Path to validate
            operation: Type of operation (access, read, write)
            
        Returns:
            True if operation is allowed
            
        Raises:
            ValueError: If operation is not allowed
        """
        try:
            target = self._validate_path(path)
        except ValueError:
            raise
        
        # Additional checks based on operation type
        if operation == "write":
            # Check if parent directory exists
            if not target.parent.exists():
                raise ValueError(
                    f"Parent directory does not exist: {target.parent}"
                )
            
            # Check write permissions on parent
            if not os.access(target.parent, os.W_OK):
                raise ValueError(
                    f"No write permission for directory: {target.parent}"
                )
        
        elif operation == "read":
            # Check if file exists and is readable
            if not target.exists():
                raise ValueError(f"File does not exist: {path}")
            
            if not os.access(target, os.R_OK):
                raise ValueError(f"No read permission for file: {path}")
        
        return True


def create_workspace_backend(workspace: Path) -> WorkspaceFilesystemBackend:
    """
    Create a workspace filesystem backend.
    
    Args:
        workspace: Path to workspace directory
        
    Returns:
        Configured WorkspaceFilesystemBackend
    """
    return WorkspaceFilesystemBackend(workspace=workspace)

