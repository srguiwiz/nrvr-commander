#!/usr/bin/python

"""nrvr.diskimage.isoimage - Clone and modify an .iso disk image

The main class provided by this module is IsoImage.

Implemented subclasses of IsoImageModification are
* IsoImageModificationFromString
* IsoImageModificationFromPath
* IsoImageModificationByReplacement
* IsoImageModificationFromByteRange

As implemented works in Linux.
As implemented requires mount, umount, iso-info, iso-read, genisoimage commands.
Nevertheless essential.  To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import codecs
import os.path
import re
import shutil

from nrvr.process.commandcapture import CommandCapture
from nrvr.util.requirements import SystemRequirements
from nrvr.util.times import Timestamp

class IsoImage(object):
    """An .iso ISO 9660 (or UDF) CD-ROM or DVD-ROM disk image."""

    @classmethod
    def commandsUsedInImplementation(cls):
        """Return a list to be passed to SystemRequirements.commandsRequired().
        
        This class can be passed to SystemRequirements.commandsRequiredByImplementations()."""
        return ["mount", "umount",
                "iso-info", "iso-read",
                (["genisoimage"], ["mkisofs"])]

    def __init__(self, isoImagePath):
        """Create new IsoImage descriptor.
        
        A descriptor can describe an .iso image that does or doesn't yet exist on the host disk."""
        # really want abspath and expanduser
        self._isoImagePath = os.path.abspath(os.path.expanduser(isoImagePath))
        self.mountDir = None

    @property
    def isoImagePath(self):
        """Path of the .iso image."""
        return self._isoImagePath

    def exists(self):
        """Return True if .iso image exists on the host disk."""
        return os.path.exists(self._isoImagePath)

    def remove(self):
        """Remove (delete) .iso image from the host disk."""
        os.remove(self._isoImagePath)

    def mount(self, mountDir, udf=False):
        """Mount .iso image."""
        if not os.path.exists(mountDir):
            # was os.makedirs, but that could allow unintended wild creations to go undetected
            os.mkdir(mountDir, 0755)
        # mount man page says something since Linux 2.6.25 there is auto-destruction of loop devices,
        # which makes mounting and unmounting easier for us than it used to be,
        # also see https://lkml.org/lkml/2007/10/30/413,
        # also see http://marc.info/?l=util-linux-ng&m=119362955431694
        if not udf: # iso9660
            filesystemType = "iso9660"
        else: # udf
            filesystemType = "udf"
        CommandCapture(["mount", "-o", "loop", "-t", filesystemType, "-r",
                       self._isoImagePath, mountDir])
        # record only in case of success
        self.mountDir = mountDir

    def unmount(self):
        """Unmount .iso image."""
        if self.mountDir:
            CommandCapture(["umount", "-d", self.mountDir],
                           exceptionIfNotZero=False, exceptionIfAnyStderr=False)

    def copyToDirectory(self, copyDirectory, udf=False, ignoreJoliet=True, tolerance=0.0):
        """Copy all files into a directory.
        
        Not using mount command, no need to run as root."""
        # as of 2013-09-29 given known uses of this package and known bugs of iso-info
        # it appears better to default to ignoreJoliet=True
        # see https://savannah.gnu.org/bugs/?40130
        # see https://savannah.gnu.org/bugs/?40138
        #
        # really want abspath and expanduser
        copyDirectory = os.path.abspath(os.path.expanduser(copyDirectory))
        # make sure not merging with pre-existing directory or files
        if os.path.exists(copyDirectory):
            shutil.rmtree(copyDirectory)
        # make directory
        os.mkdir(copyDirectory, 0755)
        if not udf: # iso9660
            # get directories info in a reasonably parsable list
            isoInfoLArgs = ["iso-info", "-i", self._isoImagePath, "-l"]
            if ignoreJoliet:
                isoInfoLArgs.insert(1, "--no-joliet")
            isoInfoL = CommandCapture(isoInfoLArgs, copyToStdio=False)
            # directories without leading slash and without trailing slash
            directories = re.findall(r"(?m)^[ \t]*/(.+?)/?[ \t]*:[ \t]*$", isoInfoL.stdout)
            # get files info in a reasonably parsable list
            isoInfoFArgs = ["iso-info", "-i", self._isoImagePath, "-f"]
            if ignoreJoliet:
                isoInfoFArgs.insert(1, "--no-joliet")
            isoInfoF = CommandCapture(isoInfoFArgs, copyToStdio=False)
            # files without leading slash and without trailing slash
            files = re.findall(r"(?m)^[ \t]*[0-9]*[ \t]+/(.+?)/?[ \t]*$", isoInfoF.stdout)
        else: # udf
            # get directories and files info in a reasonably parsable list
            isoInfoUArgs = ["iso-info", "-i", self._isoImagePath, "-U"]
            if ignoreJoliet:
                isoInfoUArgs.insert(1, "--no-joliet")
            isoInfoU = CommandCapture(isoInfoUArgs, copyToStdio=False)
            # list below excluded line 123456 /.
            isoInfoUList = re.search(r"(?s)[ \t]*[0-9]+[ \t]+/\.\s*\n(.*)", isoInfoU.stdout).group(1)
            # directories without leading slash and without trailing slash
            directories = re.findall(r"(?m)^[ \t]*[0-9]+[ \t]+/(.+?)/\.[ \t]*$", isoInfoUList)
            # files without leading slash and without trailing slash dot
            files = re.findall(r"(?m)^[ \t]*[0-9]+[ \t]+/(.*?)(?:/\.)?[ \t]*$", isoInfoUList)
        # sorting matters to allow building a tree of directories
        directories = sorted(directories)
        # make directories
        for relativePathOnIso in directories:
            pathOnHost = os.path.join(copyDirectory, relativePathOnIso)
            os.mkdir(pathOnHost, 0755)
        # tolerate some defects in iso-read
        readAttemptCount = 0
        readSuccessCount = 0
        # copy files
        for relativePathOnIso in files:
            if relativePathOnIso in directories:
                # directories exist already, nothing to do
                continue
            pathOnHost = os.path.join(copyDirectory, relativePathOnIso)
            # copy file
            try:
                readAttemptCount += 1
                isoReadArgs = ["iso-read",
                               "-i", self._isoImagePath,
                               "-e", relativePathOnIso,
                               "-o", pathOnHost];
                if udf: # udf
                    isoReadArgs.append("-U")
                CommandCapture(isoReadArgs, copyToStdio=False)
                readSuccessCount += 1
            except Exception as ex:
                print ex
        # check tolerance
        readFailureCount = readAttemptCount - readSuccessCount
        if readFailureCount > readAttemptCount * tolerance:
            raise Exception("too many ({0} of {1}) failures reading {2}".format(readFailureCount, readAttemptCount, self._isoImagePath))
        elif readFailureCount:
            print "continuing despite some ({0} of {1}) failures reading {2}".format(readFailureCount, readAttemptCount, self._isoImagePath)
        return copyDirectory

    def cloneWithModifications(self, modifications=[], cloneIsoImagePath=None, udf=False, ignoreJoliet=True,
                               pause=False):
        """Clone with any number of instances of IsoImageModification applied.
        
        A temporary assembly directory in the same directory as cloneIsoImagePath needs disk space,
        but it is removed automatically upon completion of cloning.
        
        modifications
            a list of IsoImageModification instances.
        
        cloneIsoImagePath
            if not given then in same directory with a timestamp in the filename.
        
        return
            IsoImage(cloneIsoImagePath)."""
        # as of 2013-09-29 given known uses of this package and known bugs of iso-info
        # it appears better to default to ignoreJoliet=True
        # see https://savannah.gnu.org/bugs/?40130
        # see https://savannah.gnu.org/bugs/?40138
        #
        # timestamp to the microsecond should be good enough
        timestamp = Timestamp.microsecondTimestamp()
        # ensure there is a cloneIsoImagePath
        if not cloneIsoImagePath:
            # insert timestamp before extension
            isoImagePathSplitext = os.path.splitext(self._isoImagePath)
            cloneIsoImagePath = isoImagePathSplitext[0] + "." + timestamp + isoImagePathSplitext[1]
        if os.path.exists(cloneIsoImagePath):
            raise Exception("won't overwrite already existing {0}".format(cloneIsoImagePath))
        temporaryAssemblyDirectory = cloneIsoImagePath + ".tmpdir"
        #os.mkdir(temporaryAssemblyDirectory, 0755)
        try:
            # copy files from original .iso image
            print "copying files from {0}, this may take a few minutes".format(self._isoImagePath)
            self.copyToDirectory(temporaryAssemblyDirectory, udf=udf, ignoreJoliet=ignoreJoliet)
            # give a chance to look
            if pause:
                raw_input("you requested to pause before applying modifications, press Enter to continue:")
            # apply modifications
            print "applying modifications into {0}".format(temporaryAssemblyDirectory)
            for modification in modifications:
                modification.writeIntoAssembly(temporaryAssemblyDirectory)
            # give a chance to look
            if pause:
                raw_input("you requested to pause after applying modifications, press Enter to continue:")
            # make new .iso image file
            print "making new {0}, this may take a few minutes".format(cloneIsoImagePath)
            if SystemRequirements.which("genisoimage"):
                # preferred choice
                makeIsoImageCommandName = "genisoimage"
            elif SystemRequirements.which("mkisofs"):
                # acceptable choice
                makeIsoImageCommandName = "mkisofs"
            else:
                # preferred choice for error message
                makeIsoImageCommandName = "genisoimage"
            genisoimageOptions = self.genisoimageOptions(label=timestamp, udf=udf, ignoreJoliet=ignoreJoliet)
            CommandCapture([makeIsoImageCommandName] +
                           genisoimageOptions + 
                           ["-o", cloneIsoImagePath,
                            temporaryAssemblyDirectory],
                           copyToStdio=False,
                           exceptionIfAnyStderr=False)
        finally:
            # remove in a specific, hopefully most resilient order
            shutil.rmtree(temporaryAssemblyDirectory, ignore_errors=True)
        return IsoImage(cloneIsoImagePath)

    def cloneWithModificationsUsingMount(self, modifications=[], cloneIsoImagePath=None, udf=False, ignoreJoliet=True,
                                         pause=False):
        """Clone with any number of instances of IsoImageModification applied.
        
        This is an older implementation which regrettably because of the mount command requires
        having superuser privileges.
        It is still here in case a newer implementation doesn't work right, which could be for any
        of a number of reasons, for example for symbolic links.
        
        A temporary assembly directory in the same directory as cloneIsoImagePath needs disk space,
        but it is removed automatically upon completion of cloning.
        
        modifications
            a list of IsoImageModification instances.
        
        cloneIsoImagePath
            if not given then in same directory with a timestamp in the filename.
        
        return
            IsoImage(cloneIsoImagePath)."""
        # timestamp to the microsecond should be good enough
        timestamp = Timestamp.microsecondTimestamp()
        # ensure there is a cloneIsoImagePath
        if not cloneIsoImagePath:
            # insert timestamp before extension
            isoImagePathSplitext = os.path.splitext(self._isoImagePath)
            cloneIsoImagePath = isoImagePathSplitext[0] + "." + timestamp + isoImagePathSplitext[1]
        if os.path.exists(cloneIsoImagePath):
            raise Exception("won't overwrite already existing {0}".format(cloneIsoImagePath))
        temporaryMountDirectory = cloneIsoImagePath + ".mnt"
        temporaryAssemblyDirectory = cloneIsoImagePath + ".tmpdir"
        os.mkdir(temporaryMountDirectory, 0755)
        #os.mkdir(temporaryAssemblyDirectory, 0755)
        try:
            # mount
            self.mount(temporaryMountDirectory, udf=udf)
            # copy files from original .iso image
            print "copying files from {0}, this may take a few minutes".format(self._isoImagePath)
            shutil.copytree(temporaryMountDirectory, temporaryAssemblyDirectory, symlinks=True)
            # give a chance to look
            if pause:
                raw_input("you requested to pause before applying modifications, press Enter to continue:")
            # apply modifications
            print "applying modifications into {0}".format(temporaryAssemblyDirectory)
            for modification in modifications:
                modification.writeIntoAssembly(temporaryAssemblyDirectory)
            # give a chance to look
            if pause:
                raw_input("you requested to pause after applying modifications, press Enter to continue:")
            # make new .iso image file
            print "making new {0}, this may take a few minutes".format(cloneIsoImagePath)
            genisoimageOptions = self.genisoimageOptions(label=timestamp, udf=udf, ignoreJoliet=ignoreJoliet)
            CommandCapture(["genisoimage"] + 
                           genisoimageOptions + 
                           ["-o", cloneIsoImagePath,
                            temporaryAssemblyDirectory],
                           copyToStdio=False,
                           exceptionIfAnyStderr=False)
        finally:
            # remove in a specific, hopefully most resilient order
            self.unmount()
            shutil.rmtree(temporaryAssemblyDirectory, ignore_errors=True)
            os.rmdir(temporaryMountDirectory)
        return IsoImage(cloneIsoImagePath)

    def genisoimageOptions(self, label=None, udf=False, ignoreJoliet=True):
        """Auxiliary method, called by cloneWithModifications.
        
        Can be overridden by subclass methods genisoimageOptions,
        which may want to extend the returned list.
        
        Could be improved in the future.
        Could recognize content of .iso image.
        Could select different options depending on content of .iso image.
        Maybe could use iso-info -d 9 -i self.isoImagePath.
        Could be overridden for a subclass."""
        # this implementation has been made to be a workable basis for most uses
        if not label:
            label = Timestamp.microsecondTimestamp()
        genisoimageOptions = []
        if udf: # udf
            genisoimageOptions.append("-udf")
        if not ignoreJoliet:
            # broader compatibility of filenames and metadata
            genisoimageOptions.append("-J")
        genisoimageOptions.extend([
            # broader compatibility of filenames and metadata
            "-r", "-T",
            "-f",
            #
            # possibly needed labeling,
            # volume id, volume name or label, max 32 characters
            "-V", label[-32:]
        ])
        return genisoimageOptions

