from beets.plugins import BeetsPlugin
import subprocess
import os

class OneTaggerPlugin(BeetsPlugin):
    def __init__(self):
        super(OneTaggerPlugin, self).__init__()
        self.register_listener('import', self.run_onetagger)

    def run_onetagger(self, lib, paths):
        self._log.info('Running OneTagger after import...')

        onetagger_executable = self.config['executable'].get()
        onetagger_config = self.config['config'].get()

        if not onetagger_executable or not onetagger_config:
            self._log.error('OneTagger executable or config path not set in configuration.')
            return

        total_paths = len(paths)
        for index, path in enumerate(paths, start=1):
            if isinstance(path, bytes):
                path = path.decode('utf-8')

            self._log.info(f'Processing file {index} of {total_paths}: {path}')
            try:
                command = [
                    onetagger_executable,
                    'autotagger',
                    '--config',
                    onetagger_config,
                    '--path',
                    path
                ]

                self._log.debug(f'Executing command: {" ".join(command)}')

                result = subprocess.run(command, capture_output=True, text=True)

                if result.returncode == 0:
                    self._log.info(f'OneTagger successfully processed: {path}')
                else:
                    self._log.error(f'OneTagger failed for {path}.')
                    self._log.error(f'Command: {" ".join(command)}')
                    self._log.error(f'Return code: {result.returncode}')
                    self._log.error(f'stdout: {result.stdout}')
                    self._log.error(f'stderr: {result.stderr}')

            except Exception as e:
                self._log.error(f'Error running OneTagger for {path}: {str(e)}')

        self._log.info('OneTagger processing complete')