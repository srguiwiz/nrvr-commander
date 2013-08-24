#!/usr/bin/python

"""nrvr.distros.el.util - Utilities for manipulating Enterprise Linux

Class provided by this module is ElUtil.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import re

from nrvr.util.ipaddress import IPAddress

class ElUtil():
    """Utilities for manipulating an Enterprise Linux installation."""

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
    def commandToOpenFirewallPort(cls, port):
        """Build command to open a firewall port.
        
        Only if not recognizably open yet.
        
        As implemented copies /etc/sysconfig/iptables line containing --dport 22 .
        
        Must be root to succeed.
        
        Return command to open a firewall port."""
        port = int(port) # precaution
        port = str(port)
        command = "fgrep -q -e '--dport " + port + " ' /etc/sysconfig/iptables || " \
                  + "( sed -i -e '/--dport 22 / p' -e 's/--dport 22 /--dport " + port + " /' /etc/sysconfig/iptables" \
                  + " ; service iptables restart )"
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

if __name__ == "__main__":
    print ElUtil.commandToAppendAddressNameLineToEtcHosts("127.0.0.1", "myself")
    print ElUtil.commandToOpenFirewallPort(80)
    print ElUtil.commandToOpenFirewallPort("80")
    print ElUtil.commandToWaitForNetworkDevice("eth1",30)
