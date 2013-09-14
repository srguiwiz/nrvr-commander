#!/usr/bin/python

"""nrvr.distros.el.util - Utilities for manipulating Ubuntu

Class provided by this module is ElUtil.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import nrvr.distros.common.util

class UbUtil(nrvr.distros.common.util.LinuxUtil):
    """Utilities for manipulating an Ubuntu installation."""

    @classmethod
    def ubCommandToOpenFirewallPort(cls, port):
        """Build command to open a firewall TCP port.
        
        Must be root to succeed.
        
        As implemented does not check whether firewall is enabled.
        
        Return command to open a firewall TCP port."""
        port = int(port) # precaution
        port = str(port)
        command = "ufw allow " + port + "/tcp"
        return command

if __name__ == "__main__":
    print UbUtil.commandToAppendAddressNameLineToEtcHosts("127.0.0.1", "myself")
    print UbUtil.ubCommandToOpenFirewallPort(80)
    print UbUtil.ubCommandToOpenFirewallPort("80")
    print UbUtil.commandToWaitForNetworkDevice("eth1",30)
