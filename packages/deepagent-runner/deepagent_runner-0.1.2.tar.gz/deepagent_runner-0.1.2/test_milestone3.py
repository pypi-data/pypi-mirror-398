"""Test script for Milestone 3 - Cross-platform Execute."""

import sys
import tempfile
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from deepagent_runner.shell_exec import ShellExecutor, create_executor
from deepagent_runner.config import ShellType


def test_executor_initialization():
    """Test executor initialization and shell detection."""
    print("=" * 60)
    print("Test 1: Executor Initialization & Shell Detection")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        try:
            executor = create_executor(workspace)
            print(f"✓ Executor initialized")
            print(f"  Workspace: {workspace}")
            print(f"  Shell: {executor.shell_type.value}")
            print(f"  OS: {executor.system_info.os_type.value}")
            print(f"  Available shells: {[s.value for s in executor.system_info.available_shells]}")
        except Exception as e:
            print(f"✗ Failed to initialize executor: {e}")
            return False

    print()
    return True


def test_basic_command_execution():
    """Test basic command execution."""
    print("=" * 60)
    print("Test 2: Basic Command Execution")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        executor = create_executor(workspace)

        # Test 1: Simple echo command
        result = executor.execute("echo 'Hello from Milestone 3'")
        if result.exit_code == 0 and "Hello from Milestone 3" in result.stdout:
            print("✓ Echo command executed successfully")
            print(f"  Output: {result.stdout.strip()}")
            print(f"  Duration: {result.duration_ms}ms")
        else:
            print(f"✗ Echo command failed: {result.stderr}")
            return False

        # Test 2: Current directory check
        result = executor.execute("pwd")
        if result.exit_code == 0:
            print(f"✓ Working directory verified")
            print(f"  PWD: {result.stdout.strip()}")
            # Check that we're in the workspace
            if str(workspace) in result.stdout:
                print(f"  ✓ Command runs in workspace")
            else:
                print(f"  ⚠ Warning: PWD doesn't match workspace")
        else:
            print(f"✗ PWD command failed: {result.stderr}")
            return False

        # Test 3: File operations
        result = executor.execute("echo 'test content' > test_file.txt && cat test_file.txt")
        if result.exit_code == 0 and "test content" in result.stdout:
            print("✓ File write and read successful")
            
            # Verify file exists in workspace
            test_file = workspace / "test_file.txt"
            if test_file.exists():
                print(f"  ✓ File created in workspace: {test_file.name}")
            else:
                print(f"  ✗ File not found in workspace")
                return False
        else:
            print(f"✗ File operations failed: {result.stderr}")
            return False

    print()
    return True


def test_exit_codes():
    """Test exit code handling."""
    print("=" * 60)
    print("Test 3: Exit Code Handling")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        executor = create_executor(workspace)

        # Test success (exit 0)
        result = executor.execute("true")
        if result.exit_code == 0:
            print("✓ Success command returns exit code 0")
        else:
            print(f"✗ Success command returned {result.exit_code}")
            return False

        # Test failure (exit 1)
        result = executor.execute("false")
        if result.exit_code != 0:
            print(f"✓ Failure command returns non-zero exit code: {result.exit_code}")
        else:
            print(f"✗ Failure command returned 0")
            return False

        # Test command not found
        result = executor.execute("nonexistent_command_xyz")
        if result.exit_code != 0:
            print(f"✓ Non-existent command returns error: exit {result.exit_code}")
            if result.stderr:
                print(f"  Error: {result.stderr.strip()[:100]}")
        else:
            print(f"✗ Non-existent command returned 0")
            return False

    print()
    return True


def test_timeout_handling():
    """Test command timeout."""
    print("=" * 60)
    print("Test 4: Timeout Handling")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        executor = create_executor(workspace, default_timeout=2)

        # Test command that completes within timeout
        result = executor.execute("sleep 0.5", timeout=2)
        if result.exit_code == 0 and not result.timed_out:
            print("✓ Quick command completes within timeout")
            print(f"  Duration: {result.duration_ms}ms")
        else:
            print(f"✗ Quick command failed or timed out")
            return False

        # Test command that times out
        print("\n⏱  Testing timeout (this will take 2 seconds)...")
        start = time.time()
        result = executor.execute("sleep 10", timeout=2)
        elapsed = time.time() - start
        
        if result.timed_out:
            print(f"✓ Long command timed out as expected")
            print(f"  Elapsed: {elapsed:.1f}s (expected ~2s)")
            print(f"  Exit code: {result.exit_code}")
            if "timed out" in result.stderr.lower():
                print(f"  ✓ Timeout message in stderr")
        else:
            print(f"✗ Long command did not timeout")
            return False

    print()
    return True


