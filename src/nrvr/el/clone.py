#!/usr/bin/python

"""nrvr.el.clone - Manipulate Enterprise Linux machines for cloning

Classes provided by this module include
* Clone

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import re

from nrvr.util.ipaddress import IPAddress

class Clone():
    """Utilities for manipulating a Enterprise Linux machines for cloning."""

    @classmethod
    def commandToChangeStaticIPAddress(cls, oldIpAddress, newIpAddress, interface="eth0"):
        """Build command to change static IP address.
        
        Must be root to succeed.
        
        As implemented works in Enterprise Linux versions 6.x.
        
        Return command to change static IP address."""
        oldIpAddress = IPAddress.asString(oldIpAddress)
        newIpAddress = IPAddress.asString(newIpAddress)
        # oddly has been observed to require two times service network restart
        command = r"sed -i -e 's/" + re.escape(oldIpAddress) + r"/" + re.escape(newIpAddress) + \
                  r"/' '/etc/sysconfig/network-scripts/ifcfg-" + re.escape(interface) + \
                  r"' ; ( service network restart ; service network restart ) &"
        return command

if __name__ == "__main__":
    print Clone.commandToChangeStaticIPAddress("10.123.45.67", "10.123.45.68")
