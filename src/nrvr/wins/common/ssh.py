#!/usr/bin/python

"""nrvr.wins.common.ssh - Remote commands over ssh to Cygwin

The main class provided by this module is CygwinSshCommand.

CygwinSshCommand inherits from nrvr.remote.ssh.SshCommand,
including limitations documented there.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

import re
import sys
import time

from nrvr.remote.ssh import SshCommand
from nrvr.util.classproperty import classproperty
from nrvr.util.ipaddress import IPAddress

class CygwinSshCommand(SshCommand):
    """Send a command over ssh to Cygwin."""

    def __init__(self, sshParameters, argv,
                 exceptionIfNotZero=True,
                 maxConnectionRetries=10,
                 tickerForRetry=True):
        """Create new CygwinSshCommand instance.
        
        See nrvr.remote.ssh.SshCommand."""
        super(CygwinSshCommand, self).__init__ \
        (sshParameters=sshParameters, \
         argv=argv, \
         exceptionIfNotZero=exceptionIfNotZero, \
         maxConnectionRetries=maxConnectionRetries, \
         tickerForRetry=tickerForRetry)

    _isGuiAvailableRegex = re.compile(r"[1-9]") # any number larger than 0
    _isScreenAvailableRegex = re.compile(r"[1-9]") # any number larger than 0

    @classmethod
    def isGuiAvailable(cls, sshParameters, alsoNeedsScreen=False):
        """Return whether GUI is available.
        
        Should be user to be meaningful.
        
        Will wait until completed.
        
        sshParameters
            an SshParameters instance."""
        try:
            # see http://cygwin.com/ml/cygwin/2010-01/msg00644.html
            # see http://blogs.technet.com/b/heyscriptingguy/archive/2011/03/17/use-powershell-to-detect-if-a-workstation-is-in-use.aspx
            guiProbingCommand = r"ps -u $UID -W | grep -c '\\explorer\.exe'"
            guiSshCommand = CygwinSshCommand(sshParameters,
                                             argv=[guiProbingCommand],
                                             maxConnectionRetries=1)
            if cls._isGuiAvailableRegex.search(guiSshCommand.output):
                if not alsoNeedsScreen:
                    return True
                else:
                    screenProbingCommand = r"""screen -wipe | grep -c 'wguifor_'"$USERNAME"'\s\s*(Detached'"""
                    screenSshCommand = CygwinSshCommand(sshParameters,
                                                        argv=[screenProbingCommand],
                                                        maxConnectionRetries=1)
                    if cls._isScreenAvailableRegex.search(screenSshCommand.output):
                        return True
                    else:
                        return False
            else:
                return False
        except Exception as e:
            return False

    @classmethod
    def sleepUntilIsGuiAvailable(cls, sshParameters,
                                 alsoNeedsScreen=False,
                                 checkIntervalSeconds=3.0, ticker=False,
                                 extraSleepSeconds=5.0):
        """If GUI available return, else loop sleeping for checkIntervalSeconds.
        
        Should be user to be meaningful.
        
        As implemented first calls SshCommand.sleepUntilIsAvailable(sshParameters).
        
        sshParameters
            an SshParameters instance."""
        cls.sleepUntilIsAvailable(sshParameters,
                                  checkIntervalSeconds=checkIntervalSeconds, ticker=ticker)
        printed = False
        ticked = False
        # check the essential condition, initially and then repeatedly
        while not cls.isGuiAvailable(sshParameters, alsoNeedsScreen=alsoNeedsScreen):
            if not printed:
                # first time only printing
                if not alsoNeedsScreen:
                    message = "waiting for GUI to be available to connect to {0}"
                else: # alsoNeedsScreen
                    message = "waiting for GUI and screen to be available to connect to {0}"
                print message.format(IPAddress.asString(sshParameters.ipaddress))
                sys.stdout.flush()
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
        if extraSleepSeconds:
            time.sleep(extraSleepSeconds)

if __name__ == "__main__":
    from nrvr.util.requirements import SystemRequirements
    SystemRequirements.commandsRequiredByImplementations([CygwinSshCommand], verbose=True)
