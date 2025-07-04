from pathlib import Path


def list_sub_folders(level: int,
                     name: str,
                     start_path: Path | None = None) -> list[Path]:
    r"""Search through subdirectories up to the specified
    level for files/folders matching the name.

    Args:
        level (int): Number of subdirectory levels to search
            (0 means only current directory).
        name (str): Name of file or folder to search for.
        start_path (Optional[Path]): Starting path for search
            (defaults to current working directory).

    Returns:
        List of Path objects matching the name.

    Example:
        # Search 2 levels deep for config files
        matches = list_sub_folders(2, ".traceroot-config.yaml")
    """
    if start_path is None:
        start_path = Path.cwd()

    matches = []

    def _search_level(current_path: Path, current_level: int):
        if current_level > level:
            return

        try:
            for item in current_path.iterdir():
                if item.name == name:
                    matches.append(item)

                if item.is_dir() and current_level < level:
                    _search_level(item, current_level + 1)
        except (OSError, PermissionError):
            # Skip directories we can't access
            pass

    _search_level(start_path, 0)
    return matches


def list_parent_folders(level: int,
                        name: str,
                        start_path: Path | None = None) -> list[Path]:
    r"""Search through parent directories up to the specified
    level for files/folders matching the name.

    Args:
        level (int): Number of parent directory levels to search
            (0 means only current directory).
        name (str): Name of file or folder to search for.
        start_path (Optional[Path]): Starting path for search
            (defaults to current working directory).

    Returns:
        List of Path objects matching the name

    Example:
        # Search up 3 parent directories for config files
        matches = list_parent_folders(3, ".traceroot-config.yaml")
    """
    if start_path is None:
        start_path = Path.cwd()

    matches = []
    current_path = start_path

    for i in range(level + 1):
        try:
            for item in current_path.iterdir():
                if item.name == name:
                    matches.append(item)
        except (OSError, PermissionError):
            # Skip directories we can't access
            pass

        # Move to parent directory
        if i < level:
            parent = current_path.parent
            if parent == current_path:  # Reached filesystem root
                break
            current_path = parent

    return matches
