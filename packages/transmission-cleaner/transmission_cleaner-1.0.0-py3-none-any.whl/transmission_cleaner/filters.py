"""Torrent filtering functionality."""

from transmission_rpc import Torrent


def filter_torrents(
    torrents: list[Torrent],
    dir: str | None,
    tracker: str | None,
    min_days: int = 7,
) -> list[Torrent]:
    """Filter torrents based on various criteria.

    Args:
        torrents: List of torrents to filter
        dir: Directory substring to match (optional)
        tracker: Tracker URL substring to match (optional)
        min_days: Minimum days of active seeding time

    Returns:
        Filtered list of torrents
    """
    # filter torrents to only have ones that are seeding or stopped
    torrents = [x for x in torrents if x.status == "seeding" or x.status == "stopped"]
    print(f"[FILTER] Filtered to {len(torrents)} seeding or stopped torrents")

    # Filter torrents by directory if specified
    if dir:
        torrents = [x for x in torrents if dir in str(x.download_dir)]
        print(f"[FILTER] Filtered to {len(torrents)} torrents in directory matching '{dir}'")

    # Filter torrents by tracker if specified
    if tracker:
        torrents = [x for x in torrents if any(tracker in t.announce for t in x.trackers)]
        print(f"[FILTER] Filtered to {len(torrents)} torrents with tracker matching '{tracker}'")

    if not dir and not tracker:
        print("[INFO]   No directory or tracker filters applied, processing all torrents")

    # Filter torrents by minimum seeding days
    min_seconds = min_days * 24 * 60 * 60
    torrents = [x for x in torrents if x.seconds_seeding >= min_seconds]
    print(f"[FILTER] Filtered to {len(torrents)} torrents with at least {min_days} days of active seeding")

    return torrents
