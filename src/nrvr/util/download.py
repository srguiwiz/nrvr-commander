#!/usr/bin/python

"""nrvr.util.download - A download manager

Class provided by this module is Download.

Works in Linux and Windows.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import os
import os.path
import posixpath
import shutil
import sys
import urllib2
import urlparse

from nrvr.util.user import ScriptUser

class Download(object):
    """A download manager."""

    semaphoreExtenstion = ".wait"

    @classmethod
    def basename(cls, url):
        """Base name from a dowload URL.
        
        Implemented for the purpose of all code using and relying on this
        one implementation only."""
        urlParseResult = urlparse.urlparse(url)
        baseName = posixpath.basename(urlParseResult.path)
        return baseName

    @classmethod
    def fromUrl(cls, url, ticker=True):
        """Download file or use previously downloaded file.
        
        As implemented uses urllib2.
        
        Return file path."""
        urlFilename = cls.basename(url)
        downloadDir = ScriptUser.loggedIn.userHomeRelative("Downloads")
        if not os.path.exists(downloadDir): # possibly on an international version OS
            os.mkdir(downloadDir)
        downloadPath = os.path.join(downloadDir, urlFilename)
        semaphorePath = downloadPath + cls.semaphoreExtenstion
        #
        if not os.path.exists(downloadDir):
            try:
                os.makedirs(downloadDir)
            except OSError:
                if os.path.exists(downloadDir): # concurrently made
                    pass
                else: # failure
                    raise
        #
        if os.path.exists(downloadPath):
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
        else:
            # try downloading
            pid = os.getpid()
            try:
                with open(semaphorePath, "w") as semaphoreFile:
                    # create semaphore file
                    semaphoreFile.write("pid=" + str(pid))
                #
                print "looking for " + url
                # open connection to server
                urlFileLikeObject = urllib2.urlopen(url)
                with open(downloadPath, "wb") as downloadFile:
                    print "starting to download " + url
                    if ticker:
                        sys.stdout.write("[")
                    # was shutil.copyfileobj(urlFileLikeObject, downloadFile)
                    try:
                        while True:
                            data = urlFileLikeObject.read(1000000)
                            if not data:
                                break
                            downloadFile.write(data)
                            if ticker:
                                sys.stdout.write(".")
                                sys.stdout.flush()
                    finally:
                        if ticker:
                            sys.stdout.write("]\n")
                            sys.stdout.flush()
            except: # apparently a problem
                if os.path.exists(downloadPath):
                    # don't let a bad file sit around
                    try:
                        os.remove(downloadPath)
                    except:
                        pass
                print "problem downloading " + url
                raise
            else:
                print "done downloading " + url
            finally:
                try:
                    # close connection to server
                    os.close(urlFileLikeObject)
                except:
                    pass
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
    _exampleUrl = "http://www.bbc.co.uk/historyofthebbc/img/logos_blocks.jpg"
    print Download.basename(_exampleUrl)
    _exampleFile = Download.fromUrl(_exampleUrl, ticker=False)
    print _exampleFile
    os.remove(_exampleFile)
    _exampleFile = Download.fromUrl(_exampleUrl)
    print _exampleFile
    _exampleFile = Download.fromUrl(_exampleUrl)
    print _exampleFile
    os.remove(_exampleFile)
