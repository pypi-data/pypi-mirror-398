# Author: Cameron F. Abrams, <cfa22@drexel.edu>
from copy import deepcopy
import logging
import os
import pickle
import stat
import random
from shutil import rmtree
from pathlib import Path
from .answerset import AnswerSet, AnswerSuperSet
from .config import Config
from .document import Document
from ..util.stringthings import chmod_recursive
from ..util.collectors import FileCollector
from ..util.texutils import LatexBuilder
from pathlib import Path
from importlib.resources import files

logger = logging.getLogger(__name__)

logging.getLogger("ycleptic").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

def build(args):
    FC = FileCollector()
    if hasattr(args, 'f') and args.f:
        logger.info(f'Building document(s) as specified in {args.f}...')
        config = Config(args.f)
    else:
        config = Config()
        if hasattr(args, 'texfile') and args.texfile:
            docspecs, buildspecs = config_singlet(args)
            config.document_specs = docspecs
            config.build_specs = buildspecs
        else:
            raise KeyError(f'No config file nor singlet tex file specified. No build is possible.')

    seed = config.build_specs.get('seed', None)
    if seed is not None:
        random.seed(seed)
        logger.info(f'Setting random seed to {seed}.')

    build_path: Path = Path(config.build_specs['paths']['build-dir'])
    if not build_path.exists():
        build_path.mkdir(parents=True, exist_ok=True)
    else:
        if args.overwrite:
            permissions = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
            chmod_recursive(build_path, permissions)
            rmtree(build_path)
            build_path.mkdir(parents=True, exist_ok=True)
        else:
            raise Exception(f'Build directory "{build_path.as_posix()}" already exists and "--overwrite" was not specified.')

    pickle_cache = build_path / config.pickle_cache_name
    if not pickle_cache.exists():
        pickle_cache.mkdir(parents=True, exist_ok=True)

    base_builder = LatexBuilder(config.build_specs, 
                                 searchdirs = [config.autoprob_package_dir])
    base_doc = Document(config.document_specs)
    logger.debug(f'base_doc has {len(base_doc.blocks)} blocks')
    if args.solutions:
        solution_build_specs = deepcopy(config.build_specs)
        # solution_build_specs['output-name'] = config.build_specs.get('output-name', 'document') + '_soln'
        solution_build_specs['job-name'] = config.build_specs.get('job-name', 'document') + '_soln'
        soln_builder = LatexBuilder(solution_build_specs,
                                    searchdirs = [config.autoprob_package_dir])
        
        solution_document_specs = deepcopy(config.document_specs)
        solution_document_specs['class']['options'].append('solutions')
        solution_doc = Document(solution_document_specs)
        logger.debug(f'solution_doc has {len(solution_doc.blocks)} blocks')

    if build_path != Path.cwd():
        # find any configs referenced in document blocks and copy them to output_dir
        for block in base_doc.blocks:
            file_or_files_or_none = block.copy_referenced_configs(build_path)
            if file_or_files_or_none:
                if isinstance(file_or_files_or_none, list):
                    for f in file_or_files_or_none:
                        FC.append(f)
                else:
                    FC.append(file_or_files_or_none)

    if config.build_specs.get('copies', 1) > 1:
        if config.build_specs.get('serials', None):
            # check for explict serials
            serials = [int(x) for x in config.build_specs['serials']]
        elif config.build_specs.get('serial-range', None):
            # check for a serial range
            serials = list(range(config.build_specs['serial-range'][0],
                                 config.build_specs['serial-range'][1] + 1))
        elif config.build_specs.get('serial-file', None):
            # check for a file containing serials, one integer per line
            with open(config.build_specs['serial-file'], 'r') as f:
                serials = [int(line.strip()) for line in f if line.strip()]
        else:
            serial_digits = config.build_specs.get('serial-digits', len(str(config.build_specs['copies'])))
            # generate 'copies' random serial numbers
            serials = set()
            while len(serials) < config.build_specs['copies']:
                serial = random.randint(10**(serial_digits-1), 10**serial_digits - 1)
                serials.add(serial)
            serials = list(serials)
            serials.sort()
    else:
        if config.build_specs.get('serials', None):
            # check for explict serials
            serials = [int(x) for x in config.build_specs['serials']]
        else:
            serials = [0]

    for i, serial in enumerate(serials):
        outer_substitutions = dict(serial=serial)
        base_doc.make_substitutions(outer_substitutions)
        base_builder.build_document(base_doc)
        FC.append(f'{base_builder.working_job_name}.tex')
        logger.info(f'serial # {serial} ({i+1}/{len(serials)}) => {build_path.absolute().relative_to(Path.cwd()).as_posix()}/{base_builder.working_job_name}.pdf')
        if args.solutions:
            solution_doc.make_substitutions(outer_substitutions)
            soln_builder.build_document(solution_doc)
            FC.append(f'{soln_builder.working_job_name}.tex')
            logger.info(f'serial # {serial} ({i+1}/{len(serials)}) => {build_path.absolute().relative_to(Path.cwd()).as_posix()}/{soln_builder.working_job_name}.pdf')

    if pickle_cache.exists():
        # there may be a pickle file for each serial that holds a FileCollector instance
        commonFC = FileCollector()
        for pfile in pickle_cache.glob('pythontex*.pkl'):
            with pfile.open('rb') as f:
                obj = pickle.load(f)
            if isinstance(obj, FileCollector):
                for item in obj.data:
                    commonFC.append(build_path / item)
            else:
                logger.debug(f'Unrecognized object type {type(obj)} in pickle file {pfile.as_posix()}')
            logger.debug(f'Removing pickle cache file {pfile.as_posix()}')
            pfile.unlink()
        
        archive_path = build_path / 'common_files_from_pickle_cache'
        common_archive = commonFC.archive(archive_path, delete=True)
        logger.info(f'Archived common files from pickle cache to {common_archive.absolute().relative_to(Path.cwd()).as_posix()}')
        logger.debug(f'Retaining pickle cache at {pickle_cache.as_posix()}')
        FC.append(answerset(config))

    for f in FC.data:
        logger.debug(f'Generated file: {f.absolute().relative_to(Path.cwd()).as_posix()}')
    tex_archive = FC.archive(build_path / 'tex_artifacts', delete=True)
    logger.info(f'Archived TeX artifacts to {tex_archive.absolute().relative_to(Path.cwd()).as_posix()}')
    buildfiles_archive = base_builder.FC.archive(build_path / 'buildfiles', delete=True)
    logger.info(f'Archived build files to {buildfiles_archive.absolute().relative_to(Path.cwd()).as_posix()}')
    if args.solutions:
        solnbuildfiles_archive = soln_builder.FC.archive(build_path / 'solnbuildfiles', delete=True)
        logger.info(f'Archived solution build files to {solnbuildfiles_archive.absolute().relative_to(Path.cwd()).as_posix()}')

