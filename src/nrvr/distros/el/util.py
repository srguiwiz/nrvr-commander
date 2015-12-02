#!/usr/bin/python

"""nrvr.distros.el.util - Utilities for manipulating Enterprise Linux

Class provided by this module is ElUtil.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2015.
Simplified BSD License"""

import nrvr.distros.common.util

class ElUtil(nrvr.distros.common.util.LinuxUtil):
    """Utilities for manipulating an Enterprise Linux installation."""

    @classmethod
    def elCommandToOpenFirewallPort(cls, port):
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

if __name__ == "__main__":
    print ElUtil.commandToAppendAddressNameLineToEtcHosts("127.0.0.1", "myself")
    print ElUtil.elCommandToOpenFirewallPort(80)
    print ElUtil.elCommandToOpenFirewallPort("80")
    print ElUtil.commandToWaitForNetworkDevice("eth1",30)
