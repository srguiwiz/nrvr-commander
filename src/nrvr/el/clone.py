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
    def commandToChangeStaticIPAddress(cls, oldIpAddress, newIpAddress, interface=None):
        """Build command to change static IP address.
        
        Must be root to succeed.
        
        As implemented works in Enterprise Linux versions 6.x.
        
        interface
            a string, e.g. "eth0".
        
        Return command to change static IP address."""
        oldIpAddress = IPAddress.asString(oldIpAddress)
        newIpAddress = IPAddress.asString(newIpAddress)
        # quite sensitive to quoting and not quoting
        command = r"sed -i -e 's/=\"\?" + re.escape(oldIpAddress) + r"\"\?/=\"" + re.escape(newIpAddress) + r"\"/'"
        if interface:
            command += r" '/etc/sysconfig/network-scripts/ifcfg-" + re.escape(interface) + r"'"
        else:
            # quite sensitive to quoting and not quoting
            command = r"for f in /etc/sysconfig/network-scripts/ifcfg-* ; do " + command + r" $f ; done"
        # oddly has been observed to require two times service network restart
        command += r" ; nohup sh -c 'service network restart ; service network restart' &> /dev/null &"
        return command

if __name__ == "__main__":
    print Clone.commandToChangeStaticIPAddress("10.123.45.67", "10.123.45.68")
    print Clone.commandToChangeStaticIPAddress("10.123.45.67", "10.123.45.68", interface="eth0")
