"""
Helper utilities for Joblet SDK

Provides convenient functions for common operations like file uploads.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def upload(
    local_path: Union[str, Path],
    remote_path: Optional[str] = None,
    mode: Optional[int] = None,
    pattern: str = "**/*",
    exclude: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Create upload dicts from a local file or directory (auto-detects)

    Automatically detects whether the path is a file or directory and
    handles it appropriately.

    Args:
        local_path: Path to the local file or directory to upload
        remote_path: Destination path on remote (defaults to filename/dirname)
        mode: Unix file permissions (auto-detects if not specified, only for files)
        pattern: Glob pattern for files to include (default: all files,
            only for directories)
        exclude: List of patterns to exclude (only for directories)

    Returns:
        List of upload dicts ready for use in run_job(uploads=[...])

    Example:
        >>> job = client.jobs.run_job(
        ...     command="python",
        ...     args=["main.py"],
        ...     uploads=[
        ...         *upload("./script.py"),                    # single file
        ...         *upload("./data", exclude=["*.pyc"]),      # directory
        ...     ]
        ... )
    """
    path = Path(local_path)
    exclude = exclude or []

    if not path.exists():
        raise FileNotFoundError(f"Path not found: {local_path}")

    if path.is_dir():
        # Handle directory upload
        if remote_path is None:
            remote_path = path.name

        uploads = []

        # Create the base directory
        uploads.append(
            {
                "path": remote_path,
                "content": b"",
                "mode": 0o755,
                "is_directory": True,
            }
        )

        # Walk directory and add files
        for file_path in path.glob(pattern):
            if not file_path.is_file():
                continue

            # Check exclusions
            relative = file_path.relative_to(path)
            skip = False
            for exc in exclude:
                if relative.match(exc) or any(p.match(exc) for p in relative.parents):
                    skip = True
                    break
            if skip:
                continue

            # Read file
            with open(file_path, "rb") as f:
                content = f.read()

            # Determine mode
            if os.access(file_path, os.X_OK):
                file_mode = 0o755
            else:
                file_mode = 0o644

            uploads.append(
                {
                    "path": str(Path(remote_path) / relative),
                    "content": content,
                    "mode": file_mode,
                    "is_directory": False,
                }
            )

        return uploads
    else:
        # Handle single file upload
        with open(path, "rb") as f:
            content = f.read()

        if remote_path is None:
            remote_path = path.name

        if mode is None:
            if os.access(path, os.X_OK):
                mode = 0o755
            else:
                mode = 0o644

        return [
            {
                "path": remote_path,
                "content": content,
                "mode": mode,
                "is_directory": False,
            }
        ]


def upload_string(
    content: str,
    remote_path: str,
    mode: int = 0o644,
    encoding: str = "utf-8",
) -> Dict[str, Any]:
    """Create an upload dict from a string

    Useful for creating files on-the-fly without writing to disk.

    Args:
        content: String content for the file
        remote_path: Destination path on remote
        mode: Unix file permissions (default: 0o644)
        encoding: String encoding (default: utf-8)

    Returns:
        Dict ready for use in run_job(uploads=[...])

    Example:
        >>> script = '''
        ... import sys
        ... print(f"Hello, {sys.argv[1]}!")
        ... '''
        >>> job = client.jobs.run_job(
        ...     command="python",
        ...     args=["greet.py", "World"],
        ...     uploads=[upload_string(script, "greet.py", mode=0o755)]
        ... )
    """
    return {
        "path": remote_path,
        "content": content.encode(encoding),
        "mode": mode,
        "is_directory": False,
    }


def upload_bytes(
    content: bytes,
    remote_path: str,
    mode: int = 0o644,
) -> Dict[str, Any]:
    """Create an upload dict from bytes

    Useful for binary data or pre-read file contents.

    Args:
        content: Bytes content for the file
        remote_path: Destination path on remote
        mode: Unix file permissions (default: 0o644)

    Returns:
        Dict ready for use in run_job(uploads=[...])
    """
    return {
        "path": remote_path,
        "content": content,
        "mode": mode,
        "is_directory": False,
    }


def create_directory(remote_path: str, mode: int = 0o755) -> Dict[str, Any]:
    """Create a directory on the remote

    Args:
        remote_path: Path of the directory to create
        mode: Unix directory permissions (default: 0o755)

    Returns:
        Dict ready for use in run_job(uploads=[...])

    Example:
        >>> job = client.jobs.run_job(
        ...     command="ls",
        ...     args=["-la", "output"],
        ...     uploads=[create_directory("output")]
        ... )
    """
    return {
        "path": remote_path,
        "content": b"",
        "mode": mode,
        "is_directory": True,
    }
