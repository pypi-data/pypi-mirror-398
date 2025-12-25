"""Simple test script for Milestone 1 - no external deps needed."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from deepagent_runner.config import SystemInfo, WorkspaceConfig, get_default_model


def test_system_detection():
    """Test OS and shell detection."""
    print("=" * 60)
    print("Testing System Detection")
    print("=" * 60)

    system_info = SystemInfo.detect()

    print(f"OS Type: {system_info.os_type.value}")
    print(f"Available Shells: {[s.value for s in system_info.available_shells]}")
    print(f"Preferred Shell: {system_info.preferred_shell.value if system_info.preferred_shell else 'None'}")

    assert system_info.os_type is not None
    print("✓ System detection works!\n")


def test_workspace_validation():
    """Test workspace path validation."""
    print("=" * 60)
    print("Testing Workspace Validation")
    print("=" * 60)

    # Test valid workspace (current directory)
    try:
        config = WorkspaceConfig(path=Path.cwd())
        print(f"✓ Valid workspace: {config.path}")
    except ValueError as e:
        print(f"✗ Failed to validate current directory: {e}")
        sys.exit(1)

    # Test invalid workspace
    try:
        config = WorkspaceConfig(path=Path("/nonexistent/path/that/does/not/exist"))
        print("✗ Should have failed for non-existent path")
        sys.exit(1)
    except ValueError as e:
        print(f"✓ Correctly rejected invalid path: {e}")

    print()


def test_model_config():
    """Test model configuration."""
    print("=" * 60)
    print("Testing Model Configuration")
    print("=" * 60)

    default_model = get_default_model()
    print(f"Default model: {default_model}")

    # Test valid model format
    try:
        config = WorkspaceConfig(path=Path.cwd(), model="openai:gpt-4o")
        print(f"✓ Valid model format: {config.model}")
    except ValueError as e:
        print(f"✗ Failed with valid model: {e}")
        sys.exit(1)

    # Test invalid model format
    try:
        config = WorkspaceConfig(path=Path.cwd(), model="invalid-format")
        print("✗ Should have failed for invalid model format")
        sys.exit(1)
    except ValueError as e:
        print(f"✓ Correctly rejected invalid model format: {e}")

    print()


def main():
    """Run all tests."""
    print("\n🧪 Milestone 1 - Testing Skeleton Components\n")

    try:
        test_system_detection()
        test_workspace_validation()
        test_model_config()

        print("=" * 60)
        print("✅ All Milestone 1 tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure .env file with OPENAI_API_KEY")
        print("3. Run: deepagent-runner check")
        print()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

