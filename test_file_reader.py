"""
Test suite for file_reader module.

Tests verify that the file reader properly handles:
1. Normal file reads within the base directory (should work)
2. Path traversal attacks trying to escape the base directory (should be blocked)
3. Absolute path attacks (should be blocked)
"""

import os
import tempfile
import shutil
import pytest

from file_reader import read_file


@pytest.fixture
def test_dir():
    """Create a temporary directory structure for tests."""
    tmpdir = tempfile.mkdtemp()

    # Create a safe directory with files
    safe_dir = os.path.join(tmpdir, "safe_files")
    os.makedirs(safe_dir)

    # Create a safe file inside
    with open(os.path.join(safe_dir, "allowed.txt"), "w") as f:
        f.write("This is an allowed file")

    # Create a subfolder with a file
    subdir = os.path.join(safe_dir, "subfolder")
    os.makedirs(subdir)
    with open(os.path.join(subdir, "nested.txt"), "w") as f:
        f.write("This is a nested file")

    # Create a sensitive file OUTSIDE the safe directory
    with open(os.path.join(tmpdir, "secret.txt"), "w") as f:
        f.write("SECRET: This should not be accessible!")

    yield tmpdir, safe_dir

    shutil.rmtree(tmpdir, ignore_errors=True)


def test_normal_file_read(test_dir):
    """Test that normal files within the base directory can be read."""
    tmpdir, safe_dir = test_dir

    content = read_file(safe_dir, "allowed.txt")

    assert content == "This is an allowed file"


def test_nested_file_read(test_dir):
    """Test that files in subdirectories can be read."""
    tmpdir, safe_dir = test_dir

    content = read_file(safe_dir, "subfolder/nested.txt")

    assert content == "This is a nested file"


def test_path_traversal_blocked(test_dir):
    """
    Test that path traversal attacks are blocked.

    This test will FAIL with the vulnerable code and PASS after the fix.
    CWE-22: Path Traversal vulnerability allows escaping the base directory.
    """
    tmpdir, safe_dir = test_dir

    # Try to read the secret file using path traversal
    try:
        content = read_file(safe_dir, "../secret.txt")

        # If we got here, the read succeeded - check if we got the secret
        if "SECRET" in content:
            pytest.fail(
                "VULNERABILITY DETECTED! Path traversal attack succeeded. "
                "The file reader accessed ../secret.txt outside the base directory. "
                "This is CWE-22: Path Traversal vulnerability."
            )
        # If we read something but not the secret, that's also a problem
        pytest.fail(
            "VULNERABILITY DETECTED! Path traversal was not blocked. "
            "The function should raise an error or sanitize the path."
        )
    except (ValueError, PermissionError, FileNotFoundError) as e:
        # If an appropriate exception was raised, the fix is working
        error_msg = str(e).lower()
        if "path" in error_msg or "traversal" in error_msg or "invalid" in error_msg or "outside" in error_msg:
            # Good - the fix detected and blocked the attack
            pass
        elif isinstance(e, FileNotFoundError):
            # This might mean the path was sanitized to something that doesn't exist
            # Check that it wasn't actually the secret file
            # This is acceptable if the path was sanitized
            pass
        else:
            # Some other error - re-raise to see what happened
            raise


def test_absolute_path_blocked(test_dir):
    """
    Test that absolute paths are blocked.

    This test will FAIL with the vulnerable code and PASS after the fix.
    """
    tmpdir, safe_dir = test_dir
    secret_path = os.path.join(tmpdir, "secret.txt")

    # Try to read using an absolute path
    try:
        content = read_file(safe_dir, secret_path)

        # If we got here, the read succeeded
        if "SECRET" in content:
            pytest.fail(
                "VULNERABILITY DETECTED! Absolute path attack succeeded. "
                f"The file reader accessed {secret_path} using an absolute path. "
                "This is CWE-22: Path Traversal vulnerability."
            )
        pytest.fail(
            "VULNERABILITY DETECTED! Absolute path was not blocked. "
            "The function should reject absolute paths."
        )
    except (ValueError, PermissionError, FileNotFoundError) as e:
        # If an appropriate exception was raised, the fix is working
        error_msg = str(e).lower()
        if "path" in error_msg or "absolute" in error_msg or "invalid" in error_msg or "outside" in error_msg:
            # Good - the fix detected and blocked the attack
            pass
        elif isinstance(e, FileNotFoundError):
            # Might be sanitized - that's OK
            pass
        else:
            # Some other error
            raise


def test_nonexistent_file(test_dir):
    """Test that reading a nonexistent file raises an error."""
    tmpdir, safe_dir = test_dir

    with pytest.raises(FileNotFoundError):
        read_file(safe_dir, "nonexistent.txt")
