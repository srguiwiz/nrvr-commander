#!/usr/bin/python

"""nrvr.el.ssh - Remote commands over ssh to Enterprise Linux

The main class provided by this module is ElSshCommand.

ElSshCommand inherits from nrvr.remote.ssh.SshCommand,
including limitations documented there.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import os.path
import re
import sys
import time

from nrvr.el.gnome import Gnome
from nrvr.remote.ssh import SshCommand
from nrvr.util.classproperty import classproperty
from nrvr.util.ipaddress import IPAddress

class ElSshCommand(SshCommand):
    """Send a command over ssh to Enterprise Linux."""

    @classmethod
    def commandsUsedInImplementation(cls):
        """Return a list to be passed to SystemRequirements.commandsRequired().
        
        See nrvr.remote.ssh.SshCommand."""
        return ["ssh"]

    def __init__(self, sshParameters, argv,
                 exceptionIfNotZero=True):
        """Create new ElSshCommand instance.
        
        See nrvr.remote.ssh.SshCommand."""
        super(ElSshCommand, self).__init__(sshParameters, argv, exceptionIfNotZero)

    _isGuiAvailableRegex = re.compile(r"^\s*available")

    @classmethod
    def isGuiAvailable(cls, sshParameters):
        """Return whether GUI is available.
        
        Should be user to be meaningful.
        
        Will wait until completed.
        
        sshParameters
            an SshParameters instance."""
        try:
            probingCommand = Gnome.commandToTellWhetherGuiIsAvailable()
            sshCommand = ElSshCommand(sshParameters,
                                      argv=[probingCommand])
            if ElSshCommand._isGuiAvailableRegex.search(sshCommand.output):
                return True
            else:
                return False
        except Exception as e:
            return False

    @classmethod
    def sleepUntilIsGuiAvailable(cls, sshParameters,
                                 checkIntervalSeconds=5.0, ticker=False):
        """If GUI available return, else loop sleeping for checkIntervalSeconds.
        
        Should be user to be meaningful.
        
        As implemented first calls SshCommand.sleepUntilIsAvailable(sshParameters).
        
        sshParameters
            an SshParameters instance."""
        SshCommand.sleepUntilIsAvailable(sshParameters,
                                         checkIntervalSeconds=checkIntervalSeconds, ticker=ticker)
        printed = False
        ticked = False
        # check the essential condition, initially and then repeatedly
        while not ElSshCommand.isGuiAvailable(sshParameters):
            if not printed:
                # first time only printing
                print "waiting for GUI to be available to connect to " + IPAddress.asString(sshParameters.ipaddress)
                printed = True
            if ticker:
                if not ticked:
                    # first time only printing
                    sys.stdout.write("[")
                sys.stdout.write(".")
                sys.stdout.flush()
                ticked = True
            time.sleep(checkIntervalSeconds)
        if ticked:
            # final printing
            sys.stdout.write("]\n")

if __name__ == "__main__":
    from nrvr.util.requirements import SystemRequirements
    SystemRequirements.commandsRequiredByImplementations([ElSshCommand], verbose=True)
