import unittest
from unittest.mock import Mock, patch, MagicMock


def _make_plugin():
    """Create a BeetBridgePlugin without invoking beets' full init."""
    from beetbridge import BeetBridgePlugin, RICH_AVAILABLE

    plugin = object.__new__(BeetBridgePlugin)
    plugin._log = Mock()
    plugin.config_valid = True
    plugin.total_processed = 0
    plugin.albums_processed = 0
    plugin.onetagger_running = False
    plugin.config = {
        'executable': MagicMock(**{'get.return_value': '/path/to/onetagger'}),
        'config': MagicMock(**{'get.return_value': '/path/to/config.json'}),
        'process_singletons': MagicMock(**{'get.return_value': True}),
        'timeout': MagicMock(**{'get.return_value': 300}),
    }
    if RICH_AVAILABLE:
        from rich.console import Console
        plugin.console = Console()
    return plugin


def _make_task(items, is_album=True):
    """Create a mock import task."""
    task = Mock()
    task.is_album = is_album
    task.items = items
    task.album = None
    return task


def _make_item(path=b'/path/to/audio/file.mp3', title='Test Track', album='Test Album'):
    item = Mock()
    item.path = path
    item.title = title
    item.album = album
    return item


class TestBeetBridgePlugin(unittest.TestCase):

    def setUp(self):
        self.plugin = _make_plugin()

    @patch('beetbridge.subprocess.Popen')
    def test_successful_import(self, mock_popen):
        proc = Mock()
        proc.stdout.readline.side_effect = ['Accuracy: Some(0.85)\n', '']
        proc.stderr.readline.side_effect = ['']
        proc.wait.return_value = 0
        mock_popen.return_value = proc

        task = _make_task([_make_item()])

        self.plugin.run_onetagger(task, Mock())

        mock_popen.assert_called_once()
        self.assertEqual(self.plugin.total_processed, 1)

    def test_skips_with_invalid_config(self):
        self.plugin.config_valid = False

        self.plugin.run_onetagger(Mock(), Mock())

        self.plugin._log.warning.assert_called_with(
            'Skipping OneTagger processing due to invalid configuration'
        )

    @patch('beetbridge.subprocess.Popen')
    def test_onetagger_failure(self, mock_popen):
        proc = Mock()
        proc.stdout.readline.side_effect = ['']
        proc.stderr.readline.side_effect = ['Fatal error occurred\n', '']
        proc.wait.return_value = 1
        mock_popen.return_value = proc

        task = _make_task([_make_item()])

        self.plugin.run_onetagger(task, Mock())

        mock_popen.assert_called_once()
        self.assertEqual(self.plugin.total_processed, 0)

    @patch('beetbridge.subprocess.Popen')
    def test_timeout_handling(self, mock_popen):
        import subprocess as sp

        proc = Mock()
        proc.stdout.readline.side_effect = ['']
        proc.stderr.readline.side_effect = ['']
        proc.wait.side_effect = sp.TimeoutExpired(cmd='test', timeout=300)
        proc.kill = Mock()
        mock_popen.return_value = proc

        task = _make_task([_make_item()])

        self.plugin.run_onetagger(task, Mock())

        proc.kill.assert_called_once()
        self.assertEqual(self.plugin.total_processed, 0)

    def test_show_final_summary(self):
        self.plugin.total_processed = 10
        self.plugin.albums_processed = 2

        with patch('builtins.print') as mock_print:
            self.plugin.show_final_summary(Mock(), Mock())

        mock_print.assert_called_with(
            'beetbridge: 10 files across 2 albums'
        )
        self.assertEqual(self.plugin.total_processed, 0)
        self.assertEqual(self.plugin.albums_processed, 0)

    def test_show_final_summary_no_output_when_zero(self):
        self.plugin.total_processed = 0
        self.plugin.albums_processed = 0

        with patch('builtins.print') as mock_print:
            self.plugin.show_final_summary(Mock(), Mock())

        mock_print.assert_not_called()


if __name__ == '__main__':
    unittest.main()
