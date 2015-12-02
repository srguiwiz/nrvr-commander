#!/usr/bin/python

"""nrvr.distros.el.util - Utilities for manipulating Linux

Class provided by this module is LinuxUtil.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2015.
Simplified BSD License"""

import re

from nrvr.util.ipaddress import IPAddress

class LinuxUtil():
    """Utilities for manipulating a Linux installation."""

    @classmethod
    def commandToAppendAddressNameLineToEtcHosts(cls, ipaddress, name):
        """Build command to append an ipaddress hostname line to /etc/hosts.
        
        Only if no line yet.
        As implemented any fgrep match of name in /etc/hosts prevents addition.
        
        Must be root to succeed.
        
        Return command to append an ipaddress hostname line to /etc/hosts."""
        name = re.escape(name) # precaution
        ipaddress = IPAddress.asString(ipaddress)
        command = "fgrep -q -e '" + name + "' /etc/hosts || " \
                  + "echo '" + ipaddress + " " + name + "' >> /etc/hosts"
        return command

    @classmethod
    def commandToWaitForNetworkDevice(cls, device="eth0", maxSeconds="100"):
        """Build command to wait for a network device to connect.
        
        Only waits if not connected yet.
        
        As implemented depends on NetworkManager tabular mode outputting "connected".
        
        Need not be root to succeed.
        
        device
            e.g. "eth0".
        
        maxSeconds
            maximum number of seconds to wait.
        
        Return command to wait for a network device to connect."""
        maxSeconds = abs(int(maxSeconds)) # precaution
        maxSeconds = str(maxSeconds)
        command = r"i=0 ; while (( $i < " + maxSeconds + r" )) ; do" + \
                  r" s=`nmcli -f device,state dev |" + \
                  r" sed -r -n -e 's/^\s*" + re.escape(device.strip()) + r"\s+(.*\S)\s*/\1/p'` ;" + \
                  r" if [[ $s = 'connected' ]] ; then i=" + maxSeconds + r" ; else sleep 1 ; (( i++ )) ; fi" + \
                  r" ; done"
        return command

    @classmethod
    def commandToEnableSudo(cls, username=None):
        """Build command to enable sudo.
        
        As implemented in /etc/sudoers duplicates any (presumably only one) line
        starting with "root " and replaces "root" with the username.
        
        Must be root to succeed.
        
        Return command to enable sudo."""
        username = re.escape(username) # precaution
        command = r"sed -i -e '/^root\s/ p; s/^root\(\s\.*\)/" + \
                  r"# Made same for user " + username + r" too\n" + username + r"\1/' /etc/sudoers"
        return command

if __name__ == "__main__":
    print LinuxUtil.commandToAppendAddressNameLineToEtcHosts("127.0.0.1", "myself")
    print LinuxUtil.commandToWaitForNetworkDevice("eth1",30)
    print LinuxUtil.commandToEnableSudo("joe")
