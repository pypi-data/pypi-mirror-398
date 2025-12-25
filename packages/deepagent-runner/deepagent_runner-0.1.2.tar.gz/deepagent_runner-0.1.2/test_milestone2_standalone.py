"""Standalone test for Milestone 2 - no external dependencies needed."""

import os
import sys
import tempfile
from pathlib import Path


class SimpleWorkspaceBackend:
    """Simplified backend for testing sandbox logic without deepagents dependency."""

    def __init__(self, workspace: Path):
        """Initialize with workspace directory."""
        self.workspace = workspace.resolve()
        if not self.workspace.is_dir():
            raise ValueError(f"Workspace must be a directory: {self.workspace}")

    def validate_path(self, path: str) -> Path:
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
        """Validate that an operation on path is allowed."""
        try:
            target = self.validate_path(path)
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


def test_backend_initialization():
    """Test workspace backend initialization."""
    print("=" * 60)
    print("Test 1: Backend Initialization")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Test valid initialization
        try:
            backend = SimpleWorkspaceBackend(workspace=workspace)
            print(f"✓ Backend initialized with workspace: {workspace}")
        except Exception as e:
            print(f"✗ Failed to initialize backend: {e}")
            return False

    # Test invalid workspace (not a directory)
    try:
        with tempfile.NamedTemporaryFile() as tmpfile:
            backend = SimpleWorkspaceBackend(workspace=Path(tmpfile.name))
        print("✗ Should have failed for non-directory workspace")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected non-directory workspace")

    print()
    return True


def test_path_validation():
    """Test path validation and sandbox enforcement."""
    print("=" * 60)
    print("Test 2: Path Validation & Sandbox Enforcement")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        backend = SimpleWorkspaceBackend(workspace=workspace)

        # Test valid paths (within workspace)
        valid_paths = [
            "test.txt",
            "subdir/test.txt",
            "a/b/c/deep.txt",
            "/absolute/path.txt",  # Should be treated as relative
        ]

        for path in valid_paths:
            try:
                result = backend.validate_path(path)
                print(f"✓ Valid path accepted: {path}")
            except ValueError as e:
                print(f"✗ Valid path rejected: {path} - {e}")
                return False

        # Test directory traversal attempts (should all fail)
        escape_attempts = [
            "../outside.txt",
            "../../etc/passwd",
            "subdir/../../outside.txt",
            "subdir/../../../etc/passwd",
            "./../outside.txt",
        ]

        for attempt in escape_attempts:
            try:
                backend.validate_path(attempt)
                print(f"✗ SECURITY ISSUE: Path escape not blocked: {attempt}")
                return False
            except ValueError:
                print(f"✓ Blocked path escape attempt: {attempt}")

    print()
    return True


