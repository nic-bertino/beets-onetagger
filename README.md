# beetbridge

This plugin passes beets-imported files to OneTagger to provide more robust and customized metadata.

## Installation

1. Ensure you have Beets installed.
2. Install OneTagger CLI and set up its configuration.
3. Place the `beetbridge.py` file in your Beets plugin directory (usually `~/.config/beets/plugins/`).
4. Add `beetbridge` to the `plugins` section in your Beets configuration file.

## Configuration

Add the following to your Beets configuration file (usually `config.yaml`):

```yaml
beetbridge:
    executable: path/to/onetagger-cli
    config: path/to/onetagger/config.json
```

Replace `path/to/onetagger-cli` with the actual path to your OneTagger CLI executable, and `path/to/onetagger/config.json` with the path to your OneTagger configuration file.

Both executable and config settings are required for the plugin to function correctly. You can test OneTagger's CLI separately from beets to ensure it's configured correctly.

## Example workflow

beets import -> write discogs style/genre via onetagger -> dj software

beets is my primary organizer and metadata manager for vinyl rips. When DJing, I use smart crates in Serato/Engine/Rekordbox, which read the metadata and can create crates based on metadata conditions. These conditions might include:
* Genres ("Funk/Soul")
* Year (1979-1982, 2015-present, 2024)
* Style ("Disco", "Soul", "Boogie")
* BPM (Under 100BPM, over 130BPM)

Discogs has the _most consistent_ genre and style information. I append both to the Genre tag.
