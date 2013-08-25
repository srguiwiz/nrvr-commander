#!/usr/bin/python

"""nrvr.distros.el.kickstart - Create and manipulate Enterprise Linux kickstart files

Classes provided by this module include
* ElIsoImage

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import re

import nrvr.distros.common.kickstart

class ElIsoImage(nrvr.distros.common.kickstart.DistroIsoImage):
    """An Enterprise Linux .iso ISO CD-ROM or DVD-ROM disk image."""

    def __init__(self, isoImagePath):
        """Create new Enterprise Linux IsoImage descriptor.
        
        A descriptor can describe an .iso image that does or doesn't yet exist on the host disk."""
        nrvr.distros.common.kickstart.DistroIsoImage.__init__(self, isoImagePath)

    def modificationsIncludingKickstartFile(self, _kickstartFileContent):
        """Construct and return a list of modifications to be passed to method cloneWithModifications.
        
        This method is called by method cloneWithAutoBootingKickstart, which takes the returned list
        and passes it to method cloneWithModifications.
        
        As implemented known to support Scientific Linux 6.1 and 6.4.
        As implemented tested for i386 and x86_64.
        Good chance it will work with other brand Enterprise Linux distributions.
        Good chance it will work with newer versions distributions.
        
        _kickstartFileContent
            A KickstartFileContent object.
        
        Return a list of modifications which will be passed to method cloneWithModifications."""
        # a distinct path
        kickstartCustomConfigurationPathOnIso = "isolinux/ks-custom.cfg"
        # modifications
        modifications = \
        [nrvr.diskimage.isoimage.IsoImageModificationFromString
         (kickstartCustomConfigurationPathOnIso,
          _kickstartFileContent.string),
         # in isolinux.cfg
         # delete any pre-existing "menu default"
         nrvr.diskimage.isoimage.IsoImageModificationByReplacement
         ("isolinux/isolinux.cfg",
          re.compile(r"(\r?\n)([ \t]+menu[ \t]+default)(\s)"),
          r"\3"),
         # in isolinux.cfg
         # insert section with label "ks-custom", first, before "label linux",
         # documentation says "ks=cdrom:/directory/filename.cfg" with a single "/" slash, NOT double,
         # e.g. see http://fedoraproject.org/wiki/Anaconda/Kickstart,
         # must set "ksdevice=eth0" or "ksdevice=link" or else asks which network interface to use,
         # e.g. see http://wiki.centos.org/TipsAndTricks/KickStart,
         # hope you don't need to read http://fedoraproject.org/wiki/Anaconda/NetworkIssues
         nrvr.diskimage.isoimage.IsoImageModificationByReplacement
         ("isolinux/isolinux.cfg",
          re.compile(r"(\r?\n)(label[ \t]+linux)(\s)"),
          r"\1label ks-custom\1"
          r"  menu label Custom ^Kickstart\1"
          r"  menu default\1"
          r"  kernel vmlinuz\1"
          r"  append initrd=initrd.img ks=cdrom:/" + kickstartCustomConfigurationPathOnIso + r" ksdevice=eth0 \1\2\3"),
         # in isolinux.cfg
         # change to "timeout 50" measured in 1/10th seconds
         nrvr.diskimage.isoimage.IsoImageModificationByReplacement
         ("isolinux/isolinux.cfg",
          re.compile(r"(\r?\n)(timeout[ \t]+\d+)(\s)"),
          r"\1timeout 50\3")]
        return modifications