class IsoImageModification(object):
    """A modification to an .iso image."""
    def __init__(self, pathOnIso):
        self.pathOnIso = pathOnIso
    def pathInTemporaryAssemblyDirectory(self, temporaryAssemblyDirectory):
        """Auxiliary method, called by subclass method writeIntoAssembly."""
        # remove any leading slash in order to make it relative
        relativePathOnIso = re.sub(r"^/*(.*?)$", r"\g<1>", self.pathOnIso)
        return os.path.abspath(os.path.join(temporaryAssemblyDirectory, relativePathOnIso))
    def writeIntoAssembly(self, temporaryAssemblyDirectory):
        """To be implemented in subclasses."""
        raise NotImplementedError("Method writeIntoAssembly to be implemented in subclasses of IsoImageModification.")
class IsoImageModificationFromString(IsoImageModification):
    """A modification to an .iso image, copy from string into file."""
    def __init__(self, pathOnIso, string, encoding="utf-8"):
        super(IsoImageModificationFromString, self).__init__(pathOnIso)
        self.string = string
        self.encoding = encoding
    def writeIntoAssembly(self, temporaryAssemblyDirectory):
        pathInTemporaryAssemblyDirectory = self.pathInTemporaryAssemblyDirectory(temporaryAssemblyDirectory)
        # remove pre-existing file, if any
        if os.path.exists(pathInTemporaryAssemblyDirectory):
            os.remove(pathInTemporaryAssemblyDirectory)
        # write
        with codecs.open(pathInTemporaryAssemblyDirectory, "w", encoding=self.encoding) as temporaryFile:
            temporaryFile.write(self.string)
