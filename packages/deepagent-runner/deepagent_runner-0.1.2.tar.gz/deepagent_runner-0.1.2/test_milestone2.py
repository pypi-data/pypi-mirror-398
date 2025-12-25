"""Test script for Milestone 2 - Filesystem Sandbox."""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from deepagent_runner.backend import WorkspaceFilesystemBackend, create_workspace_backend


def test_backend_initialization():
    """Test workspace backend initialization."""
    print("=" * 60)
    print("Testing Backend Initialization")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Test valid initialization
        try:
            backend = create_workspace_backend(workspace)
            print(f"✓ Backend initialized with workspace: {workspace}")
            print(f"  Root dir: {backend.root_dir}")
        except Exception as e:
            print(f"✗ Failed to initialize backend: {e}")
            return False

    # Test invalid workspace (not a directory)
    try:
        with tempfile.NamedTemporaryFile() as tmpfile:
            backend = WorkspaceFilesystemBackend(workspace=Path(tmpfile.name))
        print("✗ Should have failed for non-directory workspace")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected non-directory: {e}")

    print()
    return True


def test_path_validation():
    """Test path validation and sandbox enforcement."""
    print("=" * 60)
    print("Testing Path Validation & Sandbox")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        backend = WorkspaceFilesystemBackend(workspace=workspace)

        # Test valid path (within workspace)
        try:
            backend._validate_path("test.txt")
            print("✓ Valid path accepted: test.txt")
        except ValueError as e:
            print(f"✗ Valid path rejected: {e}")
            return False

        try:
            backend._validate_path("subdir/test.txt")
            print("✓ Valid path accepted: subdir/test.txt")
        except ValueError as e:
            print(f"✗ Valid path rejected: {e}")
            return False

        # Test directory traversal attempts (should fail)
        traversal_attempts = [
            "../outside.txt",
            "../../etc/passwd",
            "subdir/../../outside.txt",
        ]

        for attempt in traversal_attempts:
            try:
                backend._validate_path(attempt)
                print(f"✗ Path escape not blocked: {attempt}")
                return False
            except ValueError:
                print(f"✓ Blocked path escape: {attempt}")

        # Test absolute path (should be treated as relative to workspace)
        try:
            backend._validate_path("/absolute/path.txt")
            print("✓ Absolute path treated as relative: /absolute/path.txt")
        except ValueError as e:
            print(f"✗ Absolute path handling failed: {e}")
            return False

    print()
    return True


def test_filesystem_operations():
    """Test basic filesystem operations through backend."""
    print("=" * 60)
    print("Testing Filesystem Operations")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        backend = WorkspaceFilesystemBackend(workspace=workspace)

        # Create a test file
        test_file = workspace / "test.txt"
        test_content = "Hello from Milestone 2!"
        test_file.write_text(test_content)

        # Test read validation
        try:
            backend.validate_operation("test.txt", "read")
            print("✓ Read operation validated for existing file")
        except ValueError as e:
            print(f"✗ Read validation failed: {e}")
            return False

        # Test write validation
        try:
            backend.validate_operation("new_file.txt", "write")
            print("✓ Write operation validated for new file")
        except ValueError as e:
            print(f"✗ Write validation failed: {e}")
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
    """Test symlink security (prevent symlink escape)."""
    print("=" * 60)
    print("Testing Symlink Security")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        backend = WorkspaceFilesystemBackend(workspace=workspace)

        # Create an outside directory
        outside_dir = Path(tmpdir).parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        outside_file = outside_dir / "secret.txt"
        outside_file.write_text("secret data")

        try:
            # Create symlink pointing outside workspace
            symlink = workspace / "link_to_outside"
            symlink.symlink_to(outside_file)

            # Try to access via symlink (should fail)
            try:
                backend._validate_path("link_to_outside")
                print("✗ Symlink escape not blocked")
                return False
            except ValueError:
                print("✓ Blocked symlink escape to outside file")

        except Exception as e:
            print(f"⚠ Symlink test skipped (not supported on this system): {e}")

        finally:
            # Cleanup
            if outside_dir.exists():
                outside_file.unlink(missing_ok=True)
                outside_dir.rmdir()

    print()
    return True


def test_integration_check():
    """Check if dependencies are available for full agent test."""
    print("=" * 60)
    print("Checking Integration Dependencies")
    print("=" * 60)

    missing = []

    try:
        import deepagents
        print("✓ deepagents available")
    except ImportError:
        print("✗ deepagents not installed")
        missing.append("deepagents")

    try:
        import langgraph
        print("✓ langgraph available")
    except ImportError:
        print("✗ langgraph not installed")
        missing.append("langgraph")

    try:
        import langchain
        print("✓ langchain available")
    except ImportError:
        print("✗ langchain not installed")
        missing.append("langchain")

    if missing:
        print(f"\n⚠ Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        print("\nBasic tests passed, but agent integration requires dependencies.")
    else:
        print("\n✓ All dependencies available for agent integration")

    print()
    return len(missing) == 0


def main():
    """Run all Milestone 2 tests."""
    print("\n🧪 Milestone 2 - Testing Filesystem Sandbox\n")

    results = []

    # Run tests
    results.append(("Backend Initialization", test_backend_initialization()))
    results.append(("Path Validation", test_path_validation()))
    results.append(("Filesystem Operations", test_filesystem_operations()))
    results.append(("Symlink Security", test_symlink_security()))
    
    # Check integration dependencies
    deps_available = test_integration_check()

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("✅ All Milestone 2 core tests passed!")
        
        if deps_available:
            print("\n✓ Ready to test agent integration")
            print("  Run: python3 test_milestone2_agent.py")
        else:
            print("\n⚠ Install dependencies for full agent testing:")
            print("  pip install -r requirements.txt")
    else:
        print("❌ Some tests failed")
        sys.exit(1)

    print()


if __name__ == "__main__":
    main()

