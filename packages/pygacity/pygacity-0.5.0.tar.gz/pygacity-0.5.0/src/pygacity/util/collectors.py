import logging
import os
import shutil
import sys
import tarfile

from collections import UserList
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from .stringthings import my_logger

logger = logging.getLogger(__name__)

class ByteCollector:
    """A simple string manager
    
    The main object in a ByteCollector instance is a string of bytes (byte_collector).
    The string can be appended to by anoter string or the contents of a file.
    The string can have "comments" written to it.

    Attributes
    ----------
    byte_collector: str
       the string
    
    line_length: int
       number of bytes that represents the maximum length of one line of text
    
    comment_char: str(1)
       beginning-of-line character that signals the line is a comment

    Methods
    -------
    reset()
        blanks the string
    
    write(msg)
        appends msg to string

    addline(msg)
        appends msg to string with a line-end byte
        
    injest_file(filename)
        appends the contents of filename to the string
    
    comment(msg)
        appends the msg as a comment (or multiple comment
        lines) to the string

    log(msg)
        uses the auxiliary function my_logger to write
        a log line to the string
    
    banner(msg)
        uses the auxiliary function my_logger to write
        a banner line to the string
    
    """
    def __init__(self, comment_char='#', line_length=80):
        self.line_length=line_length
        self.comment_char=comment_char
        self.byte_collector=''
    
    def reset(self):
        """Resets the string"""
        self.byte_collector=''

    def write(self,msg):
        """Appends msg to the string
        
        Parameters
        ----------
        msg: str            for ln in:
                outstr=ll+ln+rr
                logf(fmt.format(outstr))

           the message
        """
        self.byte_collector+=msg

    def addline(self,msg,end='\n'):
        """Appends msg to the string as a line
        
        Parameters
        ----------
        msg: str
           the message
        
        end: str, optional
            end-of-line byte
        """
        self.byte_collector+=f'{msg}{end}'

    def lastline(self,end='\n',exclude='#'):
        """Returns last line in the string
        
        Parameters
        ----------
        end: str, optional
            end-of-line byte
        exclude: str, optional
            comment byte
        """
        lines=[x for x in self.byte_collector.split(end) if (len(x)>0 and not x.startswith(exclude))]
        if len(lines)>0:
            return lines[-1]
        else:
            return None
    
    def has_statement(self,statement,end='\n',exclude='#'):
        """Determines if a particular statement is on at least one non-comment line
        
        Parameters
        ----------
        statement: str
            the statement; e.g., 'exit'
        end: str, optional
            end-of-line byte
        exclude: str, optional
            comment byte
        """
        lines=[x for x in self.byte_collector.split(end) if (len(x)>0 and not x.startswith(exclude))]
        if len(lines)>0:
            for l in lines:
                if statement in l:
                    return True
        return False
    
    def injest_file(self,filename):
        """Appends contents of file 'filename' to the string
        
        Parameters
        ----------
        filename: str
           the name of the file
        """
        with open(filename,'r') as f:
            self.byte_collector+=f.read()

    def comment(self,msg,end='\n'):
        """Appends msg as a comment to the string
        
        Parameters
        ----------
        msg: str
           the message
        
        end: str, optional
            end-of-line byte
        """
        comment_line=f'{self.comment_char} {msg}'
        comment_words=comment_line.split()
        comment_lines=['']
        current_line_idx=0
        for word in comment_words:
            test_line=' '.join(comment_lines[current_line_idx].split()+[word])
            if len(test_line)>self.line_length:
                comment_lines.append(f'{self.comment_char} {word}')
                current_line_idx+=1
            else:
                comment_lines[current_line_idx]=test_line
        for line in comment_lines:
            self.addline(line,end=end)

    def log(self,msg):
        my_logger(msg,self.addline)

    def banner(self,msg):
        my_logger(msg,self.addline,fill='#',width=80,just='^')

    def __str__(self):
        return self.byte_collector
    
class FileCollector(UserList):
    """A class for handling collections of files
    
    Methods
    -------
    flush()
       remove all files in the collection
       
    archive()
       make a tarball or zipfile of the collection
    """

    def __init__(self, initial: list[str | Path] = None):
        self.data: list[Path] = [Path(x) for x in initial] if initial is not None else []
        super().__init__(self.data)

    def append(self, item: str | Path):
        p = Path(item)
        if p not in self.data:
            self.data.append(p) 

    def flush(self):
        logger.debug(f'Flushing file collector: {len(self.data)} entries.')
        for f in self.data:
            if f.is_file():
                # logger.debug(f'Deleting file {f.as_posix()} exists? {f.exists()}')
                f.unlink()
                # logger.debug(f'  -> exists? {f.exists()}')
            elif f.is_dir():
                # logger.debug(f'Deleting directory {f.as_posix()} exists? {f.exists()}')
                shutil.rmtree(f)
                # logger.debug(f'  -> exists? {f.exists()}')
            else:
                logger.debug(f'FileCollector.flush: path {f.as_posix()} does not exist.')
        self.clear()

    def __str__(self):
        cwd = Path.cwd()
        return ' '.join([x.relative_to(cwd).as_posix() for x in self.data])

    def archive(self, basepath: Path, delete=False):
        """If Linux, makes a tarball of the files in the collection; if Windows, makes a zipfile 
        
        Parameters
        ----------
        basename: str
            basename of the resulting tarball or zipfile
        """
        # check the OS type first
        arcname = ''
        if sys.platform.startswith('win'):
            # Windows: make a zipfile
            zippath = basepath.with_suffix('.zip')
            with ZipFile(zippath, 'w', ZIP_DEFLATED) as zf:
                for src in self.data:
                    if src.is_file():
                        zf.write(src, arcname=src.name)
                    else:
                        for p in src.rglob("*"):
                            logger.debug(f'adding {p} to zipfile')
                            if p.is_file():
                                zf.write(p, arcname=p.relative_to(basepath.parent))
            logger.debug(f'generated zipfile {zippath}')
            arcname = zippath
        else:
            tgzpath = basepath.with_suffix('.tgz')
            with tarfile.open(tgzpath, 'w:gz') as tf:
                for f in self.data:
                    tf.add(f, arcname=f.name)
            logger.debug(f'generated tarball {tgzpath}')
            arcname = tgzpath
        if delete:
            self.flush()
        return arcname