def answerset(config: Config = None) -> str:
    build_path: Path = Path(config.build_specs['paths']['build-dir'])
    pickle_cache = build_path / config.pickle_cache_name
    if not pickle_cache.exists():
        raise Exception(f'No cache found -- cannot build answer set')
    AnswerSets: list[AnswerSet] = []
    for pfile in pickle_cache.glob('answer*.pkl'):
        with pfile.open('rb') as f:
            obj = pickle.load(f)
        AnswerSets.append(obj)
    AS = AnswerSuperSet(initial=AnswerSets)

    answer_buildspecs = {'job-name': config.build_specs.get('answer-name', 'answerset'),
                         'paths': config.build_specs['paths']}
    AnswerSetBuilder = LatexBuilder(answer_buildspecs,
                                    searchdirs = [config.autoprob_package_dir])
    
    answer_docspecs = deepcopy(config.document_specs) 
    answer_docspecs['structure'] = [] 
    answer_docspecs['structure'].append(deepcopy(config.document_specs['structure'][0]))
    answer_docspecs['structure'].append({'text': AS.to_latex()})
    answer_docspecs['structure'].append(deepcopy(config.document_specs['structure'][-1]))
    AnswerSetDoc = Document(answer_docspecs)
    AnswerSetDoc.make_substitutions(dict(serial='Answer Set'))
    AnswerSetBuilder.build_document(AnswerSetDoc)
    logger.info(f'Combined answer set => {build_path.absolute().relative_to(Path.cwd()).as_posix()}/{AnswerSetBuilder.working_job_name}.pdf')
    answerset_archive = AnswerSetBuilder.FC.archive(build_path / 'answerset_buildfiles', delete=True)
    logger.info(f'Archived answer set build files to {answerset_archive.absolute().relative_to(Path.cwd()).as_posix()}')
    return Path.cwd() / f'{AnswerSetBuilder.working_job_name}.tex'

def answerset_subcommand(args):
    logger.info(f'Generating answer set document from previous build specified in {args.f}...')
    config = Config(args.f)
    tex_file = answerset(config)
    # remove the tex source
    os.remove(tex_file)

def config_singlet(args):
    """
    Builds a solution document for a single input tex file, no input config needed
    """
    tex_sourcefile = args.texfile
    docspecs = {
        'class': {
            'classname': 'autoprob',
            'options': [
                '11pt',
                'solutions'
            ]
        },
        'preamble': r"""
\usepackage[T1]{fontenc}
\usepackage{tgheros}
\renewcommand{\sfdefault}{qhv}
\renewcommand{\familydefault}{\sfdefault}""",
        'structure': [
            {'text': r'\begin{document}'},
            {'pythontex': [
                'setup',
                'matplotlib',
                'sandlersteam',
                'chemeq'
            ]},
            {'enumerate':[
                {'source': tex_sourcefile,
                 'group': 1}
            ]},
            {'pythontex': [
                'showsteamtables',
                'teardown'
            ]},
            {'text': r'\end{document}'}
        ]
    }
    buildspecs = {
        'copies': 1,
        'job-name': Path(tex_sourcefile).stem + '-singlet',
        'paths': {
            'build-dir': './build_singlet',
            'pdflatex': 'pdflatex',
            'pythontex': 'pythontex'
        }
    }

    return docspecs, buildspecs
    