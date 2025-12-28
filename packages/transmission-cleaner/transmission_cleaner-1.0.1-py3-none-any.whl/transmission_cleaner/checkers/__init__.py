"""Checker modules for different torrent and file analysis operations."""

from transmission_cleaner.checkers.errors import check_cross_seeding, get_torrents_with_errors, is_cross_seeded
from transmission_cleaner.checkers.hardlinks import get_torrents_without_hardlinks, is_hardlink
from transmission_cleaner.checkers.orphans import find_orphaned_files, get_tracked_files, scan_directory

__all__ = [
    # Hardlinks
    "get_torrents_without_hardlinks",
    "is_hardlink",
    # Errors
    "get_torrents_with_errors",
    "check_cross_seeding",
    "is_cross_seeded",
    # Orphans
    "scan_directory",
    "get_tracked_files",
    "find_orphaned_files",
]
