#!/usr/bin/python

"""nrvr.wins.common.javaw - A download manager for Java for Windows installs

Class provided by this module is JavawDownload.

As implemented works in Linux and Mac OS X, uses wget.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

import os
import os.path
import sys

from nrvr.process.commandcapture import CommandCapture
from nrvr.util.user import ScriptUser

class Arch(str): pass # make sure it is a string to avoid string-number unequality

class JavawDownload(object):
    """A download manager for Java for Windows installs."""

    semaphoreExtenstion = ".wait"

    @classmethod
    def commandsUsedInImplementation(cls):
        """Return a list to be passed to SystemRequirements.commandsRequired().
        
        This class can be passed to SystemRequirements.commandsRequiredByImplementations()."""
        return ["wget", "sed"]

    @classmethod
    def _currentOfflineInstallerUrl(cls):
        """Auxiliary method."""
        offlineInstallerPageUrl = r"http://java.com/en/download/windows_offline.jsp"
        sedToExtractDownloadUrl = r"sed -n -e 's/.*\(http:\/\/.*BundleId=[0-9]*\).*/\1/p'"
        wget = CommandCapture(
            ["sh",
             "-c", "wget -q -O- " + offlineInstallerPageUrl + r" | " + sedToExtractDownloadUrl],
            copyToStdio=False,
            forgoPty=True)
        if not wget.stdout:
            raise Exception("not able to get offline installer URL from {0}".format(offlineInstallerPageUrl))
        return wget.stdout.strip()

    @classmethod
    def now(cls,
            force=False,
            dontDownload=False,
            ticker=True):
        """Download file or use previously downloaded file.
        
        As implemented uses wget.
        That has been a choice of convenience, could be written in Python instead.
        
        force
            whether to force downloading even if apparently downloaded already.
            
            May be useful for programmatically updating at times.
        
        dontDownload
            whether you don't want to start a download, for some reason.
        
        Return file path."""
        simpleFilename = "jre-version-windows-arch.exe"
        downloadDir = ScriptUser.loggedIn.userHomeRelative("Downloads")
        downloadPath = os.path.join(downloadDir, simpleFilename)
        semaphorePath = downloadPath + cls.semaphoreExtenstion
        #
        if os.path.exists(downloadPath) and not force:
            if not os.path.exists(semaphorePath):
                # file exists and not download in progress,
                # assume it is good
                return downloadPath
            else:
                # file exists and download in progress,
                # presumably from another script running in another process or thread,
                # wait for it to complete
                printed = False
                ticked = False
                # check the essential condition, initially and then repeatedly
                while os.path.exists(semaphorePath):
                    if not printed:
                        # first time only printing
                        print "waiting for " + semaphorePath + " to go away on completion"
                        sys.stdout.flush()
                        printed = True
                    if ticker:
                        if not ticked:
                            # first time only printing
                            sys.stdout.write("[")
                        sys.stdout.write(".")
                        sys.stdout.flush()
                        ticked = True
                    time.sleep(5)
                if ticked:
                    # final printing
                    sys.stdout.write("]\n")
                    sys.stdout.flush()
        elif not dontDownload: # it is normal to download
            if not os.path.exists(downloadDir):
                try:
                    os.makedirs(downloadDir)
                except OSError:
                    if os.path.exists(downloadDir): # concurrently made
                        pass
                    else: # failure
                        raise
            #
            # try downloading
            pid = os.getpid()
            try:
                with open(semaphorePath, "w") as semaphoreFile:
                    # create semaphore file
                    semaphoreFile.write("pid=" + str(pid))
                #
                offlineInstallerUrl = cls._currentOfflineInstallerUrl()
                print "starting to download " + offlineInstallerUrl
                if ticker:
                    sys.stdout.write("[.")
                    sys.stdout.flush()
                try:
                    wget = CommandCapture(
                        ["wget",
                         "--quiet",
                         "-O", downloadPath,
                         offlineInstallerUrl],
                        forgoPty=True)
                    if ticker:
                        sys.stdout.write("]")
                        sys.stdout.flush()
                finally:
                    if ticker:
                        sys.stdout.write("\n")
                        sys.stdout.flush()
            except: # apparently a problem
                print "problem downloading " + downloadPath + " from " + offlineInstallerUrl
                raise
            else:
                print "done downloading " + downloadPath
            finally:
                try:
                    # delete semaphore file
                    os.remove(semaphorePath)
                except:
                    pass
        if os.path.exists(downloadPath):
            # file exists now, assume it is good
            return downloadPath
        else:
            # apparently download has failed
            raise IOError("file not found " + downloadPath)

if __name__ == "__main__":
    _exampleDownload = JavawDownload.now()
    print _exampleDownload
    _exampleDownload2 = JavawDownload.now(dontDownload=True)
    print _exampleDownload2