class IsoImageModificationFromPath(IsoImageModification):
    """A modification to an .iso image, copy from path into file or into directory."""
    def __init__(self, pathOnIso, pathOnHost):
        super(IsoImageModificationFromPath, self).__init__(pathOnIso)
        self.pathOnHost = pathOnHost
    def writeIntoAssembly(self, temporaryAssemblyDirectory):
        pathInTemporaryAssemblyDirectory = self.pathInTemporaryAssemblyDirectory(temporaryAssemblyDirectory)
        if not os.path.isdir(self.pathOnHost):
            # if not a directory then
            # remove pre-existing file, if any
            if os.path.exists(pathInTemporaryAssemblyDirectory):
                os.remove(pathInTemporaryAssemblyDirectory)
            # copy
            shutil.copy2(self.pathOnHost, pathInTemporaryAssemblyDirectory)
        else:
            # if a directory then
            # remove pre-existing directory, if any
            if os.path.exists(pathInTemporaryAssemblyDirectory):
                shutil.rmtree(pathInTemporaryAssemblyDirectory)
            # copy
            shutil.copytree(self.pathOnHost, pathInTemporaryAssemblyDirectory, symlinks=True)
class IsoImageModificationByReplacement(IsoImageModification):
    # raw string in addition to triple-quoted string because of backslashes \
    r"""A modification to an .iso image, replace within file.
    
    Treats whole file as one string to match.
    To match a newline a regular expression may use "(\r?\n)",
    which nicely allows in the replacement to place appropriate newlines
    by backreference, e.g. by "\g<1>"."""
    def __init__(self, pathOnIso, regularExpression, replacement, encoding="utf-8"):
        super(IsoImageModificationByReplacement, self).__init__(pathOnIso)
        self.regularExpression = regularExpression
        self.replacement = replacement
        self.encoding = encoding
    def writeIntoAssembly(self, temporaryAssemblyDirectory):
        pathInTemporaryAssemblyDirectory = self.pathInTemporaryAssemblyDirectory(temporaryAssemblyDirectory)
        # read pre-existing file
        with codecs.open(pathInTemporaryAssemblyDirectory, "r", encoding=self.encoding) as inputFile:
            fileContent = inputFile.read()
        fileContent = self.regularExpression.sub(self.replacement, fileContent)
        # overwrite
        with codecs.open(pathInTemporaryAssemblyDirectory, "w", encoding=self.encoding) as outputFile:
            outputFile.write(fileContent)
