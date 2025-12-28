"""Torrent and file action processing functionality."""

import pathlib
from collections.abc import Mapping, Sequence

from transmission_rpc import Client, Torrent


def process_torrents(
    client: Client,
    torrents: Sequence[Torrent],
    action: str | None,
    cross_seed_map: Mapping[int, Sequence[Torrent]] | None = None,
) -> int:
    """Process torrents based on the specified action.

    Args:
        client: Transmission RPC client
        torrents: List of torrents to process
        action: Action to perform - None (interactive), "list"/"l", "delete"/"d", "remove"/"r"
        cross_seed_map: Optional dict mapping torrent IDs to list of cross-seeding torrents.
                       If provided, protects cross-seeded torrents from data deletion.

    Returns:
        Total bytes freed (only counts data that was actually deleted)
    """
    cross_seed_map = cross_seed_map or {}
    total_space_freed = 0

    # Handle action based on argument
    if action in ["list", "l"]:
        for torrent in torrents:
            cross_status = " [CROSS-SEEDED]" if torrent.id in cross_seed_map else ""
            size_gb = torrent.total_size / (1024**3)
            print(f"  - {torrent.name}{cross_status} ({size_gb:.2f} GB)")

    elif action in ["delete", "d"]:
        for torrent in torrents:
            if torrent.id in cross_seed_map:
                # Cross-seeded: protect data, remove torrent only
                print(f"[PROTECTED] {torrent.name}: Cross-seeded, removing torrent only (keeping data)")
                client.remove_torrent(torrent.id, delete_data=False)
            else:
                # Not cross-seeded: safe to delete data
                size_gb = torrent.total_size / (1024**3)
                print(f"[ACTION] {torrent.name}: Removing with data ({size_gb:.2f} GB)")
                client.remove_torrent(torrent.id, delete_data=True)
                total_space_freed += torrent.total_size

    elif action in ["remove", "r"]:
        for torrent in torrents:
            print(f"[ACTION] {torrent.name}: Removing without data")
            client.remove_torrent(torrent.id, delete_data=False)

    elif action in ["interactive", "i", None]:
        # Interactive mode
        for torrent in torrents:
            cross_status = " [CROSS-SEEDED]" if torrent.id in cross_seed_map else ""
            choice = (
                input(f"[PROMPT] {torrent.name}{cross_status}\n         Remove torrent? [N(o)/r(emove)/d(ata)] ")
                .strip()
                .lower()
                or "n"
            )

            if choice == "r":
                print(f"[ACTION] {torrent.name}: Removing without data")
                client.remove_torrent(torrent.id, delete_data=False)
            elif choice == "d":
                if torrent.id in cross_seed_map:
                    # Cross-seeded: protect data even if user wants to delete
                    print(f"[PROTECTED] {torrent.name}: Cross-seeded, removing torrent only (keeping data)")
                    client.remove_torrent(torrent.id, delete_data=False)
                else:
                    # Not cross-seeded: safe to delete data
                    size_gb = torrent.total_size / (1024**3)
                    print(f"[ACTION] {torrent.name}: Removing with data ({size_gb:.2f} GB)")
                    client.remove_torrent(torrent.id, delete_data=True)
                    total_space_freed += torrent.total_size
            else:
                print("[SKIP]   Skipped")

    return total_space_freed


def process_orphaned_files(
    orphaned_files: Sequence[pathlib.Path],
    action: str | None,
) -> int:
    """Process orphaned files based on the specified action.

    Args:
        orphaned_files: List of orphaned file paths to process
        action: Action to perform - None (interactive), "list"/"l", "delete"/"d"

    Returns:
        Total bytes freed (only counts files that were actually deleted)
    """
    total_space_freed = 0

    if action in ["list", "l"]:
        for file_path in sorted(orphaned_files):
            try:
                size = file_path.stat().st_size if file_path.exists() else 0
                size_mb = size / (1024 * 1024)
                print(f"  - {file_path} ({size_mb:.2f} MB)")
            except (OSError, PermissionError) as e:
                print(f"  - {file_path} [ERROR: {e}]")

    elif action in ["delete", "d"]:
        for file_path in orphaned_files:
            try:
                if file_path.exists():
                    size = file_path.stat().st_size
                    size_mb = size / (1024 * 1024)
                    print(f"[ACTION] Deleting: {file_path} ({size_mb:.2f} MB)")
                    file_path.unlink()
                    total_space_freed += size
                else:
                    print(f"[SKIP]   File no longer exists: {file_path}")
            except (OSError, PermissionError) as e:
                print(f"[ERROR]  Failed to delete {file_path}: {e}")

    else:  # interactive mode
        for file_path in orphaned_files:
            try:
                if not file_path.exists():
                    print(f"[SKIP]   File no longer exists: {file_path}")
                    continue
                size = file_path.stat().st_size
                size_mb = size / (1024 * 1024)
                choice = input(f"[PROMPT] {file_path} ({size_mb:.2f} MB)\n         Delete file? [y/N] ").strip().lower()
                if choice == "y":
                    print(f"[ACTION] Deleting: {file_path}")
                    file_path.unlink()
                    total_space_freed += size
                else:
                    print("[SKIP]   Skipped")
            except (OSError, PermissionError) as e:
                print(f"[ERROR]  Cannot process {file_path}: {e}")

    return total_space_freed
