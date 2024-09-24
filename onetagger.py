from beets.plugins import BeetsPlugin
import subprocess
import os

class OneTaggerPlugin(BeetsPlugin):
    def __init__(self):
        super(OneTaggerPlugin, self).__init__()
        self.register_listener('import', self.run_onetagger)

    def run_onetagger(self, lib, paths):
        print(f'  [OneTagger Plugin] Import complete, starting OneTagger.')

        onetagger_executable = self.config['executable'].get()
        onetagger_config = self.config['config'].get()

        if not onetagger_executable or not onetagger_config:
            self._log.error('OneTagger executable or config path not set in configuration.')
            return

        # Convert paths to strings if they're bytes
        str_paths = [p.decode('utf-8') if isinstance(p, bytes) else p for p in paths]

        # Get all items that were just imported
        imported_items = lib.items(str_paths)
        total_items = len(imported_items)

        for index, item in enumerate(imported_items, start=1):
            post_import_path = item.path
            if isinstance(post_import_path, bytes):
                post_import_path = post_import_path.decode('utf-8')

            self._log.info(f'Processing file {index} of {total_items}: {post_import_path}')
            try:
                command = [
                    onetagger_executable,
                    'autotagger',
                    '--config',
                    onetagger_config,
                    '--path',
                    post_import_path
                ]
                self._log.debug(f'Executing command: {" ".join(command)}')
                # Run the subprocess and capture output in real-time
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)

                success_message_seen = False
                # Log stdout in real-time
                for stdout_line in iter(process.stdout.readline, ""):
                    self._log.info(f"OneTagger output: {stdout_line.strip()}")
                    if "successfully" in stdout_line.lower():
                        success_message_seen = True
                process.stdout.close()
                # Log stderr in real-time
                for stderr_line in iter(process.stderr.readline, ""):
                    self._log.info(f"OneTagger error: {stderr_line.strip()}")
                process.stderr.close()
                # Wait for the process to finish and get the return code
                return_code = process.wait()
                if return_code == 0:
                    if not success_message_seen:
                        print(f'  [OneTagger Plugin] Successfully processed: {post_import_path}')
                else:
                    self._log.error(f'OneTagger failed for {post_import_path}.')
                    self._log.error(f'Command: {" ".join(command)}')
                    self._log.error(f'Return code: {return_code}')
            except Exception as e:
                self._log.error(f'Error running OneTagger for {post_import_path}: {str(e)}')
        self._log.info('OneTagger processing complete')
