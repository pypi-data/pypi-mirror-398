import pathlib

from transmission_rpc import Client, Torrent


def is_hardlink(path: pathlib.Path) -> bool:
    return path.stat().st_nlink > 1


def get_torrents_without_hardlinks(torrents: list[Torrent]) -> list[Torrent]:
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
                print("FILE NOT FOUND!!\n -", file_path)
                break
        else:
            if not has_hardlink:
                without_hardlinks.append(torrent)
    return without_hardlinks


def filter_torrents(
    torrents: list[Torrent],
    dir: str | None,
    tracker: str | None,
) -> list[Torrent]:
    # filter torrents to only have ones that are seeding or stopped
    torrents = [x for x in torrents if x.status == "seeding" or x.status == "stopped"]
    print(f"Filtered to {len(torrents)} seeding or stopped torrents")
    # Filter torrents by directory if specified
    if dir:
        torrents = [x for x in torrents if dir in str(x.download_dir)]
        print(f"Filtered to {len(torrents)} torrents in directory matching '{dir}'")

    # Filter torrents by tracker if specified
    if tracker:
        torrents = [x for x in torrents if any(tracker in t.announce for t in x.trackers)]
        print(f"Filtered to {len(torrents)} torrents with tracker matching '{tracker}'")

    if not dir and not tracker:
        print("No directory or tracker filters applied, processing all torrents")

    return torrents


def process_torrents(client: Client, torrents: list[Torrent], action: str):
    # Handle action based on argument
    if action in ["list", "l"]:
        for torrent in torrents:
            print(f"  - {torrent.name}")
    elif action in ["delete-data", "d"]:
        for torrent in torrents:
            print(f"{torrent.name}: Removing with data")
            client.remove_torrent(torrent.id, delete_data=True)
    elif action in ["remove", "r"]:
        for torrent in torrents:
            print(f"{torrent.name}: Removing without data")
            client.remove_torrent(torrent.id, delete_data=False)
    else:
        for torrent in torrents:
            choice = input(f"{torrent.name}\n^ Remove torrent? [N/y/d(ata)] ").strip().lower() or "n"
            if choice == "y":
                client.remove_torrent(torrent.id, delete_data=False)
            elif choice == "d":
                client.remove_torrent(torrent.id, delete_data=True)
            else:
                print("skipped")
