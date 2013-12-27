#!/usr/bin/python

"""nrvr.wins.common.cygwin - A download manager for Cygwin installs

Class provided by this module is CygwinDownload.

As implemented works in Linux and Mac OS X, uses wget.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import os
import os.path
import posixpath
import re
import shutil
import sys

from nrvr.process.commandcapture import CommandCapture
from nrvr.util.user import ScriptUser

class Arch(str): pass # make sure it is a string to avoid string-number unequality

class CygwinDownload(object):
    """A download manager for Cygwin installs."""

    semaphoreExtenstion = ".wait"

    @classmethod
    def commandsUsedInImplementation(cls):
        """Return a list to be passed to SystemRequirements.commandsRequired().
        
        This class can be passed to SystemRequirements.commandsRequiredByImplementations()."""
        return ["wget"]

    @classmethod
    def _directoryDepth(cls, directoryUrl):
        """Auxiliary method."""
        return len(filter(None,directoryUrl.split('/'))) - 2;

    @classmethod
    def basename(cls, arch):
        """Base name of directory for architecture.
        
        Implemented for the purpose of all code using and relying on this
        one implementation only."""
        baseName = "cygwin-" + arch
        return baseName

    @classmethod
    def installerName(cls, arch):
        """Exact name of installer command.
        
        Implemented for the purpose of all code using and relying on this
        one implementation only."""
        arch = Arch(arch)
        if arch == Arch(32):
            return "setup-x86.exe"
        elif arch == Arch(64):
            return "setup-x86_64.exe"
        else:
            raise Exception("unknown architecture arch=%s" % (arch))

    @classmethod
    def forArch(cls, arch, packageDirs,
                force=False, mirror="http://mirrors.kernel.org/sourceware/cygwin/",
                noWait=False,
                dontDownload=False,
                ticker=True):
        """Download files or use previously downloaded files.
        
        As implemented uses wget.
        That has been a choice of convenience, could be written in Python instead.
        
        arch
            32 or 64.
        
        packageDirs
            a list of directories needed.
            
            You don't want to download all of Cygwin, only what is needed.
        
        force
            whether to force downloading even if apparently downloaded already.
            
            May be useful for programmatically updating at times.
        
        mirror
            URL of mirror to download from.
        
        noWait
            whether to forgo short waits between files.
            
            Be warned that frequent high use of bandwidth may be penalized by a server
            by refusal to serve anything at all to a specific client address or range of
            addresses.
        
        dontDownload
            whether you don't want to start a download, for some reason.
        
        Return directory path."""
        arch = Arch(arch)
        installerName = cls.installerName(arch)
        if arch == Arch(32):
            archPath = "x86"
        elif arch == Arch(64):
            archPath = "x86_64"
        else:
            raise Exception("unknown architecture arch=%s" % (arch))
        downloadDir = ScriptUser.loggedIn.userHomeRelative("Downloads")
        archDir = cls.basename(arch)
        downloadDir = os.path.join(downloadDir, archDir)
        semaphorePath = downloadDir + cls.semaphoreExtenstion
        #
        if os.path.exists(downloadDir) and not force:
            if not os.path.exists(semaphorePath):
                # directory exists and not download in progress,
                # assume it is good
                return downloadDir
            else:
                # directory exists and download in progress,
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
                print "starting to download " + archDir
                if ticker:
                    sys.stdout.write("[.")
                    sys.stdout.flush()
                try:
                    installerUrl = "http://cygwin.com/" + installerName
                    wget = CommandCapture(
                        ["wget",
                         "--quiet",
                         "--timestamping",
                         "-P", downloadDir,
                         installerUrl],
                        forgoPty=True)
                    #
                    if ticker:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                    downloadPathRoot = posixpath.join(mirror, archPath) + "/"
                    downloadPathRootDepth = cls._directoryDepth(downloadPathRoot)
                    rejectList = "index.html*,*-src.tar.bz2,*-devel,*-devel-*,*-debuginfo,*-debuginfo-*"
                    wgetArgs = [
                        "wget",
                        "--quiet",
                        "--timestamping",
                        "--recursive",
                        "--no-host-directories",
                        "--cut-dirs", str(downloadPathRootDepth),
                        "--ignore-case",
                        "--reject", rejectList,
                        "-P", downloadDir,
                        "--no-parent",
                        "--level=1",
                        "-e", "robots=off",
                    ]
                    if not noWait:
                        wgetArgs.extend(["--wait=1", "--random-wait"])
                    wgetArgs.extend([downloadPathRoot])
                    wget = CommandCapture(wgetArgs, forgoPty=True)
                    #
                    downloadPackagesPath = posixpath.join(downloadPathRoot, "release") + "/"
                    #wildcardRegex = re.compile(r"^(.*)/([^/]*\*)$")
                    for packageDir in packageDirs:
                        if ticker:
                            sys.stdout.write(".")
                            sys.stdout.flush()
                        if not isinstance(packageDir, (tuple, list)): # e.g. "bash"
                            level = 1
                        else: # e.g. ("openssl", 2)
                            level = packageDir[1]
                            packageDir = packageDir[0]
                        downloadPath = posixpath.join(downloadPackagesPath, packageDir) + "/"
                        wgetArgs = [
                            "wget",
                            "--quiet",
                            "--timestamping",
                            "--recursive",
                            "--no-host-directories",
                            "--cut-dirs", str(downloadPathRootDepth),
                            "--ignore-case",
                            "--reject", rejectList,
                            "-P", downloadDir,
                            "--no-parent",
                            "--level", str(level),
                            "-e", "robots=off",
                        ]
                        if not noWait:
                            wgetArgs.extend(["--wait=1", "--random-wait"])
                        wgetArgs.extend([downloadPath])
                        wget = CommandCapture(wgetArgs, forgoPty=True)
                    if ticker:
                        sys.stdout.write("]")
                        sys.stdout.flush()
                finally:
                    if ticker:
                        sys.stdout.write("\n")
                        sys.stdout.flush()
            except: # apparently a problem
                print "problem downloading " + archDir
                raise
            else:
                print "done downloading " + archDir
            finally:
                try:
                    # delete semaphore file
                    os.remove(semaphorePath)
                except:
                    pass
        if os.path.exists(downloadDir):
            # directory exists now, assume it is good
            return downloadDir
        else:
            # apparently download has failed
            raise IOError("directory not found " + downloadDir)

    # a list of directories which at the time of this writing has been known to work well
    # for installing Cygwin with base packages and with packages openssh and shutdown
    usablePackageList001 = "openssh,shutdown,tar,unzip,wget,curl"
    usablePackageDirs001 = [
        "_autorebase",
        "_update-info-dir",
        "alternatives",
        "attr/libattr1",
        "base-cygwin",
        "base-files",
        "bash",
        ("bzip2", 2),
        "coreutils",
        "crypt",
        "csih",
        "curl",
        "cygrunsrv",
        "cygutils",
        "cygwin",
        "cyrus-sasl",
        "db",
        "dash",
        "diffutils",
        "dos2unix",
        "e2fsprogs/libcom_err2",
        "editrights",
        "file",
        "findutils",
        "gawk",
        "gcc/libgcc1",
        "gcc/libssp0",
        "gcc/libstdc++6",
        "gettext/libintl8",
        "gmp/libgmp3",
        "gmp/libgmp10",
        "grep",
        "groff",
        "gzip",
        ("heimdal", 2),
        "ipc-utils",
        "less",
        "libedit/libedit0",
        "libiconv/libiconv2",
        "login",
        "man",
        "mintty",
        "mpfr/libmpfr4",
        "ncurses",
        "ncursesw/libncursesw10",
        "openldap",
        "openssh",
        ("openssl", 2),
        "pcre/libpcre0",
        "pcre/libpcre1",
        "popt/libpopt0",
        ("readline", 2),
        "rebase",
        "run",
        "sed",
        "shutdown",
        ("sqlite3", 2),
        "tar",
        "tcp_wrappers/libwrap0",
        "terminfo",
        "texinfo",
        "tzcode",
        "unzip",
        "util-linux",
        "vim/vim-minimal",
        "wget",
        "which",
        ("xz", 2),
        "zlib/zlib0",
    ]

if __name__ == "__main__":
    print len(CygwinDownload.usablePackageDirs001)
    #
    _exampleDownload = CygwinDownload.forArch(32, packageDirs=CygwinDownload.usablePackageDirs001)
    print _exampleDownload
    _exampleDownload2 = CygwinDownload.forArch(32, packageDirs=CygwinDownload.usablePackageDirs001, dontDownload=True)
    print _exampleDownload2
