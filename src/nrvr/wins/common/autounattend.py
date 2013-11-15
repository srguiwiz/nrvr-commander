#!/usr/bin/python

"""nrvr.wins.common.autounattend - Create and manipulate Windows installer autounattend.xml files

Classes provided by this module include
* WinUdfImage
* InstallerAutounattendFileContent

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
        clone = super(WinUdfImage, self).cloneWithModifications(modifications=modifications,
                                                                cloneIsoImagePath=cloneIsoImagePath,
                                                                udf=udf,
                                                                ignoreJoliet=ignoreJoliet,
                                                                pause=pause)
        return WinUdfImage(clone.isoImagePath)

    def modificationsIncludingAutounattendFile(self, _autounattendFileContent):
        """Construct and return a list of modifications to be passed to method cloneWithModifications.
        
        This method is called by method cloneWithAutounattend, which takes the returned list
        and passes it to method cloneWithModifications.
        
        Subclasses may provide further implementations of this method.
        Possibly different per Windows version specific subclass.
        This class implementation does return an essential list.
        
        _autounattendFileContent
            An InstallerAutounattendFileContent object.
            
            If None then proceed nevertheless.
        
        Return a list of modifications which will be passed to method cloneWithModifications."""
        # modifications
        modifications = \
        [
            # a boot image is a necessity
            self.modificationForElToritoBootImage()
        ]
        if _autounattendFileContent:
            modifications.extend([
                # the autounattend.xml file
                nrvr.diskimage.isoimage.IsoImageModificationFromString
                ("autounattend.xml",
                 _autounattendFileContent.string)
                ])
        return modifications

    def cloneWithAutounattend(self, _autounattendFileContent, cloneIsoImagePath=None):
        """Clone with autounattend.xml file added and modified to automatically boot with it.
        
        For more on behavior see documentation of class IsoImage method cloneWithModifications.
        
        For details of modifications see method modificationsIncludingAutounattendFile,
        which might be different per Windows version specific subclass.
        
        _autounattendFileContent
            An InstallerAutounattendFileContent object.
            
            If None then proceed nevertheless."""
        # modifications, possibly different per Windows version specific subclass
        modifications = self.modificationsIncludingAutounattendFile(_autounattendFileContent)
        # clone with modifications
        clone = self.cloneWithModifications(modifications=modifications,
                                            cloneIsoImagePath=cloneIsoImagePath)
        return clone

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

    def modificationMakeEiCfg(self, editionId, oem=False, volumeLicense=False):
        """Construct and return an instance of IsoImageModification, to be processed
        by method cloneWithModifications.
        
        As implemented writes a new sources/ei.cfg file from scratch.
        
        editionId
            a string.
            For Windows 7 one of "Starter", "HomeBasic", "HomePremium", "Professional", "Ultimate", "Enterprise".
            For Windows 8 one of "Core", "Professional", "Enterprise"."""
        eiCfgContent = "".join(
            "[EditionID]\n"
            + editionId + "\n"
            "[Channel]\n"
            + ("Retail" if not oem else "OEM") + "\n"
            "[VL]\n"
            + ("0" if not volumeLicense else "1") + "\n"
            )
        modification = \
            nrvr.diskimage.isoimage.IsoImageModificationFromString(
                "sources/ei.cfg",
                eiCfgContent)
        return modification


class InstallerAutounattendFileContent(object):
    """The text content of a Windows installer autounattend.xml file for use with a Windows installer."""

    def __init__(self, string):
        """Create new autounattend file content container.
        
        This constructor does unicode(string)."""
        self._string = unicode(string)

    @property
    def string(self):
        """The whole content."""
        return self._string
