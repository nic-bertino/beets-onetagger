import os
import subprocess
import threading
import time

from beets.plugins import BeetsPlugin

try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from rich.box import SIMPLE
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class BeetBridgePlugin(BeetsPlugin):

    def __init__(self):
        super().__init__()

        self.config.add({
            'executable': '',
            'config': '',
            'process_singletons': True,
            'timeout': 300,
        })
        self.config_valid = self._validate_config()

        self.register_listener('import_task_files', self.run_onetagger)
        self.register_listener('import_end', self.show_final_summary)

        self.total_processed = 0
        self.albums_processed = 0
        self.onetagger_running = False

        if RICH_AVAILABLE:
            self.console = Console()

    def _validate_config(self):
        executable = self.config['executable'].get()
        config_path = self.config['config'].get()

        if not executable:
            self._log.warning('OneTagger executable path not configured')
            return False

        if not config_path:
            self._log.warning('OneTagger config path not configured')
            return False

        if not os.path.isfile(executable):
            self._log.warning(f'OneTagger executable not found at {executable}')
            return False

        if not os.path.isfile(config_path):
            self._log.warning(f'OneTagger config not found at {config_path}')
            return False

        return True

    def run_onetagger(self, task, session):
        if not self.config_valid:
            self._log.warning('Skipping OneTagger processing due to invalid configuration')
            return

        if self.onetagger_running:
            self._log.info('OneTagger is already running, skipping this task')
            return

        self.onetagger_running = True
        live = None

        try:
            if not task.is_album:
                if not self.config['process_singletons'].get(bool):
                    self._log.info('Skipping singleton item (process_singletons=False)')
                    return

            onetagger_executable = self.config['executable'].get()
            onetagger_config = self.config['config'].get()
            timeout = self.config['timeout'].get(int)

            imported_items = list(task.items)
            total_items = len(imported_items)

            if total_items == 0:
                self._log.debug('No items to process in this task')
                return

            # Determine album name
            album_name = "Unknown Album"
            if hasattr(task, 'album') and task.album and hasattr(task.album, 'album'):
                album_name = task.album.album
            elif imported_items and hasattr(imported_items[0], 'album'):
                album_name = imported_items[0].album

            self.albums_processed += 1

            # Build track status list
            track_statuses = []
            for i, item in enumerate(imported_items, 1):
                title = item.title if hasattr(item, 'title') and item.title else os.path.basename(
                    item.path.decode('utf-8') if isinstance(item.path, bytes) else item.path
                )
                track_statuses.append({
                    'title': title,
                    'status': '',
                    'match': '',
                    'elapsed': 0,
                    'failed': False,
                })

            if RICH_AVAILABLE:
                live = Live(
                    self._build_table(album_name, track_statuses),
                    console=self.console,
                    refresh_per_second=8,
                    transient=False,
                )
                live.start()
            else:
                print(f"beetbridge: {album_name}")

            # Process each track
            for index, item in enumerate(imported_items):
                path = item.path
                if isinstance(path, bytes):
                    path = path.decode('utf-8')

                track_statuses[index]['status'] = 'Tagging'
                if RICH_AVAILABLE and live:
                    live.update(self._build_table(album_name, track_statuses))

                start_time = time.time()

                command = [
                    onetagger_executable, 'autotagger',
                    '--config', onetagger_config,
                    '--path', path,
                ]
                self._log.debug(f'Executing command: {" ".join(command)}')

                try:
                    success, match, _ = self._run_subprocess(
                        command, timeout, track_statuses, index
                    )
                    track_statuses[index]['elapsed'] = int(time.time() - start_time)

                    if success:
                        track_statuses[index]['status'] = 'Done'
                        track_statuses[index]['match'] = match
                        self.total_processed += 1
                    else:
                        track_statuses[index]['status'] = 'Failed'
                        track_statuses[index]['failed'] = True

                except Exception as e:
                    self._log.error(f'Error running OneTagger for {path}: {e}')
                    track_statuses[index]['status'] = 'Failed'
                    track_statuses[index]['failed'] = True
                    track_statuses[index]['elapsed'] = int(time.time() - start_time)

                if RICH_AVAILABLE and live:
                    live.update(self._build_table(album_name, track_statuses))
                else:
                    s = track_statuses[index]
                    match_str = f" {s['match']}" if s['match'] else ""
                    if s['failed']:
                        print(f"  [{index + 1}/{total_items}] {s['title']}... failed")
                    else:
                        print(f"  [{index + 1}/{total_items}] {s['title']}"
                              f"{match_str} {s['elapsed']}s")

            if not RICH_AVAILABLE:
                total_secs = sum(s['elapsed'] for s in track_statuses)
                print(f"  {total_items} tracks  {total_secs}s")

            self._log.info(f'OneTagger processing complete for album: {album_name}')

        finally:
            if live:
                try:
                    live.stop()
                except Exception:
                    pass
            self.onetagger_running = False

    def _run_subprocess(self, command, timeout, track_statuses, index):
        """Run onetagger-cli and parse output. Returns (success, match_quality, elapsed)."""
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        lock = threading.Lock()
        result = {'match': '', 'failed': False}

        def output_reader():
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                self._log.debug(f'OneTagger output: {line}')

                if 'Accuracy:' in line:
                    try:
                        accuracy = line.split('Accuracy: Some(')[1].split(')')[0]
                        pct = int(float(accuracy) * 100)
                        with lock:
                            result['match'] = f"{pct}%"
                    except Exception:
                        pass

            for line in iter(process.stderr.readline, ''):
                line = line.strip()
                self._log.debug(f'OneTagger stderr: {line}')
                if line and not line.startswith(('Debug:', 'Info:')):
                    with lock:
                        result['failed'] = True

        reader_thread = threading.Thread(target=output_reader, daemon=True)
        reader_thread.start()

        try:
            return_code = process.wait(timeout=timeout)
            reader_thread.join(timeout=2.0)

            with lock:
                match = result['match']
                failed = result['failed']

            if return_code == 0 and not failed:
                return True, match, 0
            else:
                return False, match, 0

        except subprocess.TimeoutExpired:
            process.kill()
            reader_thread.join(timeout=2.0)
            self._log.error(f'OneTagger timed out after {timeout}s')
            return False, '', 0

    def _build_table(self, album_name, track_statuses):
        """Build a Rich Table for the current track statuses."""
        has_match = any(s['match'] for s in track_statuses)
        done = sum(1 for s in track_statuses if s['status'] in ('Done', 'Failed'))
        total = len(track_statuses)
        total_secs = sum(s['elapsed'] for s in track_statuses)

        caption = f"{done}/{total} tracks  {total_secs}s" if done else ""

        table = Table(
            box=SIMPLE,
            show_lines=False,
            expand=False,
            title=Text(f"beetbridge: {album_name}"),
            title_justify="left",
            title_style="",
            caption=caption,
            caption_justify="left",
            caption_style="dim",
            show_header=False,
        )

        table.add_column("Track")
        if has_match:
            table.add_column("Match", justify="right")

        for s in track_statuses:
            if s['failed']:
                style = "red"
            elif s['status'] == 'Done':
                style = "green"
            elif s['status'] == 'Tagging':
                style = ""
            else:
                style = "dim"

            title = s['title'] if not s['failed'] else f"{s['title']}  failed"

            row = [title]
            if has_match:
                row.append(s['match'])

            table.add_row(*row, style=style)

        return table

    def show_final_summary(self, lib, session):
        if self.total_processed > 0:
            print(f"beetbridge: {self.total_processed} files across "
                  f"{self.albums_processed} albums")

        self.total_processed = 0
        self.albums_processed = 0
