# Author: Cameron F. Abrams, <cfa22@drexel.edu>
from __future__ import annotations
import logging
import os
import re

from copy import deepcopy
from importlib.resources import files
from pathlib import Path
from shutil import copy2

logger = logging.getLogger(__name__)

def path_resolver(filename: str, search_paths: list[Path] = [], ext: str ='') -> Path:
    local_filename = filename if filename.endswith(ext) else filename + ext
    # check local directory first
    local_path = Path(local_filename)
    if local_path.exists():
        return local_path
    # check search path next
    else:
        for search_path in search_paths:
            template_path = search_path / local_filename
            if template_path.exists():
                return template_path
        spm = ':'.join([str(sp) for sp in search_paths])
        raise FileNotFoundError((f'Could not locate source file {local_filename} in cwd ({os.getcwd()}) '
                                 f'or search path {spm}.'))

class LatexCompoundBlock:
    resources_root: Path = files('pygacity') / 'resources'
    templates_dir: Path = resources_root / 'templates'
    pythontex_dir = resources_root / 'pythontex'
    substitution_delimiters: tuple = (r'<<<', r'>>>')

    def __init__(self, block_specs: dict, parent_idx: str = '', idx: int = 0):
        self.block_specs = block_specs
        self.idx = parent_idx + (f'.{idx}' if parent_idx != '' else f'{idx}')
        self.textcontents: str = block_specs.get('text', '')

        self.sourcename: str = block_specs.get('source', None)
        self.substitution_map: dict = block_specs.get('substitutions', {})

        self.points: int = block_specs.get('points', 0)
        self.config_filename: str = block_specs.get('config', None)
        self.group: int = block_specs.get('group', 0)

        self.pythontex: list[str] = block_specs.get('pythontex', [])

        self.enumerate = [LatexCompoundBlock(block_specs=child, parent_idx=self.idx, idx=i+1) for i, child in enumerate(block_specs.get('enumerate', []))]
        self.itemize = [LatexCompoundBlock(block_specs=child, parent_idx=self.idx, idx=i+1) for i, child in enumerate(block_specs.get('itemize', []))]
        self.children = self.enumerate + self.itemize

        self.sourcepath = None
        self.config_path = Path(self.config_filename) if self.config_filename else None
        self.processedcontents: str = ''
        self.has_pycode: bool = False
        self.embedded_graphics: list[str | Path] = []

        self._check_schema()

        logger.debug(f'LatexCompoundBlock.__init__ substitution_map: {self.substitution_map}')

    def _check_schema(self):
        # cannot specify both text content and a source file
        if self.textcontents != '' and self.sourcename is not None:
            raise ValueError('Block cannot specify both "text" content and a "source" file.')
        # cannot specify both enumerate and itemize
        if len(self.enumerate) > 0 and len(self.itemize) > 0:
            raise ValueError('Block cannot specify both "enumerate" and "itemize" children.')
        # if list of pythontext files is non-empty, cannot specify text or source
        if len(self.pythontex) > 0:
            if self.textcontents != '' or self.sourcename is not None:
                raise ValueError('Block cannot specify "pythontex" files along with "text" content or a "source" file.')

    def load(self) -> LatexCompoundBlock:
        if self.sourcename:
            self.sourcepath = path_resolver(self.sourcename, search_paths=[self.templates_dir])
            with open(self.sourcepath, 'r') as f:
                self.textcontents = f.read()
        elif len(self.pythontex) > 0:
            self.textcontents = r'\begin{pycode}' + '\n'
            for ptfile in self.pythontex:
                ptpath = path_resolver(ptfile, search_paths=[LatexCompoundBlock.pythontex_dir], ext='.pycode')
                with open(ptpath, 'r') as f:
                    self.textcontents += f.read() + '\n\n'
            self.textcontents += r'\end{pycode}' + '\n'
        self.has_pycode = r'\begin{pycode}' in self.textcontents or self.has_pycode
        # check contents for substitution keys and embedded graphics files
        KEY_RE = re.compile(rf'{self.substitution_delimiters[0]}\s*([A-Za-z0-9_-]+)\s*{self.substitution_delimiters[1]}')
        for line in self.textcontents.split('\n'):
            keys = set(KEY_RE.findall(line))
            for key in keys:
                if not key in self.substitution_map:
                    self.substitution_map[key] = None
            # check for embedded graphics
            GRAPHICS_RE = re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{([^\}]+)\}')
            graphics_files = GRAPHICS_RE.findall(line)
            for gf in graphics_files:
                if gf not in self.embedded_graphics:
                    self.embedded_graphics.append(gf)
        self.processedcontents = self.textcontents[:]
        if self.config_path:
            if not self.config_path.exists():
                raise FileNotFoundError(f'Configuration file {self.config_path.as_posix()} does not exist.')
            self.substitution_map['config'] = self.config_path.as_posix()
        if self.points:
            self.substitution_map['points'] = self.points
        if self.group:
            self.substitution_map['group'] = self.group
        self.substitution_map['idx'] = self.idx

        for child in self.children:
            child.load()
            self.has_pycode = child.has_pycode or self.has_pycode
            self.embedded_graphics.extend(child.embedded_graphics)

        logger.debug(f'LatexCompoundBlock.load completed for idx={self.idx} with substitutions: {self.substitution_map}')
        return self

    def substitute(self, super_substitutions: dict = {}, match_all: bool = True):
        self.processedcontents = self.textcontents[:]
        substitutions = deepcopy(super_substitutions)
        logger.debug(f'block at idx {self.idx} incoming substitutions: {substitutions}')
        logger.debug(f'block at idx {self.idx} own substitution_map: {self.substitution_map}')
        substitutions.update({k: v for k, v in self.substitution_map.items() if v is not None})
        logger.debug(f'block at idx {self.idx} substitutions: {substitutions}')
        # apply substitutions to the contents
        for key, value in substitutions.items():
            if value is not None:
                self.processedcontents = self.processedcontents.replace(f'{self.substitution_delimiters[0]}{key}{self.substitution_delimiters[1]}', str(value))
            elif match_all:
                raise KeyError(f'Substitution key {key} has no associated value for text {self.textcontents[:30]}...')
        # apply substitutions to children
        for child in self.children:
            child.substitute(super_substitutions=substitutions, match_all=match_all)

    def copy_referenced_configs(self, output_dir: str):
        config_paths = []
        if self.config_path and self.config_path.exists():
            dest_path = Path(output_dir) / self.config_path.name
            if not dest_path.exists():
                copy2(self.config_path, dest_path)
                logger.debug(f'Copied config file {self.config_path} to {dest_path}')
            config_paths.append(str(dest_path))
        for child in self.children:
            child_paths = child.copy_referenced_configs(output_dir)
            if child_paths:
                config_paths.extend(child_paths)
        return config_paths

    def __str__(self):
        contents = self.processedcontents
        if self.enumerate:
            enum_str = r'\begin{enumerate}' + '\n'
            for item in self.enumerate:
                enum_str += r'\item ' + str(item) + '\n'
            enum_str += r'\end{enumerate}' + '\n'
            contents += '\n' + enum_str
        if self.itemize:
            item_str = r'\begin{itemize}' + '\n'
            for item in self.itemize:
                item_str += r'\item ' + str(item) + '\n'
            item_str += r'\end{itemize}' + '\n'
            contents += '\n' + item_str
        return contents