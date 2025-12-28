import argparse
import signal
import sys

from transmission_cleaner.actions import process_torrents
from transmission_cleaner.client import create_client, get_client_config
from transmission_cleaner.filters import filter_torrents


def signal_handler(signal, frame):
    print("[INFO]   Graceful exit 🦢")
    sys.exit(0)


def add_common_auth_args(parser):
    """Add common authentication arguments to a parser."""
    auth_group = parser.add_argument_group("authentication")
    auth_group.add_argument(
        "--settings-file",
        type=str,
        help="Path to Transmission settings.json file",
    )
    auth_group.add_argument(
        "--protocol", choices=["http", "https"], default="http", help="Protocol to use (default: http)"
    )
    auth_group.add_argument("--username", type=str, help="Transmission username")
    auth_group.add_argument("--password", required=True, type=str, help="Transmission password")
    auth_group.add_argument("--host", type=str, default="127.0.0.1", help="Transmission host (default: 127.0.0.1)")
    auth_group.add_argument("--port", type=int, default=9091, help="Transmission port (default: 9091)")
    auth_group.add_argument(
        "--rpc-path", type=str, default="/transmission/rpc", help="Transmission RPC path (default: /transmission/rpc)"
    )


def add_common_filter_args(parser):
    """Add common filter arguments to a parser."""
    parser.add_argument(
        "-d",
        "--dir",
        "--directory",
        dest="directory",
        type=str,
        help="Filter torrents by download directory (substring match)",
    )
    parser.add_argument(
        "-t",
        "--tracker",
        type=str,
        help="Filter torrents by announce URL (substring match)",
    )
    parser.add_argument(
        "--min-days",
        type=int,
        default=7,
        help="Minimum days of active seeding time (default: 7)",
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transmission maintenance tool for hardlinks, errors, and orphaned files",
        epilog="Note: All commands require authentication (--password). Use 'transmission-cleaner <command> --help' for command-specific options.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Hardlinks subcommand
    hardlinks_parser = subparsers.add_parser(
        "hardlinks", help="Find and manage torrents without hardlinks to other files"
    )
    add_common_filter_args(hardlinks_parser)
    hardlinks_parser.add_argument(
        "--action",
        choices=["list", "l", "interactive", "i", "delete", "d", "remove", "r"],
        default="list",
        help=(
            "Action to perform (default: list) | "
            "list/l: show torrents only | "
            "interactive/i: prompt for each torrent | "
            "delete/d: remove torrent with data | "
            "remove/r: remove torrent from client only"
        ),
    )
    add_common_auth_args(hardlinks_parser)

    # Errors subcommand
    errors_parser = subparsers.add_parser("errors", help="Find and manage torrents with error status")
    add_common_filter_args(errors_parser)
    errors_parser.add_argument(
        "--error-pattern",
        type=str,
        help="Filter by error message pattern (e.g., 'Unregistered')",
    )
    errors_parser.add_argument(
        "--skip-cross-seed",
        action="store_true",
        help="Skip cross-seed detection (allow data deletion even if cross-seeded)",
    )
    errors_parser.add_argument(
        "--action",
        choices=["list", "l", "interactive", "i", "delete", "d", "remove", "r"],
        default="list",
        help=(
            "Action to perform (default: list) | "
            "list/l: show torrents only | "
            "interactive/i: prompt for each torrent | "
            "delete/d: remove torrent with data (respects cross-seed check) | "
            "remove/r: remove torrent from client only"
        ),
    )
    add_common_auth_args(errors_parser)

    # Orphans subcommand
    orphans_parser = subparsers.add_parser("orphans", help="Find and manage files not tracked by any torrent")
    orphans_parser.add_argument(
        "-d",
        "--dir",
        "--directory",
        dest="directory",
        type=str,
        required=True,
        help="Directory to scan for orphaned files",
    )
    orphans_parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files (files starting with .)",
    )
    orphans_parser.add_argument(
        "--action",
        choices=["list", "l", "interactive", "i", "delete", "d"],
        default="list",
        help=(
            "Action to perform (default: list) | "
            "list/l: show files only | "
            "interactive/i: prompt for each file | "
            "delete/d: remove orphaned files"
        ),
    )
    add_common_auth_args(orphans_parser)

    args = parser.parse_args()

    # If no subcommand provided, show help
    if not args.command:
        parser.print_help()
        sys.exit(1)

    return args


