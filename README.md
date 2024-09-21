# Beets OneTagger Plugin

This Beets plugin integrates OneTagger functionality into your Beets workflow, automatically running OneTagger after importing new music files.

## Installation

1. Ensure you have Beets installed.
2. Install OneTagger CLI and set up its configuration.
3. Place the `onetagger.py` file in your Beets plugin directory (usually `~/.config/beets/plugins/`).
4. Add `onetagger` to the `plugins` section in your Beets configuration file.

## Configuration

Add the following to your Beets configuration file (usually `config.yaml`):

```yaml
onetagger:
    executable: path/to/onetagger-cli
    config: path/to/onetagger/config.json
```

Replace `path/to/onetagger-cli` with the actual path to your OneTagger CLI executable, and `path/to/onetagger/config.json` with the path to your OneTagger configuration file.

Both executable and config settings are required for the plugin to function correctly.

## Usage
Once installed and configured, the plugin will automatically run OneTagger on newly imported music files. No additional steps are required during normal usage.

## Logging
The plugin logs its activities, including successful processing and any errors encountered. Check your Beets log file for details on OneTagger operations.