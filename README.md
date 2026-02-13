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
    process_singletons: true    # Optional: process non-album files (default: true)
    timeout: 300                # Optional: maximum seconds per file (default: 300)
```

Replace `path/to/onetagger-cli` with the actual path to your OneTagger CLI executable, and `path/to/onetagger/config.json` with the path to your OneTagger configuration file.

Both executable and config settings are required for the plugin to function correctly. You can test OneTagger's CLI separately from beets to ensure it's configured correctly.

## User Interface

When [Rich](https://github.com/Textualize/rich) is installed, the plugin displays a live-updating table during tagging. Track rows turn green as they complete, and a Match column appears when OneTagger returns accuracy data. Failed tracks are shown in red.

```
beetbridge: Changing

  Changing
  Pressure
  Always
  Said You Wouldn't Leave Again
  You Know What I Like
  Where Do We Go From Here
  Love Soldier
  Problem Solver

8/8 tracks  16s
```

Without Rich, the plugin falls back to plain text:

```
beetbridge: Changing
  [1/8] Changing 2s
  [2/8] Pressure 2s
  ...
  8 tracks  16s
```
