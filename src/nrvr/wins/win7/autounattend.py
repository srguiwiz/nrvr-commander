#!/usr/bin/python

"""nrvr.wins.win7.autounattend - Create and manipulate Windows 7 installer autounattend.xml files

Classes provided by this module include
* Win7UdfImage
* Win7AutounattendFileContent

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

import re

import nrvr.wins.common.autounattend

class Win7UdfImage(nrvr.wins.common.autounattend.WinUdfImage):
    """A Windows 7 installer UDF DVD-ROM disk image."""

    def __init__(self, isoImagePath):
        """Create new Windows 7 installer Win7UdfImage descriptor.
        
        A descriptor can describe an .iso image that does or doesn't yet exist on the host disk."""
        nrvr.wins.common.autounattend.WinUdfImage.__init__(self, isoImagePath)


class Win7AutounattendFileContent(nrvr.wins.common.autounattend.InstallerAutounattendFileContent):
    """The text content of a Windows installer autounattend.xml file for use with a Windows 7 installer."""

    def __init__(self, string):
        """Create new autounattend file content container."""
        nrvr.wins.common.autounattend.InstallerAutounattendFileContent.__init__(self, string)
