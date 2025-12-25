"""Hardlink detection for torrent files."""

import pathlib

from transmission_rpc import Torrent


def is_hardlink(path: pathlib.Path) -> bool:
    """Check if a file has multiple hardlinks.

    Args:
        path: Path to the file to check

    Returns:
        True if the file has more than one hardlink, False otherwise
    """
    return path.stat().st_nlink > 1


def get_torrents_without_hardlinks(torrents: list[Torrent]) -> list[Torrent]:
    """Find torrents that have no hardlinked files.

    Args:
        torrents: List of torrents to check

    Returns:
        List of torrents where none of the files have hardlinks
    """
    without_hardlinks: list[Torrent] = []

    for torrent in sorted(torrents, key=lambda t: t.name):
        has_hardlink = False
        for file in sorted(torrent.get_files()):
            file_path = pathlib.Path(torrent.download_dir) / file.name
            try:
                if is_hardlink(file_path):
                    has_hardlink = True
                    break
            except FileNotFoundError:
                print(f"[ERROR]  File not found: {file_path}")
                break
        else:
            if not has_hardlink:
                without_hardlinks.append(torrent)
    return without_hardlinks
