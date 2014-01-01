#!/usr/bin/python

"""nrvr.util.nameserver - Utilities regarding domain name servers

Class provided by this module is Nameserver.

As implemented works in Linux.  Probably limited compatibility with Windows.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

import os.path
import re

from nrvr.util.classproperty import classproperty
from nrvr.util.ipaddress import IPAddress

class Nameserver(object):
    """Utilities regarding domain name servers."""

    # auxiliary
    _nameserverRegex = re.compile(r"^nameserver\s*(.+?)\s*$")

    @classproperty
    def list(cls):
        """List of IPAddress instances of known domain name servers.
        
        Also see http://linux.die.net/man/5/resolv.conf."""
        nameservers = []

        resolvConfFile = "/etc/resolv.conf"
        if os.path.exists(resolvConfFile):
            with open (resolvConfFile, "r") as inputFile:
                resolvConfLines = inputFile.readlines()
            for resolvConfLine in resolvConfLines:
                nameserverMatch = cls._nameserverRegex.search(resolvConfLine)
                if nameserverMatch:
                    nameserver = nameserverMatch.group(1)
                    if nameserver:
                        nameservers.append(nameserver)
        return nameservers

if __name__ == "__main__":
    print Nameserver.list
