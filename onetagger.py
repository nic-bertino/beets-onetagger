from beets.plugins import BeetsPlugin
import subprocess
import itertools
import threading
import time
from datetime import datetime

class ConsoleFormatter:
    """Handles consistent console output formatting"""
    COLORS = {
        'header': '\033[1;38;5;39m',
        'success': '\033[1;38;5;76m',
        'error': '\033[1;38;5;196m',
        'warning': '\033[1;38;5;214m',
        'info': '\033[1;38;5;147m',
        'reset': '\033[0m'
    }
    
    @staticmethod
    def format_message(message, style='info', prefix='onetagger'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        prefix_color = ConsoleFormatter.COLORS.get(style, ConsoleFormatter.COLORS['info'])
        return f"{prefix_color}[{timestamp}] {prefix} ❯ {message}{ConsoleFormatter.COLORS['reset']}"
    
    @staticmethod
    def progress_bar(current, total, width=30):
        percentage = current / total
        filled = int(width * percentage)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {current}/{total} ({percentage:.1%})"


class OneTaggerPlugin(BeetsPlugin):

    def __init__(self):
        super(OneTaggerPlugin, self).__init__()
        self.register_listener('import_task_files', self.run_onetagger)
        self.formatter = ConsoleFormatter()

    def run_onetagger(self, task):
        onetagger_executable = self.config['executable'].get()
        onetagger_config = self.config['config'].get()
        if not onetagger_executable or not onetagger_config:
            print(self.formatter.format_message(
                'Configuration error: OneTagger executable or config path not set!', 
                style='error'
            ))
            print(self.formatter.format_message(
                'Please check your config.yaml file and ensure both paths are set correctly.',
                style='info'
            ))
            return

        # Get all items that were just imported
        imported_items = task.items
        total_items = len(imported_items)

        self._log.debug(f'Total imported items: {total_items}')

        def spinner():
            spinner_chars = itertools.cycle(['◜', '◠', '◝', '◞', '◡', '◟'])
            while self.spinner_running:
                char = next(spinner_chars)
                status = self.formatter.format_message(
                    f"{char} Processing...", 
                    style='info'
                )
                print(f"\r{status}", end='', flush=True)
                time.sleep(0.1)

        for index, item in enumerate(imported_items, start=1):
            post_import_path = item.path
            if isinstance(post_import_path, bytes):
                post_import_path = post_import_path.decode('utf-8')

            filename = post_import_path.split('/')[-1]
            progress = self.formatter.progress_bar(index, total_items)
            print(f"\r{self.formatter.format_message(f'{progress} Processing: {filename}', style='header')}", end='', flush=True)
            try:
                command = [
                    onetagger_executable, 'autotagger', '--config',
                    onetagger_config, '--path', post_import_path
                ]
                self._log.debug(f'Executing command: {" ".join(command)}')

                # Start spinner in a separate thread
                self.spinner_running = True
                spinner_thread = threading.Thread(target=spinner)
                spinner_thread.start()

                # Run the subprocess and capture output in real-time
                process = subprocess.Popen(command,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           text=True,
                                           bufsize=1,
                                           universal_newlines=True)

                success_message_seen = False
                # Log stdout in real-time
                for stdout_line in iter(process.stdout.readline, ""):
                    line = stdout_line.strip()
                    self._log.info(f"OneTagger output: {line}")
                    
                    # Show important status messages to user
                    if "matching" in line.lower():
                        print(self.formatter.format_message(f"🔍 {line}", style='info'))
                    elif "found" in line.lower():
                        print(self.formatter.format_message(f"✓ {line}", style='success'))
                    elif "successfully" in line.lower():
                        print(self.formatter.format_message(f"✨ {line}", style='success'))
                        success_message_seen = True
                process.stdout.close()
                
                # Log stderr in real-time
                for stderr_line in iter(process.stderr.readline, ""):
                    line = stderr_line.strip()
                    self._log.info(f"OneTagger error: {line}")
                    # Show errors to user
                    if not line.startswith(("Debug:", "Info:")):
                        print(self.formatter.format_message(f"❌ {line}", style='error'))
                process.stderr.close()
                
                # Wait for the process to finish and get the return code
                return_code = process.wait()
                self.spinner_running = False
                spinner_thread.join()
                if return_code == 0:
                    if not success_message_seen:
                        # Get terminal width for proper line clearing
                        try:
                            import shutil
                            terminal_width = shutil.get_terminal_size().columns
                        except:
                            terminal_width = 120  # fallback width
                        
                        # Clear the entire line
                        print('\r' + ' ' * terminal_width + '\r', end='', flush=True)
                        filename = post_import_path.split('/')[-1]
                        print(f"\r{self.formatter.format_message(f'✅ {filename}', style='success')}", end='\n', flush=True)

                else:
                    self._log.error(
                        f'OneTagger failed for {post_import_path}.')
                    self._log.error(f'Command: {" ".join(command)}')
                    self._log.error(f'Return code: {return_code}')
            except Exception as e:
                self._log.error(
                    f'Error running OneTagger for {post_import_path}: {str(e)}'
                )
        self._log.info('OneTagger processing complete')
        summary = f"🎉 All done! Successfully processed {total_items} files"
        print("\n" + self.formatter.format_message(summary, style='success'))