def handle_hardlinks(client, args):
    """Handle the hardlinks subcommand."""

    from transmission_cleaner.checkers.hardlinks import get_torrents_without_hardlinks

    torrents = client.get_torrents()
    print(f"[INFO]   Found {len(torrents)} torrents")

    torrents = filter_torrents(torrents, args.directory, args.tracker, args.min_days)
    without_hardlinks = get_torrents_without_hardlinks(torrents)

    print(f"[INFO]   Found {len(without_hardlinks)} torrents without hardlinks")

    # Normalize action for interactive mode
    action = args.action if args.action not in ["interactive", "i"] else None
    bytes_freed = process_torrents(client, without_hardlinks, action)

    # Print summary if any space was freed
    if bytes_freed > 0:
        space_freed_gb = bytes_freed / (1024**3)
        print(f"\n[INFO]   Total disk space freed: {space_freed_gb:.2f} GB")


def handle_errors(client, args):
    """Handle the errors subcommand."""
    from transmission_cleaner.checkers.errors import check_cross_seeding, get_torrents_with_errors

    torrents = client.get_torrents()
    print(f"[INFO]   Found {len(torrents)} torrents")

    torrents = filter_torrents(torrents, args.directory, args.tracker, args.min_days)
    errored_torrents = get_torrents_with_errors(torrents, args.error_pattern)

    print(f"[INFO]   Found {len(errored_torrents)} torrents with errors")

    # Process with cross-seed awareness
    check_cross_seed = not args.skip_cross_seed
    action = args.action if args.action not in ["interactive", "i"] else None

    # Build cross-seed map
    cross_seed_map = {}
    if check_cross_seed:
        print("[INFO]   Checking for cross-seeded torrents...")
        for torrent in errored_torrents:
            cross_seeders = check_cross_seeding(client, torrent)
            if cross_seeders:
                cross_seed_map[torrent.id] = cross_seeders
                print(f"[CROSS-SEED] {torrent.name}")
                print(f"             Shared with: {', '.join(t.name for t in cross_seeders)}")
    else:
        print("[INFO]   Skipping cross-seed checks")

    # Process torrents with cross-seed protection using shared action processor
    bytes_freed = process_torrents(client, errored_torrents, action, cross_seed_map=cross_seed_map)

    # Print summary if any space was freed
    if bytes_freed > 0:
        space_freed_gb = bytes_freed / (1024**3)
        print(f"\n[INFO]   Total disk space freed: {space_freed_gb:.2f} GB")


def handle_orphans(client, args):
    """Handle the orphans subcommand."""
    import pathlib

    from transmission_cleaner.actions import process_orphaned_files
    from transmission_cleaner.checkers.orphans import find_orphaned_files, get_tracked_files, scan_directory

    directory = pathlib.Path(args.directory)
    if not directory.exists():
        print(f"[ERROR]  Directory not found: {directory}")
        sys.exit(1)

    print(f"[INFO]   Scanning directory: {directory}")
    scanned_files = scan_directory(directory, args.include_hidden)
    print(f"[INFO]   Found {len(scanned_files)} files")

    print("[INFO]   Getting tracked files from Transmission...")
    tracked_files = get_tracked_files(client)
    print(f"[INFO]   {len(tracked_files)} files tracked by torrents")

    orphaned = find_orphaned_files(scanned_files, tracked_files)
    print(f"[INFO]   Found {len(orphaned)} orphaned files")

    # Process orphaned files
    action = args.action if args.action not in ["interactive", "i"] else None
    bytes_freed = process_orphaned_files(orphaned, action)

    # Print summary if any space was freed
    if bytes_freed > 0:
        space_freed_gb = bytes_freed / (1024**3)
        print(f"\n[INFO]   Total disk space freed: {space_freed_gb:.2f} GB")


def main():
    args = parse_args()

    # Create Transmission client (shared by all commands)
    client_config = get_client_config(
        settings_file=args.settings_file,
        protocol=args.protocol,
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        path=args.rpc_path,
    )
    client = create_client(**client_config)

    # Dispatch to appropriate handler
    if args.command == "hardlinks":
        handle_hardlinks(client, args)
    elif args.command == "errors":
        handle_errors(client, args)
    elif args.command == "orphans":
        handle_orphans(client, args)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
