# Transmission Cleaner

A CLI tool to help you clean up Transmission torrents that don't have hardlinks to other files on your system.

This is particularly useful if you're using Transmission with media management tools like Sonarr, Radarr, or similar applications that create hardlinks to your torrent files. This tool helps you identify and remove torrents whose files are no longer hardlinked anywhere else.

## Installation

### Quick Install (Recommended)

If you haven't yet, [install uv](https://docs.astral.sh/uv/getting-started/installation/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`). It's a massive painkiller for the python management headache.

```bash
# Using uv (recommended for CLI tools)
uv tool install transmission-unlinked

# Or from source
git clone https://github.com/flying-sausages/transmission-unlinked.git
cd transmission-unlinked
uv tool install .
```

## Usage

After installation, you can run the tool using the `transmission-unlinked` command:

```bash
transmission-unlinked --settings-file ~/.config/transmission-daemon/settings.json --password YOUR_PASSWORD
```
### Arguments
you can see the latest commandline args by running the following:
```bash
transmision-unlinked --help
```

Currently, this looks like the following:
```
usage: transmission-unlinked [-h] [-d DIRECTORY] [-t TRACKER] [--min-days MIN_DAYS]
                             [--action {None,list,l,delete,d,remove,r}] [--settings-file SETTINGS_FILE]
                             [--protocol {http,https}] [--username USERNAME] --password PASSWORD
                             [--host HOST] [--port PORT] [--path PATH]

Clean up Transmission torrents based on hardlink status

options:
  -h, --help            show this help message and exit
  -d, --dir, --directory DIRECTORY
                        Filter torrents by download directory (substring match)
  -t, --tracker TRACKER
                        Filter torrents by announce URL (substring match)
  --min-days MIN_DAYS   Minimum days of active seeding time (default: 7)
  --action {None,list,l,delete,d,remove,r}
                        Action to apply to torrents without any other hardlinks. Interactive by default |
                        list / l: show torrents only | delete / d: remove torrent with data on disk | remove
                        / r: remove torrent from client only |

authentication:
  --settings-file SETTINGS_FILE
                        Path to Transmission settings.json file
  --protocol {http,https}
                        Protocol to use (default: http)
  --username USERNAME   Transmission username
  --password PASSWORD   Transmission password
  --host HOST           Transmission host (default: 127.0.0.1)
  --port PORT           Transmission port (default: 9091)
  --path PATH           Transmission RPC path (default: /transmission/rpc)
```

### Arrs setup suggestion:
- Have something (Plex/maintainerr/etc.) automatically delete things
- Make sure your arr has `Unmonitor Deleted Episodes` set to True
- In the arr's download client settings, set a value for `Category` (this moves downloaded torrents into the following )
- use that for the directory argument (`transmission-unlinked --directory Sonarr`)
- After playing around with the tool, add something like this to your crontab to run daily at 3am:
`0 3 * * * /path/to/transmission-unlinked --settings-file ~/.config/transmission-daemon/settings.json --password YOUR_PASSWORD --directory /path/to/sonarr --action delete >> /var/log/transmission-unlinked.log 2>&1`

## Development

```bash
# Set the project up
uv sync

# Run linting
ruff check .

# Run type checking
basedpyright
```

## Safety Notes

- **Always test with `--action list` first** to see what would be affected
- **Use interactive mode** when unsure about automatic removal
- **Backup your data** before performing bulk deletions
- The tool requires direct filesystem access to check hardlinks

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
