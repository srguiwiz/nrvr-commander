#!/usr/bin/python

"""nrvr.wins.common.udfimage - Clone and modify a UDF disk image

Classes provided by this module include
* WinUdfImage

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import re

import nrvr.diskimage.isoimage
from nrvr.process.commandcapture import CommandCapture

class WinUdfImage(nrvr.diskimage.isoimage.IsoImage):
    """A Windows installer UDF DVD-ROM disk image."""

    @classmethod
    def commandsUsedInImplementation(cls):
        """Return a list to be passed to SystemRequirements.commandsRequired().
        
        This class can be passed to SystemRequirements.commandsRequiredByImplementations()."""
        return nrvr.diskimage.isoimage.IsoImage.commandsUsedInImplementation() + ["isoinfo"]

    def __init__(self, isoImagePath):
        """Create new Windows installer WinUdfImage descriptor.
        
        A descriptor can describe an .iso image that does or doesn't yet exist on the host disk."""
        nrvr.diskimage.isoimage.IsoImage.__init__(self, isoImagePath)

    def genisoimageOptions(self,
                           bootImage="boot.bin",
                           label=None,
                           udf=True, ignoreJoliet=False):
        """Auxiliary method, called by cloneWithModifications.
        
        Can be overridden by subclass methods genisoimageOptions,
        which may want to extend the returned list.
        
        Could be improved in the future.
        Could recognize content of .iso image.
        Could select different options depending on content of .iso image.
        Maybe could use iso-info -d 9 -i self.isoImagePath.
        Could be overridden for a subclass."""
        # this implementation has been made to work for Windows
        if not label:
            label = Timestamp.microsecondTimestamp()
        genisoimageOptions = []
        if udf: # udf
            genisoimageOptions.append("-udf")
        if not ignoreJoliet:
            # broader compatibility of filenames and metadata
            genisoimageOptions.extend([
                # broader compatibility of filenames and metadata
                "-J",
                "-joliet-long"
            ])
        genisoimageOptions.extend([
            # directories and filenames
            "-relaxed-filenames",
            #
            # boot related
            "-no-emul-boot",
            "-b", bootImage,
            #
            # possibly needed labeling,
            # volume id, volume name or label, max 32 characters
            "-V", label[-32:]
        ])
        return genisoimageOptions

    def modificationForElToritoBootImage(self):
        """Construct and return an instance of IsoImageModification, to be processed
        by method cloneWithModifications.
        
        As implemented copies El Torito boot image from sectors into a file."""
        # as implemented assumes this is the kind of disk with this kind of info
        isoinfo = CommandCapture([
            "isoinfo",
            "-d",
            "-j", "UTF-8", # avoid stderr "Setting input-charset to 'UTF-8' from locale."
            "-i", self._isoImagePath],
            copyToStdio=False)
        info = isoinfo.stdout
        numberOfSectors = re.search(r"(?mi)^[ \t]*Nsect[ \t]+([0-9]+).*$", info).group(1)
        numberOfSectors = int(numberOfSectors, base=16)
        firstSector = re.search(r"(?mi)^[ \t]*Bootoff[ \t]+([0-9a-f]+).*$", info).group(1)
        firstSector = int(firstSector, base=16)
        start = firstSector * 2048
        stop = start + numberOfSectors * 2048
        modification = \
            nrvr.diskimage.isoimage.IsoImageModificationFromByteRange(
                "boot.bin",
                self.isoImagePath,
                start, stop)
        return modification

    def cloneWithModifications(self, modifications=[], cloneIsoImagePath=None, udf=True, ignoreJoliet=False,
                               pause=False):
        """Clone with any number of instances of IsoImageModification applied.
        
        A temporary assembly directory in the same directory as cloneIsoImagePath needs disk space,
        but it is removed automatically upon completion of cloning.
        
        modifications
            a list of IsoImageModification instances.
        
        cloneIsoImagePath
            if not given then in same directory with a timestamp in the filename.
        
        return
            WinUdfImage(cloneIsoImagePath)."""
        modifications.insert(0, self.modificationForElToritoBootImage())
        clone = super(WinUdfImage, self).cloneWithModifications(modifications=modifications,
                                                                cloneIsoImagePath=cloneIsoImagePath,
                                                                udf=udf,
                                                                ignoreJoliet=ignoreJoliet,
                                                                pause=pause)
        return WinUdfImage(clone.isoImagePath)
