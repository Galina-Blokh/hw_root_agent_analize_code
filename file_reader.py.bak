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
    """
    # VULNERABLE: Direct path concatenation without validation
    # This allows path traversal attacks like ../../../etc/passwd
    file_path = os.path.join(base_dir, filename)

    with open(file_path, 'r') as f:
        return f.read()