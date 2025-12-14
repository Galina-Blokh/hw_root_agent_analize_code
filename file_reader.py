"""
File reader utility for reading files from a designated directory.

This module provides functionality to read files from a specific base directory.
"""

import os


def read_file(base_dir, filename):
    """
    Read a file from the base directory.

    Args:
        base_dir (str): The base directory to read files from
        filename (str): The name of the file to read

    Returns:
        str: The contents of the file

    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If the file can't be read
        ValueError: If the filename is invalid or attempts path traversal
    """
    # Ensure the base directory is an absolute path
    base_dir = os.path.abspath(base_dir)

    # Validate and sanitize the filename
    safe_filename = os.path.normpath(filename)

    # Ensure the filename doesn't contain path traversal
    if os.path.isabs(safe_filename) or '..' in safe_filename.split(os.path.sep):
        raise ValueError("Invalid filename or path traversal attempt detected.")

    # Create the full path
    file_path = os.path.join(base_dir, safe_filename)

    # Ensure the file path is still within the base directory
    if not file_path.startswith(base_dir + os.path.sep):
        raise ValueError("Path traversal detected.")

    with open(file_path, 'r') as f:
        return f.read()