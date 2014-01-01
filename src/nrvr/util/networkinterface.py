#!/usr/bin/python

"""nrvr.util.networkinterface - Utilities regarding network interfaces

Classes provided by this module include
* NetworkInterface
* NetworkConfigurationStaticParameters

Works in Linux and Mac OS X.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

from collections import namedtuple
import math
import re

from nrvr.process.commandcapture import CommandCapture
from nrvr.util.ipaddress import IPAddress

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
    def ipAddressOf(cls, networkInterfaceName):
        """For networkInterfaceName="lo" return "127.0.0.1".
        
        networkInterfaceName
            the name of the interface.
        
        Return the IP address of the interface, or None."""
        # as implemented absent ifconfig command return as if interface not found
        ifconfig = CommandCapture(["ifconfig", networkInterfaceName],
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
    print NetworkInterface.ipAddressOf("lo")
    print NetworkInterface.ipAddressOf("lo0")
    print NetworkInterface.ipAddressOf("vmnet1")
    print NetworkInterface.ipAddressOf("madesomethingup")


class NetworkConfigurationStaticParameters(namedtuple("NetworkConfigurationStaticParameters",
                                                      ["ipaddress", "netmask", "gateway", "nameservers"])):
    """Static IP options for network configuration.
    
    As implemented only supports IPv4."""

    __slots__ = ()

    @property
    def routingprefixlength(self):
        """Return an integer."""
        netmask = IPAddress.asList(self.netmask)
        # for an easy way to determine the highest bit set see https://wiki.python.org/moin/BitManipulation
        return 8 * len(netmask) - int(math.floor(math.log(IPAddress.asInteger(IPAddress.bitNot(netmask)) + 1, 2)))

    @property
    def localprefix(self):
        return IPAddress.bitAnd(self.ipaddress, self.netmask)

    @classmethod
    def normalizeStaticIp(self, ipaddress, netmask="255.255.255.0", gateway=None, nameservers=None):
        """Normalize static IP options for network configuration.
        
        As implemented only supports IPv4.
        
        ipaddress
            IP address.
        
        netmask
            netmask.
            Defaults to 255.255.255.0.
        
        gateway
            gateway.
            If None then default to ip.1.
        
        nameservers
            one nameserver or a list of nameservers.
            If None then default to gateway.
            If empty list then remove option.
        
        return
            a NetworkConfigurationStaticParameters instance."""
        # also see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        # sanity check
        ipaddress = IPAddress.asString(ipaddress)
        if not re.match(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$", ipaddress):
            raise Exception("won't accept apparently impossible IP address {0}".format(ipaddress))
        netmask = IPAddress.asString(netmask)
        if gateway is None:
            # default to ip.1
            gateway = IPAddress.bitOr(IPAddress.bitAnd(ipaddress, netmask), "0.0.0.1")
        gateway = IPAddress.asString(gateway)
        if nameservers is None:
            # default to gateway
            nameservers = [gateway]
        elif not isinstance(nameservers, list):
            # process one as a list of one
            nameservers = [nameservers]
        else:
            # given a list already
            nameservers = nameservers
        nameserversStrings = [IPAddress.asString(oneNameserver) for oneNameserver in nameservers]
        normalized = NetworkConfigurationStaticParameters(ipaddress=ipaddress,
                                                          netmask=netmask,
                                                          gateway=gateway,
                                                          nameservers=nameserversStrings)
        return normalized