def test_filesystem_operations():
    """Test filesystem operation validation."""
    print("=" * 60)
    print("Test 3: Filesystem Operation Validation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        backend = SimpleWorkspaceBackend(workspace=workspace)

        # Create test file
        test_file = workspace / "test.txt"
        test_file.write_text("test content")
        print("✓ Created test file: test.txt")

        # Test read validation (existing file)
        try:
            backend.validate_operation("test.txt", "read")
            print("✓ Read operation validated for existing file")
        except ValueError as e:
            print(f"✗ Read validation failed: {e}")
            return False

        # Test write validation (new file)
        try:
            backend.validate_operation("new_file.txt", "write")
            print("✓ Write operation validated for new file")
        except ValueError as e:
            print(f"✗ Write validation failed: {e}")
            return False

        # Create subdirectory for nested tests
        subdir = workspace / "subdir"
        subdir.mkdir()
        
        try:
            backend.validate_operation("subdir/nested.txt", "write")
            print("✓ Write operation validated for nested file")
        except ValueError as e:
            print(f"✗ Nested write validation failed: {e}")
            return False

        # Test write to non-existent directory (should fail)
        try:
            backend.validate_operation("nonexistent_dir/file.txt", "write")
            print("✗ Should have failed for non-existent parent directory")
            return False
        except ValueError:
            print("✓ Correctly rejected write to non-existent directory")

        # Test read non-existent file (should fail)
        try:
            backend.validate_operation("nonexistent.txt", "read")
            print("✗ Should have failed for non-existent file")
            return False
        except ValueError:
            print("✓ Correctly rejected read of non-existent file")

    print()
    return True


def test_symlink_security():
    """Test symlink security."""
    print("=" * 60)
    print("Test 4: Symlink Security")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        backend = SimpleWorkspaceBackend(workspace=workspace)

        # Create an outside directory
        outside_dir = Path(tmpdir).parent / "outside_workspace"
        outside_dir.mkdir(exist_ok=True)
        outside_file = outside_dir / "secret.txt"
        outside_file.write_text("secret data")
        print(f"✓ Created outside file: {outside_file}")

        try:
            # Create symlink pointing outside workspace
            symlink = workspace / "link_to_outside"
            symlink.symlink_to(outside_file)
            print(f"✓ Created symlink: {symlink} -> {outside_file}")

            # Try to access via symlink (should fail)
            try:
                result = backend.validate_path("link_to_outside")
                print(f"✗ SECURITY ISSUE: Symlink escape not blocked!")
                print(f"  Symlink resolved to: {result}")
                return False
            except ValueError as e:
                print("✓ Blocked symlink escape to outside workspace")
                print(f"  Error: {e}")

        except OSError as e:
            print(f"⚠ Symlink test skipped (not supported): {e}")
            # Not a failure, just platform limitation

        finally:
            # Cleanup
            if outside_file.exists():
                outside_file.unlink()
            if outside_dir.exists():
                outside_dir.rmdir()

    print()
    return True


def test_real_world_scenarios():
    """Test real-world usage scenarios."""
    print("=" * 60)
    print("Test 5: Real-World Scenarios")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        backend = SimpleWorkspaceBackend(workspace=workspace)

        # Scenario 1: Python project structure
        print("\n📦 Scenario 1: Python project")
        project_files = [
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "README.md",
            "requirements.txt",
        ]

        for file_path in project_files:
            # Create parent directories
            full_path = workspace / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"# {file_path}")

            try:
                backend.validate_operation(file_path, "read")
                print(f"  ✓ {file_path}")
            except Exception as e:
                print(f"  ✗ {file_path}: {e}")
                return False

        # Scenario 2: Try to access /etc/passwd (should fail)
        print("\n🔒 Scenario 2: Security - system file access")
        dangerous_paths = [
            "/../../../etc/passwd",
            "/etc/passwd",  # Even though we treat / as workspace root
        ]

        for path in dangerous_paths:
            try:
                backend.validate_path(path)
                # If /etc/passwd resolves to workspace/etc/passwd, it's OK
                # But it should NOT resolve to real /etc/passwd
                result = backend.validate_path(path)
                if str(result) == "/etc/passwd":
                    print(f"  ✗ SECURITY ISSUE: Accessed real {path}")
                    return False
                print(f"  ✓ Blocked or sandboxed: {path}")
            except ValueError:
                print(f"  ✓ Blocked: {path}")

        # Scenario 3: Deep nesting
        print("\n📁 Scenario 3: Deep directory nesting")
        deep_path = "a/b/c/d/e/f/g/deep.txt"
        full_path = workspace / deep_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("deep file")

        try:
            backend.validate_operation(deep_path, "read")
            print(f"  ✓ Deep nesting works: {deep_path}")
        except Exception as e:
            print(f"  ✗ Deep nesting failed: {e}")
            return False

    print()
    return True


def main():
    """Run all Milestone 2 standalone tests."""
    print("\n" + "=" * 60)
    print("🧪 Milestone 2 - Filesystem Sandbox (Standalone Tests)")
    print("=" * 60)
    print()

    results = [
        ("Backend Initialization", test_backend_initialization()),
        ("Path Validation & Sandbox", test_path_validation()),
        ("Filesystem Operations", test_filesystem_operations()),
        ("Symlink Security", test_symlink_security()),
        ("Real-World Scenarios", test_real_world_scenarios()),
    ]

    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All Milestone 2 sandbox tests PASSED!")
        print("\n✅ Core sandbox functionality verified:")
        print("  • Workspace boundary enforcement")
        print("  • Directory traversal prevention")
        print("  • Symlink security")
        print("  • File operation validation")
        print()
        print("📦 Next steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Test full agent integration with DeepAgents")
        print("  3. Continue to Milestone 3 (execute tool)")
    else:
        print("\n❌ Some tests FAILED - fix issues before proceeding")
        sys.exit(1)

    print()


if __name__ == "__main__":
    main()

