# -*- coding: us-ascii -*-
"""Mixed utilities."""
from os import path
import sys
import logging
import argparse


def generateCf(filename, template):
    if not path.exists(path.dirname(filename)):
        print("Error, path for controlfile does not exist")
    if path.exists(filename):
        answer = raw_input("File already exists, replace? (y/n)")
        if answer == "n":
            sys.exit(0)
        elif answer == "y":
            fid = open(filename, "w")
            fid.write(template)
            fid.close()
        else:
            print("Invalid answer (should be y or n)")
            sys.exit(1)
    else:
        fid = open(filename, "w")
        fid.write(template)
        fid.close()

        
def create_terminal_handler(loglevel=logging.INFO, prog=None):
    """Configure a log handler for the terminal."""
    if prog is None:
        prog = path.basename(sys.argv[0])
        streamhandler = logging.StreamHandler()
        streamhandler.setLevel(loglevel)
        format = ': '.join((prog, '%(levelname)s', '%(message)s'))
        streamformatter = logging.Formatter(format)
        streamhandler.setFormatter(streamformatter)
        return streamhandler

    
def create_file_handler(filename, loglevel=logging.DEBUG):
    """Configure a log handler for *filename*."""
    filehandler = logging.FileHandler(filename, mode='w', encoding='utf-8')
    filehandler.setLevel(logging.DEBUG)
    fmt = '%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s'
    fileformatter = logging.Formatter(fmt)
    filehandler.setFormatter(fileformatter)
    return filehandler

    
class VerboseAction(argparse.Action):

    """Argparse action to handle terminal verbosity level."""

    def __init__(self, option_strings, dest,
                 default=logging.WARNING, help=None):
        baselogger = logging.getLogger()
        baselogger.setLevel(logging.DEBUG)
        self._loghandler = create_terminal_handler(default)
        baselogger.addHandler(self._loghandler)
        super(VerboseAction, self).__init__(
            option_strings, dest,
            nargs=0,
            default=default,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        currentlevel = getattr(namespace, self.dest, logging.WARNING)
        self._loghandler.setLevel(currentlevel - 10)
        setattr(namespace, self.dest, self._loghandler.level)


class LogFileAction(argparse.Action):

    """Argparse action to setup logging to file."""

    def __call__(self, parser, namespace, values, option_string=None):
        baselogger = logging.getLogger()
        baselogger.addHandler(create_file_handler(values))
        setattr(namespace, self.dest, values)