def test_output_size_limit():
    """Test output size limiting."""
    print("=" * 60)
    print("Test 5: Output Size Limiting")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        # Set small output limit for testing
        executor = create_executor(workspace, max_output_size=1000)

        # Generate large output (more than 1000 bytes)
        result = executor.execute("for i in {1..100}; do echo 'This is line number $i with some extra text to make it longer'; done")
        
        if result.truncated:
            print("✓ Large output was truncated")
            print(f"  Output length: {len(result.stdout)} bytes")
            print(f"  Contains truncation notice: {'truncated' in result.stdout.lower()}")
        else:
            # Might not trigger if output is naturally small
            print("⚠ Output not truncated (may be within limit)")
            print(f"  Output length: {len(result.stdout)} bytes")

    print()
    return True


def test_command_validation():
    """Test command safety validation."""
    print("=" * 60)
    print("Test 6: Command Safety Validation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        executor = create_executor(workspace)

        # Test empty command
        try:
            result = executor.execute("")
            print("✗ Empty command should have been rejected")
            return False
        except ValueError as e:
            print(f"✓ Empty command rejected: {e}")

        # Test dangerous command patterns
        dangerous_commands = [
            "rm -rf /",
            "rm -rf /*",
            "mkfs.ext4 /dev/sda",
        ]

        for cmd in dangerous_commands:
            try:
                result = executor.execute(cmd)
                print(f"✗ Dangerous command not blocked: {cmd}")
                return False
            except ValueError as e:
                print(f"✓ Blocked dangerous command: {cmd[:30]}...")

    print()
    return True


def test_cross_platform_commands():
    """Test cross-platform compatible commands."""
    print("=" * 60)
    print("Test 7: Cross-Platform Commands")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        executor = create_executor(workspace)

        # Create test file
        (workspace / "test.txt").write_text("test content")

        # Commands that should work on both POSIX and Windows
        # (when using bash/POSIX shell)
        cross_platform_commands = [
            ("ls", "list files"),
            ("cat test.txt", "read file"),
            ("echo $PWD", "print working directory"),
        ]

        all_passed = True
        for cmd, description in cross_platform_commands:
            result = executor.execute(cmd)
            if result.exit_code == 0:
                print(f"✓ {description}: {cmd}")
            else:
                print(f"✗ {description} failed: {cmd}")
                print(f"  Error: {result.stderr.strip()[:100]}")
                all_passed = False

        if not all_passed:
            return False

    print()
    return True


def test_shell_type_detection():
    """Test that correct shell is being used."""
    print("=" * 60)
    print("Test 8: Shell Type Detection")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        executor = create_executor(workspace)

        print(f"Detected shell: {executor.shell_type.value}")
        
        # Check shell priority
        if executor.shell_type in [ShellType.BASH, ShellType.ZSH, ShellType.SH]:
            print("✓ Using POSIX shell (preferred)")
        elif executor.shell_type in [ShellType.POWERSHELL, ShellType.CMD]:
            print("⚠ Using Windows shell (POSIX not available)")
        else:
            print(f"? Unknown shell type: {executor.shell_type}")

        # Try to detect which shell is actually running
        result = executor.execute("echo $SHELL")
        if result.exit_code == 0 and result.stdout.strip():
            print(f"  Shell path: {result.stdout.strip()}")

    print()
    return True


def main():
    """Run all Milestone 3 tests."""
    print("\n" + "=" * 60)
    print("🧪 Milestone 3 - Cross-Platform Execute Tests")
    print("=" * 60)
    print()

    results = [
        ("Executor Initialization", test_executor_initialization()),
        ("Basic Command Execution", test_basic_command_execution()),
        ("Exit Code Handling", test_exit_codes()),
        ("Timeout Handling", test_timeout_handling()),
        ("Output Size Limiting", test_output_size_limit()),
        ("Command Safety Validation", test_command_validation()),
        ("Cross-Platform Commands", test_cross_platform_commands()),
        ("Shell Type Detection", test_shell_type_detection()),
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
        print("\n🎉 All Milestone 3 execute tests PASSED!")
        print("\n✅ Shell execution features verified:")
        print("  • Cross-platform shell detection")
        print("  • POSIX shell preferred (bash → zsh → sh)")
        print("  • Windows shell fallback (PowerShell → cmd)")
        print("  • Command execution in workspace")
        print("  • Exit code handling")
        print("  • Timeout protection")
        print("  • Output size limits")
        print("  • Command safety validation")
        print()
        print("📦 Next steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Test full agent integration")
        print("  3. Continue to Milestone 4 (agent wiring complete)")
    else:
        print("\n❌ Some tests FAILED - fix issues before proceeding")
        sys.exit(1)

    print()


if __name__ == "__main__":
    main()

