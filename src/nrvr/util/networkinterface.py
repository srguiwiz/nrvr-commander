#!/usr/bin/python

"""nrvr.util.networkinterface - Utilities regarding network interfaces

Class provided by this module is NetworkInterface.

Works in Linux and Mac OS X.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import re

from nrvr.process.commandcapture import CommandCapture

class NetworkInterface(object):
    """Utilities regarding network interfaces.
    
    As implemented only supports IPv4."""

    # Linux inet addr:127.0.0.1
    # Mac OS X inet 127.0.0.1
    _networkInterfaceAddressRegex = re.compile(r"(?i)\s*(?:inet\s*addr\s*:\s*|inet\s+)([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})")

    @classmethod
    def commandsUsedInImplementation(cls):
        """Return a list to be passed to SystemRequirements.commandsRequired().
        
        This class can be passed to SystemRequirements.commandsRequiredByImplementations()."""
        return ["ifconfig"]

    @classmethod
    def ipAddressOf(cls, name):
        """For name="lo0" return "127.0.0.1".
        
        name
            the name of the interface.
        
        Return the IP address of the interface, or None."""
        # as implemented does NOT require vmrun command, absence means not any
        ifconfig = CommandCapture(["ifconfig", name],
                                  copyToStdio=False,
                                  exceptionIfNotZero=False, exceptionIfAnyStderr=False)
        if ifconfig.returncode != 0 or ifconfig.stderr:
            return None
        interfaceAddressMatch = cls._networkInterfaceAddressRegex.search(ifconfig.stdout)
        if not interfaceAddressMatch:
            return None
        interfaceAddress = interfaceAddressMatch.group(1)
        return interfaceAddress

if __name__ == "__main__":
    from nrvr.util.requirements import SystemRequirements
    SystemRequirements.commandsRequiredByImplementations([NetworkInterface], verbose=True)
    #
    print NetworkInterface.ipAddressOf("lo0")
    print NetworkInterface.ipAddressOf("madesomethingup")
