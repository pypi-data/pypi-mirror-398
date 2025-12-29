# Author: Cameron F. Abrams, <cfa22@drexel.edu>
""" Defines the ByteCollector and FileCollector classes
"""
import logging
import os
import shutil
from pathlib import Path
import pandas as pd

from io import StringIO

logger=logging.getLogger(__name__)

_SYMBOLS_={
    'ANGSTROM':'Å',
    'CUBED':'³',
    'SQUARED':'²'
}
_UNITS_={
    'SQUARE-ANGSTROMS':f'{_SYMBOLS_["ANGSTROM"]}{_SYMBOLS_["SQUARED"]}',
    'CUBIC-ANGSTROMS':f'{_SYMBOLS_["ANGSTROM"]}{_SYMBOLS_["CUBED"]}',
    }

import importlib.metadata

__pygacity_version__ = importlib.metadata.version("pygacity")

banner_message=f"""

░       ░░░  ░░░░  ░░░      ░░░░      ░░░░      ░░░        ░░        ░░  ░░░░  ░
▒  ▒▒▒▒  ▒▒▒  ▒▒  ▒▒▒  ▒▒▒▒▒▒▒▒  ▒▒▒▒  ▒▒  ▒▒▒▒  ▒▒▒▒▒  ▒▒▒▒▒▒▒▒  ▒▒▒▒▒▒  ▒▒  ▒▒
▓       ▓▓▓▓▓    ▓▓▓▓  ▓▓▓   ▓▓  ▓▓▓▓  ▓▓  ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓    ▓▓▓
█  ███████████  █████  ████  ██        ██  ████  █████  ████████  ████████  ████
█  ███████████  ██████      ███  ████  ███      ███        █████  {__pygacity_version__:█^8s}  ████

    (\"pie-GAS-ity\")
    
    Cameron F. Abrams <cfa22@drexel.edu>

"""

def banner(logf):
    my_logger(banner_message,logf,fill=' ',just='<')

def my_logger(msg,logf,width=None,fill='',just='<',frame='',depth=0,**kwargs):
    """A fancy logger
    
    Parameters
    ----------
    msg: str, list
       the message to be logged, either as a single string, list, or dict
    
    logf: function
       writer; e.g., print, f.write, etc.

    width: int, optional
       linelength in bytes

    fill: str, optional
       single character used to fill blank spaces

    sep: str, optional
       single character used in join calls

    just: str, optional
       format character
    """
    if width is None:
        if logf is print:
            ts=shutil.get_terminal_size((80,20))
            width=ts.columns
        else:
            width=67
    fmt=r'{'+r':'+fill+just+f'{width}'+r'}'
    ll=' ' if just in '^>' else ''
    rr=' ' if just in '^<' else ''
    if frame:
        ffmt=r'{'+r':'+frame+just+f'{width}'+r'}'
        logf(ffmt.format(frame))
    if type(msg)==list:
        for tok in msg:
            my_logger(tok,logf,width=width,fill=fill,just=just,frame=False,depth=depth,kwargs=kwargs)
    elif type(msg)==dict:
        for key,value in msg.items():
            if type(value)==str or not hasattr(value,"__len__"):
                my_logger(f'{key}: {value}',logf,width=width,fill=fill,just=just,frame=False,depth=depth,kwargs=kwargs)
            else:
                my_logger(f'{key}:',logf,width=width,fill=fill,just=just,frame=False,depth=depth,kwargs=kwargs)
                my_logger(value,logf,width=width,fill=fill,just=just,frame=False,depth=depth+1,kwargs=kwargs)
    elif type(msg)==pd.DataFrame:
        dfoutmode=kwargs.get('dfoutmode','value')
        if dfoutmode=='value':
            my_logger([ll+x+rr for x in msg.to_string().split('\n')],logf,width=width,fill=fill,just=just,frame=False,depth=depth,kwargs=kwargs)
        elif dfoutmode=='info':
            buf=StringIO()
            msg.info(buf=buf)
            my_logger([ll+x+rr for x in buf.getvalue().split('\n')],logf,width=width,fill=fill,just=just,frame=False,depth=depth,kwargs=kwargs)
        else:
            return
    else:
        indent=f'{" "*depth*2}' if just=='<' and not kwargs.get('no_indent',False) else ''
        if type(msg)==str:
            lns=msg.split('\n')
            if len(lns)>1:
                my_logger(lns,logf,width=width,fill=fill,just=just,frame=False,depth=depth+1,kwargs=kwargs)
            else:
                outstr=indent+ll+f'{msg}'+rr
                logf(fmt.format(outstr))
        else:
            outstr=indent+ll+f'{msg}'+rr
            logf(fmt.format(outstr))
    if frame:
        logf(ffmt.format(frame))
            

def oxford(a_list,conjunction='or'):
    """ returns a comma-delimited string of items in a_list, following the oxford comma rules including a terminal conjuction (default is 'or') """
    if not a_list: return ''
    if len(a_list)==1:
        return a_list[0]
    elif len(a_list)==2:
        return f'{a_list[0]} {conjunction} {a_list[1]}'
    else:
        return ", ".join(a_list[:-1])+f', {conjunction} {a_list[-1]}'
    
def linesplit(line,cchar='!'):
    """ splits the single string 'line' into to substrings at first occurrence of 'cchar' and returns the two strings as a tuple """
    if not cchar in line:
        return line,''
    idx=line.index(cchar)
    if idx==0:
        return '',line[1:]
    return line[:idx],line[idx+1:]

def striplist(L):
    """ removes all blank bytes from all members of list L and returns a new list """
    l=[x.strip() for x in L]
    while '' in l:
        l.remove('')
    return l

def chmod_recursive_dirs_files(path: Path, dmode=0o755, fmode=0o644):
    path.chmod(dmode)
    for p in path.rglob("*"):
        if p.is_dir():
            p.chmod(dmode)
        else:
            p.chmod(fmode)


def chmod_recursive(path, mode):
    """
    Recursively changes permissions of a directory and its contents.
    
    :param path: The root directory to change permissions for.
    :param mode: The mode (permissions) to apply.
    """
    for root, dirs, files in os.walk(path):
        # Change permissions for directories
        for dirname in dirs:
            dir_path = os.path.join(root, dirname)
            os.chmod(dir_path, mode)
        
        # Change permissions for files
        for filename in files:
            file_path = os.path.join(root, filename)
            os.chmod(file_path, mode)
    
    # Change permissions for the root directory itself
    os.chmod(path, mode)