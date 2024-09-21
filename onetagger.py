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
                        # Run the OneTagger CLI and capture output in real-time
                        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)

                        # Log stdout in real-time
                        for stdout_line in iter(process.stdout.readline, ""):
                            self._log.info(f"OneTagger output: {stdout_line.strip()}")
                        process.stdout.close()
                        # Log stderr in real-time
                        for stderr_line in iter(process.stderr.readline, ""):
                            self._log.info(f"OneTagger error: {stderr_line.strip()}")
                        process.stderr.close()
                        # Wait for the process to finish and get the return code
                        return_code = process.wait()
                        if return_code == 0:
                           print(f'  [OneTagger Plugin] Successfully processed: {path}')
                        else:
                            self._log.error(f'OneTagger failed for {path}.')
                            self._log.error(f'Command: {" ".join(command)}')
                            self._log.error(f'Return code: {return_code}')
                    except Exception as e:
                        self._log.error(f'Error running OneTagger for {path}: {str(e)}')
                self._log.info('OneTagger processing complete')