import argparse
import json
import signal
import sys
import textwrap

# from traceback_with_variables import activate_by_import  # noqa: F401
from transmission_rpc import Client

from transmission_unlinked.core import filter_torrents, get_torrents_without_hardlinks, process_torrents


def signal_handler(signal, frame):
    print(" Graceful exit 🦢")
    sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser(description="Clean up Transmission torrents based on hardlink status")

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
        "--action",
        choices=[None, "list", "l", "delete", "d", "remove", "r"],
        default=None,
        help=textwrap.dedent(
            """Action to apply to torrents without any other hardlinks. Interactive by default
                list / l:       show torrents only
                delete / d:     remove torrent with data on disk
                remove / r:     remove torrent from client only
            """.replace("\n", " | ")
        ),
    )

    # Authentication group
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
        "--path", type=str, default="/transmission/rpc", help="Transmission RPC path (default: /transmission/rpc)"
    )

    return parser.parse_args()


def load_settings_from_file(settings_file: str, password: str) -> dict:
    """Load Transmission settings from settings.json file."""
    with open(settings_file, "r") as f:
        settings = json.load(f)

    return {
        "host": "127.0.0.1",
        "port": settings.get("rpc-port", 9091),
        "username": settings.get("rpc-username"),
        "password": password,
        "path": settings.get("rpc-url", "/transmission/rpc"),
    }


def get_client_config(args) -> dict:
    """Get client configuration from arguments or settings file."""
    if args.settings_file:
        return load_settings_from_file(args.settings_file, args.password)

    return {
        "protocol": args.protocol,
        "host": args.host,
        "port": args.port,
        "username": args.username,
        "password": args.password,
        "path": args.path,
    }


def main():
    args = parse_args()

    # Get client configuration
    client_config = get_client_config(args)
    c = Client(**client_config)

    torrents = c.get_torrents()
    print(f"Found {len(torrents)} torrents.")

    torrents = filter_torrents(torrents, args.directory, args.tracker)

    without_hardlinks = get_torrents_without_hardlinks(torrents)

    print(f"Found {len(without_hardlinks)} torrents without hardlinks")

    process_torrents(c, without_hardlinks, args.action)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    main()