class IsoImageModificationFromByteRange(IsoImageModification):
    """A modification to an .iso image, copy from byte range from file into a file by itself."""
    def __init__(self, pathOnIso, pathOnHost, start, stop):
        super(IsoImageModificationFromByteRange, self).__init__(pathOnIso)
        self.pathOnHost = pathOnHost
        self.start = start
        self.stop = stop
    def writeIntoAssembly(self, temporaryAssemblyDirectory):
        pathInTemporaryAssemblyDirectory = self.pathInTemporaryAssemblyDirectory(temporaryAssemblyDirectory)
        if self.start:
            start = self.start
        else:
            start = 0
        if self.stop:
            stop = self.stop
        else:
            stop = os.path.getsize(self.pathOnHost)
        # remove pre-existing file, if any
        if os.path.exists(pathInTemporaryAssemblyDirectory):
            os.remove(pathInTemporaryAssemblyDirectory)
        # copy
        with open(self.pathOnHost, "rb") as inputFile:
            inputFile.seek(start)
            with open(pathInTemporaryAssemblyDirectory, "wb") as outputFile:
                current = start
                while current < stop:
                    remainder = stop - current
                    chunk = min(remainder, 10240)
                    bytes = inputFile.read(chunk)
                    outputFile.write(bytes)
                    current += chunk

