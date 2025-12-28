"""Orphaned file detection for files not tracked by any torrent."""

import os
import pathlib

from transmission_rpc import Client


def scan_directory(
    directory: pathlib.Path,
    include_hidden: bool = False,
) -> list[pathlib.Path]:
    """Scan a directory for all files.

    Args:
        directory: Directory path to scan
        include_hidden: Whether to include hidden files (files starting with .)

    Returns:
        List of file paths found in the directory and subdirectories
    """
    files: list[pathlib.Path] = []

    # System files to always exclude
    system_files = {".DS_Store", "Thumbs.db", "desktop.ini", ".directory"}

    # Recursively walk the directory (don't follow symlinks)
    for root, dirs, filenames in os.walk(directory, followlinks=False):
        root_path = pathlib.Path(root)

        # Remove symlink directories from dirs to prevent descending into them
        dirs[:] = [d for d in dirs if not (root_path / d).is_symlink()]

        for filename in filenames:
            item = root_path / filename

            if (
                # Skip symlinks to prevent scanning outside directory
                item.is_symlink()
                # Skip system files
                or filename in system_files
                # Skip torrent files (case-insensitive)
                or item.suffix.lower() == ".torrent"
                # Skip hidden files unless explicitly included
                or (not include_hidden and filename.startswith("."))
            ):
                continue

            files.append(item)

    return files


def get_tracked_files(client: Client) -> set[pathlib.Path]:
    """Get all files tracked by torrents in the Transmission client.

    Args:
        client: Transmission RPC client

    Returns:
        Set of file paths tracked by at least one torrent
    """
    tracked: set[pathlib.Path] = set()

    # Get all torrents
    torrents = client.get_torrents()

    # Collect all files from all torrents
    for torrent in torrents:
        for file in torrent.get_files():
            file_path = pathlib.Path(torrent.download_dir) / file.name
            # Resolve to absolute path for consistent comparison
            try:
                tracked.add(file_path.resolve())
            except (OSError, RuntimeError):
                # Handle broken symlinks or permission issues
                tracked.add(file_path)

    return tracked


def find_orphaned_files(
    scanned_files: list[pathlib.Path],
    tracked_files: set[pathlib.Path],
) -> list[pathlib.Path]:
    """Find files that are not tracked by any torrent.

    Args:
        scanned_files: List of files found in directory scan
        tracked_files: Set of files tracked by torrents

    Returns:
        List of orphaned files (in scanned but not in tracked)
    """
    orphaned: list[pathlib.Path] = []

    for file_path in scanned_files:
        # Resolve to absolute path for comparison
        try:
            resolved_path = file_path.resolve()
        except (OSError, RuntimeError):
            # If we can't resolve, use as-is
            resolved_path = file_path

        if resolved_path not in tracked_files:
            orphaned.append(file_path)

    return orphaned
