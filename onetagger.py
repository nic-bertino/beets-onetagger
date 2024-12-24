from beets.plugins import BeetsPlugin
import subprocess
import itertools
import threading
import time


class OneTaggerPlugin(BeetsPlugin):

    def __init__(self):
        super(OneTaggerPlugin, self).__init__()
        self.register_listener('import_task_files', self.run_onetagger)

    def run_onetagger(self, task):

        onetagger_executable = self.config['executable'].get()
        onetagger_config = self.config['config'].get()
        def format_onetagger_message(message):
            return f"\033[1;38;5;256;48;5;65m bonetagger ➜ \033[22;38;5;256;48;5;65m {message} \033[0m"
        if not onetagger_executable or not onetagger_config:
            self._log.error(
                'OneTagger executable or config path not set in configuration.'
            )
            return

        # Get all items that were just imported
        imported_items = task.items
        total_items = len(imported_items)

        self._log.debug(f'Total imported items: {total_items}')

        def spinner():
            colors = itertools.cycle(['\033[37m', '\033[90m', '\033[37;1m', '\033[38;5;250m', '\033[38;5;245m', '\033[38;5;240m'])
            spinner_chars = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
            while self.spinner_running:
                color = next(colors)
                char = next(spinner_chars)
                print('\r' + format_onetagger_message(f'{color}{char}'), end='', flush=True)
                time.sleep(0.2)
                print('\r', end='', flush=True)

        for index, item in enumerate(imported_items, start=1):
            post_import_path = item.path
            if isinstance(post_import_path, bytes):
                post_import_path = post_import_path.decode('utf-8')

            self._log.info(
                f'Processing file {index} of {total_items}: {post_import_path}'
            )
            print(format_onetagger_message(f'Tagging {index}/{total_items}: {post_import_path}'))
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
                    if any(key in line.lower() for key in ["matching", "found", "successfully"]):
                        print(f"\r{format_onetagger_message(line)}")

                    if "successfully" in line.lower():
                        success_message_seen = True
                process.stdout.close()
                
                # Log stderr in real-time
                for stderr_line in iter(process.stderr.readline, ""):
                    line = stderr_line.strip()
                    self._log.info(f"OneTagger error: {line}")
                    # Show errors to user
                    if not line.startswith(("Debug:", "Info:")):
                        print(f"\r  [OneTagger Error] {line}")
                process.stderr.close()
                
                # Wait for the process to finish and get the return code
                return_code = process.wait()
                self.spinner_running = False
                spinner_thread.join()
                if return_code == 0:
                    if not success_message_seen:
                        print(f'\r{format_onetagger_message(f"Finished tagging: {post_import_path}")}')

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
        print(format_onetagger_message(f'Completed! {total_items} tagged'))