if __name__ == "__main__":
    from nrvr.util.requirements import SystemRequirements
    SystemRequirements.commandsRequiredByImplementations([IsoImage], verbose=True)
    #
    import tempfile
    _testDir = os.path.join(tempfile.gettempdir(), Timestamp.microsecondTimestamp())
    os.mkdir(_testDir, 0755)
    try:
        _originalDir = os.path.join(_testDir, "cd")
        os.mkdir(_originalDir, 0755)
        with open(os.path.join(_originalDir, "cheese.txt"), "w") as outputFile:
            outputFile.write("please")
        os.mkdir(os.path.join(_originalDir, "empty"))
        os.mkdir(os.path.join(_originalDir, "something"))
        with open(os.path.join(_originalDir, u"something/\xf6sterreichischer K\xe4se.txt"), "w") as outputFile:
            outputFile.write("stinkt, aber gesund")
        os.mkdir(os.path.join(_originalDir, "tree"))
        with open(os.path.join(_originalDir, "tree/leaf.txt"), "w") as outputFile:
            outputFile.write("green")
        os.mkdir(os.path.join(_originalDir, "tree/branch"))
        with open(os.path.join(_originalDir, "tree/branch/fruit.txt"), "w") as outputFile:
            outputFile.write("yummy")
        os.mkdir(os.path.join(_originalDir, "tree/branch/another one"))
        _isoImageFile = os.path.join(_testDir, "cd.iso")
        CommandCapture(["genisoimage",
                        "-r", "-J", "-T",
                        "-o", _isoImageFile,
                        _originalDir],
                       copyToStdio=False,
                       exceptionIfAnyStderr=False)
        _isoImage = IsoImage(_isoImageFile)
        _copyDir = os.path.join(_testDir, "cd2")
        _isoImage.copyToDirectory(_copyDir)
    finally:
        shutil.rmtree(_testDir)
