# -*- coding: us-ascii -*-
"""Mixed utilities."""
from os import path
import sys
import logging
import argparse


def generateCf(filename, template):
    if not path.exists(path.dirname(filename)):
        print "Error, path for controlfile does not exist"
    if path.exists(filename):
        answer = raw_input("File already exists, replace? (y/n)")
        if answer == "n":
            sys.exit(0)
        elif answer == "y":
            fid = open(filename, "w")
            fid.write(template)
            fid.close()
        else:
            print "Invalid answer (should be y or n)"
            sys.exit(1)
    else:
        fid = open(filename, "w")
        fid.write(template)
        fid.close()


class VerboseAction(argparse.Action):

    """Argparse action to handle terminal verbosity level."""

    def __init__(self, option_strings, dest,
                 default=logging.WARNING, help=None):
        baselogger = logging.getLogger()
        baselogger.setLevel(logging.DEBUG)
        self._loghandler = logging.create_terminal_handler(default)
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
        baselogger.addHandler(logging.create_file_handler(values))
        setattr(namespace, self.dest, values)
