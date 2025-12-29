# Author: Cameron F. Abrams, <cfa22@drexel.edu>
import os
import logging
import yaml
import sys

from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from shutil import which

from ..util.stringthings import my_logger

logger = logging.getLogger(__name__)

def is_executable(cmd: str) -> bool:
    return which(cmd) is not None

class Config:
    def __init__(self, userfile='' , **kwargs):
        self.resource_root = files('pygacity') / 'resources'
        self.specs = {}
        if userfile:
            assert os.path.exists(userfile), f'Config file {userfile} not found'
            with open(userfile, 'r', encoding='utf-8') as f:
                self.specs = yaml.safe_load(f)
        else:
            raise ValueError('No user config file specified')
        assert 'document' in self.specs, f'Your config file does not specify a document structure'
        assert 'build' in self.specs, f'Your config file does not specify document build parameters'

        self.document_specs = self.specs['document']
        self.build_specs = self.specs['build']

        self.autoprob_package_root = self.resource_root / 'autoprob-package'
        self.autoprob_package_dir = self.autoprob_package_root / 'tex' / 'latex'

        logger.debug(f'autoprob_package_root {self.autoprob_package_root}')
        
        self.progress = kwargs.get('progress', False)
        self.templates_root = self.resource_root / 'templates'
        assert os.path.exists(self.templates_root)

        self.platform = sys.platform
        self.home = Path.home()

        self._set_defaults()

    def _set_defaults(self):
        if 'class' not in self.document_specs:
            self.document_specs['class'] = {
                'classname': 'autoprob',
                'options': ['11pt']
            }
        if 'structure' not in self.document_specs:
            raise ValueError('Document structure not specified in config file')
        if 'substitutions' not in self.document_specs:
            self.document_specs['substitutions'] = {}
        if 'paths' not in self.build_specs:
            self.build_specs['paths'] = {}
        for cmd in ['pdflatex', 'pythontex']:
            if cmd not in self.build_specs['paths']:
                self.build_specs['paths'][cmd] = cmd
                logger.debug(f'Setting default path for {cmd} to "{cmd}"')
                if not is_executable(cmd):
                    if self.platform == 'win32':
                        # default: C:\Users\cfa22\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe
                        self.build_specs['paths'][cmd] = self.home / 'AppData' / 'Local' / 'Programs' / 'MiKTeX' / 'miktex' / 'bin' / 'x64' / f'{cmd}.exe'
                        cmd = str(self.build_specs['paths'][cmd])
                        if not is_executable(cmd):
                            raise ValueError(f'{cmd} executable not found in PATH; please specify its location in the config file')
                    else:
                        raise ValueError(f'{cmd} executable not found in PATH; please specify its location in the config file')
                else:
                    logger.debug(f'Found {cmd} executable in PATH')
        if 'build-dir' not in self.build_specs['paths']:
            self.build_specs['paths']['build-dir'] = Path.cwd() / 'build'
        # if 'output-dir' not in self.build_specs:
        #     self.build_specs['output-dir'] = Path.cwd() / 'build'
        if 'job-name' not in self.build_specs:
            self.build_specs['job-name'] = 'pygacity_document'
        if 'overwrite' not in self.build_specs:
            self.build_specs['overwrite'] = False
        if 'solutions' not in self.build_specs:
            self.build_specs['solutions'] = True
        if 'copies' not in self.build_specs:
            self.build_specs['copies'] = 1
        if 'serial-digits' not in self.build_specs:
            self.build_specs['serial-digits'] = 8
        if 'answer-set' not in self.build_specs:
            self.build_specs['answer-set'] = 'all'