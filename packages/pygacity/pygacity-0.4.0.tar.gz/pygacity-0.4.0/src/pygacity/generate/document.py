# Author: Cameron F. Abrams, <cfa22@drexel.edu>
import logging

from copy import deepcopy
from importlib.resources import files
from pathlib import Path

from .block import LatexCompoundBlock

logger = logging.getLogger(__name__)

class Document:
    resources_root: Path = files('pygacity') / 'resources'
    templates_dir: Path = resources_root / 'templates'
    def __init__(self, document_specs: dict):
        self.blocks: list[LatexCompoundBlock] = []
        self.specs = deepcopy(document_specs)
        self.preamble = self.specs.get('preamble', [])
        self.substitutions = self.specs.get('substitutions', {})
        logger.debug(f'Document.__init__ with specs: {self.specs}')
        for idx, section in enumerate(self.specs['structure']):
            assert type(section) == dict
            self.blocks.append(LatexCompoundBlock(block_specs=section, parent_idx='', idx=idx+1).load())
            logger.debug(f'Added block for top section {idx}: {section}')
        self.has_pycode = any(block.has_pycode for block in self.blocks)
        self.embedded_graphics = []
        for block in self.blocks:
            self.embedded_graphics.extend(block.embedded_graphics)
            
    def make_substitutions(self, outer_substitutions: dict = {}):
        self.substitutions.update(deepcopy(outer_substitutions))
        logger.debug(f'Document.make_substitutions with substitutions: {self.substitutions}')
        for block in self.blocks:
            block.substitute(super_substitutions=self.substitutions)

    def write_source(self, local_output_name: str  = 'local_document'):
        with open(local_output_name + '.tex', 'w') as f:
            f.write('% Automatically generated LaTeX source file\n')
            class_specs = self.specs.get('class', {})
            logger.debug(f'Document.write_source with class_specs: {class_specs}')
            dcoptions = class_specs.get('options', [])
            classname = class_specs.get('classname', 'article')
            f.write(rf'\documentclass[{", ".join(dcoptions)}]{{{classname}}}' + '\n')
            f.write(str(self.preamble) + '\n')
            for block in self.blocks:
                f.write(str(block) + '\n')
            f.write('% End of automatically generated LaTeX source file\n')


   