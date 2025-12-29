# Author: Cameron F. Abrams, <cfa22@drexel.edu>


import logging
import os
import shutil

import argparse as ap

from .generate.build import build, answerset_subcommand
from .util.pdfutils import combine_pdfs
from .util.stringthings import oxford, banner

logger = logging.getLogger(__name__)

def setup_logging(args):    
    loglevel_numeric = getattr(logging, args.logging_level.upper())
    if args.log:
        if os.path.exists(args.log):
            shutil.copyfile(args.log, args.log+'.bak')
        logging.basicConfig(filename=args.log,
                            filemode='w',
                            format='%(asctime)s %(name)s %(message)s',
                            level=loglevel_numeric
        )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s> %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def cli():
    subcommands = {
        'build': dict(
            func = build,
            help = 'build document',
            ),
        'answerset' : dict(
            func = answerset_subcommand,
            help = 'remake answer set document from a previous build',
        ),
        'combine': dict(
            func = combine_pdfs,
            help = 'combine PDFs',
        )
    }
    parser = ap.ArgumentParser(
        prog='pygacity',
    )
    parser.add_argument(
        '-b',
        '--banner',
        default=True,
        action=ap.BooleanOptionalAction,
        help='toggle banner message'
    )
    parser.add_argument(
        '--logging-level',
        type=str,
        default='debug',
        choices=[None, 'info', 'debug', 'warning'],
        help='Logging level for messages written to diagnostic log'
    )
    parser.add_argument(
        '-l',
        '--log',
        type=str,
        default='pygacity-diagnostics.log',
        help='File to which diagnostic log messages are written'
    )
    subparsers = parser.add_subparsers(
        title="subcommands",
        dest="command",
        metavar="<command>",
        required=True,
    )
    command_parsers={}
    for k, specs in subcommands.items():
        command_parsers[k] = subparsers.add_parser(
            k,
            help=specs['help'],
            formatter_class=ap.RawDescriptionHelpFormatter
        )
        command_parsers[k].set_defaults(func=specs['func'])

    command_parsers['build'].add_argument(
        '-o',
        '--overwrite',
        type=bool,
        default=False,
        action=ap.BooleanOptionalAction,
        help='completely remove old save dir and build new exams')
    command_parsers['build'].add_argument(
        '-s',
        '--solutions',
        type=bool,
        default=True,
        action=ap.BooleanOptionalAction,
        help='build solutions document(s)')
    command_parsers['build'].add_argument(
        'f',
        help='mandatory YAML input file')
    command_parsers['answerset'].add_argument(
        'f',
        help='mandatory YAML input file used in a previous build to generate the answer set')
    command_parsers['combine'].add_argument(
        '-i',
        '--input-pdfs',
        type=str,
        default=[],
        nargs='+',  
        help='space-separated list of PDF file names to combine'
    )
    command_parsers['combine'].add_argument(
        '-o',
        '--pdf-out',
        type=str,
        default='out.pdf',
        help='name of new output PDF to be created')
    
    args = parser.parse_args()

    setup_logging(args)

    if args.banner:
        banner(print)    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        my_list = oxford(list(subcommands.keys()))
        print(f'No subcommand found. Expected one of {my_list}')
    logger.info('Thanks for using pygacity!')
