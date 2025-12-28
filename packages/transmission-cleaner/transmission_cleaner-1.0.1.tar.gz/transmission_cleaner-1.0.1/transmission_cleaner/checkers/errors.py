"""Error status and cross-seed detection for torrents."""

import pathlib

from transmission_rpc import Client, Torrent


def get_torrents_with_errors(
    torrents: list[Torrent],
    error_pattern: str | None = None,
) -> list[Torrent]:
    """Find torrents with error status.

    Args:
        torrents: List of torrents to check
        error_pattern: Optional pattern to match in error string (e.g., "Unregistered")

    Returns:
        List of torrents with errors matching the pattern (or any error if no pattern)
    """
    errored_torrents: list[Torrent] = []

    for torrent in sorted(torrents, key=lambda t: t.name):
        # Check if torrent has an error
        error_string = getattr(torrent, "error_string", "") or getattr(torrent, "error", "")

        if error_string:
            # If pattern provided, check if it matches
            if error_pattern:
                if error_pattern.lower() in error_string.lower():
                    errored_torrents.append(torrent)
            else:
                # No pattern - include all errors
                errored_torrents.append(torrent)

    return errored_torrents


def check_cross_seeding(client: Client, torrent: Torrent) -> list[Torrent]:
    """Check if a torrent's files are cross-seeded by other torrents.

    Args:
        client: Transmission RPC client
        torrent: Torrent to check for cross-seeding

    Returns:
        List of other torrents that share files with this torrent
    """
    cross_seeders: list[Torrent] = []

    # Get all files from the target torrent
    target_files = set()
    for file in torrent.get_files():
        file_path = pathlib.Path(torrent.download_dir) / file.name
        target_files.add(file_path)

    # Get all other torrents
    all_torrents = client.get_torrents()

    for other_torrent in all_torrents:
        # Skip the same torrent
        if other_torrent.id == torrent.id:
            continue

        # Check if any files overlap
        for file in other_torrent.get_files():
            other_file_path = pathlib.Path(other_torrent.download_dir) / file.name
            if other_file_path in target_files:
                cross_seeders.append(other_torrent)
                break  # Found overlap, no need to check more files

    return cross_seeders


def is_cross_seeded(client: Client, torrent: Torrent) -> bool:
    """Check if a torrent is cross-seeded by any other torrent.

    Args:
        client: Transmission RPC client
        torrent: Torrent to check

    Returns:
        True if any other torrent shares files with this torrent
    """
    cross_seeders = check_cross_seeding(client, torrent)
    return len(cross_seeders) > 0
