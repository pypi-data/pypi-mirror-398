from typing import Optional
from pathlib import Path


def find_directory_in_parent_dirs(dirname, start_path=None) -> Optional[Path]:
    """
    Recursively checks for a file in the current directory and its parent directories.

    Args:
        dirname (str): The name of the file to search for.
        start_path (str or Path, optional): The starting directory for the search.
                                            If None, the current working directory is used.

    Returns:
        Path or None: The absolute path to the file if found, otherwise None.
    """
    if start_path is None:
        current_dir = Path.cwd()
    else:
        current_dir = Path(start_path).resolve()

    while True:
        dir_path = current_dir / dirname 
        if dir_path.is_dir():
            return dir_path
        
        # If we've reached the root directory and the file isn't found, stop
        if current_dir == current_dir.parent:
            return None
        
        current_dir = current_dir.parent


def find_file_in_parent_dirs(filename, start_path=None) -> Optional[Path]:
    """
    Recursively checks for a file in the current directory and its parent directories.

    Args:
        filename (str): The name of the file to search for.
        start_path (str or Path, optional): The starting directory for the search.
                                            If None, the current working directory is used.

    Returns:
        Path or None: The absolute path to the file if found, otherwise None.
    """
    if start_path is None:
        current_dir = Path.cwd()
    else:
        current_dir = Path(start_path).resolve()

    while True:
        file_path = current_dir / filename
        if file_path.is_file():
            return file_path
        
        # Move up to the parent directory
        current_dir = current_dir.parent
        
        # If we've reached the root directory and the file isn't found, stop
        if current_dir == current_dir:
            return None
 