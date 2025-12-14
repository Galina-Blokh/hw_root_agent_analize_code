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
        ValueError: If an invalid path is provided
    """
    # Resolve the base directory to an absolute path
    base_dir = os.path.abspath(base_dir)
    
    # Resolve the file path within the base directory
    file_path = os.path.abspath(os.path.join(base_dir, filename))
    
    # Ensure the file path is within the base directory
    if not file_path.startswith(base_dir + os.path.sep):
        raise ValueError("Invalid file path: path traversal attempt detected")

    with open(file_path, 'r') as f:
        return f.read()