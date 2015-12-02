#!/usr/bin/python

"""To use in developing and testing of cloning and modifying an .iso disk image.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2015.
Simplified BSD License"""

from optparse import OptionParser, OptionError
import os.path

from nrvr.diskimage.isoimage import IsoImage
from nrvr.distros.common.kickstart import DistroIsoImage
from nrvr.wins.common.autounattend import WinUdfImage

optionsParser = OptionParser(usage="%prog [options] isofile",
                             description=
"""Utility to use in developing and testing of cloning and modifying an .iso disk image.
Exercises nrvr.diskimage.isoimage.IsoImage.cloneWithModifications() without any modifications.""",
                             version="%prog 1.1")
optionsParser.add_option("-k", "--keep-clone", action="store_true", dest="keepClone",
                         help="keep clone when exiting, which uses disk space, default %default", default=False)
optionsParser.add_option("-j", "--dont-ignore-joliet", action="store_true", dest="dontIgnoreJoliet",
                         help="don't ignore Joliet-extension information, default %default", default=False)
optionsParser.add_option("-l", "--linux-distro", action="store_true", dest="linuxDistro",
                         help="clone a Linux distro, bootable with boot image and catalog, default %default", default=False)
optionsParser.add_option("-u", "--udf", action="store_true", dest="udf",
                         help="use UDF instead of ISO 9660, default %default", default=False)
optionsParser.add_option("-w", "--windows-installer", action="store_true", dest="windowsInstaller",
                         help="clone a Windows installer, bootable with boot image, default %default", default=False)
optionsParser.add_option("-p", "--pause", action="store_true", dest="pause",
                         help="pause before and after applying modifications, default %default", default=False)
(options, args) = optionsParser.parse_args()
if len(args) is not 1:
    raise OptionError("needs exactly one argument, a .iso file")

try:
    isoFile = args[0]
    isoImageClone = isoImage = None # define to avoid distracting exceptions
    if options.linuxDistro:
        isoImage = DistroIsoImage(isoFile)
        isoImageClone = isoImage.cloneWithModifications(modifications=[],
                                                        udf=options.udf,
                                                        ignoreJoliet=not options.dontIgnoreJoliet)
    elif options.windowsInstaller:
        isoImage = WinUdfImage(isoFile)
        isoImageClone = isoImage.cloneWithModifications(modifications=[isoImage.modificationForElToritoBootImage()],
                                                        pause=options.pause)
    else:
        isoImage = IsoImage(isoFile)
        isoImageClone = isoImage.cloneWithModifications(modifications=[],
                                                        udf=options.udf,
                                                        ignoreJoliet=not options.dontIgnoreJoliet)
    print "cloned into %s" % (isoImageClone.isoImagePath)
finally:
    if isoImageClone and os.path.exists(isoImageClone.isoImagePath):
        if not options.keepClone:
            print "avoiding disk clogging, now deleting cloned %s" % (isoImageClone.isoImagePath)
            isoImageClone.remove()
        else:
            print "watch your disk space, per --keep-clone now keeping cloned %s" % (isoImageClone.isoImagePath)
