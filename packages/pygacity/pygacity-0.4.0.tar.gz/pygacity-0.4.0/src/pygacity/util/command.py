# Author: Cameron F. Abrams, <cfa22@drexel.edu>
import subprocess
import logging

logger = logging.getLogger(__name__)

class Command:
    def __init__(self, command, ignore_codes=[], **options):
        self.command = command
        self.ignore_codes = ignore_codes
        self.options = options
        self.c = f'{self.command} ' + ' '.join([f'-{k} {v}' for k, v in self.options.items()])
        
    def run(self):
        process = subprocess.Popen(self.c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = process.communicate()
        if process.returncode != 0 and not process.returncode in self.ignore_codes:
            raise subprocess.SubprocessError(f'Command "{self.c}" failed with returncode {process.returncode}')
        return out, err