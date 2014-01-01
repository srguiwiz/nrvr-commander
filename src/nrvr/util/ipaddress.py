#!/usr/bin/python

"""nrvr.util.ipaddress - Utilities regarding IP addresses

Class provided by this module is IPAddress.

Works in Linux and Windows.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

import re

class IPAddress(object):
    """Methods for multiple machines on one subnet.
    
    As implemented only supports IPv4."""

    octetsRegex = re.compile(r"^\s*([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\s*$")

    @classmethod
    def asList(cls, ipaddress, rangeCheck=False):
        """For ipaddress="10.123.45.67" return mutable [10, 123, 45, 67].
        
        If already a list, a copy is made and returned."""
        if isinstance(ipaddress, basestring):
            octetsMatch = IPAddress.octetsRegex.search(ipaddress)
            if not octetsMatch:
                raise Exception("won't recognize as IP address: {0}".format(ipaddress))
            octets = [octetsMatch.group(1),
                      octetsMatch.group(2),
                      octetsMatch.group(3),
                      octetsMatch.group(4)]
            for index, octet in enumerate(octets):
                octet = int(octet)
                if rangeCheck and octet > 255:
                    raise Exception("won't recognize as IP address because > 255: {0}".format(ipaddress))
                octets[index] = octet
            return octets
        elif isinstance(ipaddress, (int, long)):
            octets = []
            while ipaddress:
                octets.append(ipaddress % 256)
                ipaddress /= 256
            octets += [0 for i in range(max(4 - len(octets), 0))]
            octets.reverse()
            return octets
        else:
            # force making a copy
            return list(ipaddress)

    @classmethod
    def asTuple(cls, ipaddress):
        """For ipaddress="10.123.45.67" return immutable (10, 123, 45, 67)."""
        if isinstance(ipaddress, tuple):
            return ipaddress
        elif isinstance(ipaddress, list):
            return tuple(ipaddress)
        else:
            return tuple(cls.asList(ipaddress))

    @classmethod
    def asString(cls, ipaddress):
        """For ipaddress=[10, 123, 45, 67] return "10.123.45.67"."""
        if isinstance(ipaddress, basestring):
            return ipaddress
        if isinstance(ipaddress, (int, long)):
            ipaddress = cls.asList(ipaddress)
        return ".".join(map(str, ipaddress))

    @classmethod
    def asInteger(cls, ipaddress):
        """For ipaddress=[10, 123, 45, 67] return 175844675.
        
        At the time of this writing, such an integer however is
        not accepted as input by other methods of this class."""
        octets = cls.asList(ipaddress) # must make a copy
        integer = 0
        while octets:
            integer = 256 * integer + octets.pop(0)
        return integer

    @classmethod
    def bitAnd(cls, one, other):
        if not isinstance(one, (list, tuple)):
            one = cls.asList(one)
        if not isinstance(other, (list, tuple)):
            other = cls.asList(other)
        octets = []
        for oneOctet, otherOctet in zip(one, other):
            octets.append(oneOctet & otherOctet)
        return octets

    @classmethod
    def bitOr(cls, one, other):
        if not isinstance(one, (list, tuple)):
            one = cls.asList(one)
        if not isinstance(other, (list, tuple)):
            other = cls.asList(other)
        octets = []
        for oneOctet, otherOctet in zip(one, other):
            octets.append(oneOctet | otherOctet)
        return octets

    @classmethod
    def bitNot(cls, one):
        if not isinstance(one, (list, tuple)):
            one = cls.asList(one)
        octets = []
        for oneOctet in one:
            octets.append(~oneOctet & 255)
        return octets

    @classmethod
    def nameWithNumber(cls, stem, ipaddress, octets=1, separator="-"):
        """For stem="example" and ipaddress="10.123.45.67" return "example-067".
        
        If octets=2 return "example-045-067"."""
        name = stem
        ipaddress = IPAddress.asTuple(ipaddress)
        if not separator:
            # empty string instead of e.g. None
            separator = ""
        for index in range(-octets, 0):
            # create leading zeros, e.g. from "19" to "019"
            name += separator + "%03d" % ipaddress[index]
        return name

    @classmethod
    def numberWithinSubnet(cls, oneInSubnet, otherNumber, netmask="255.255.255.0"):
        """For oneInSubnet="10.123.45.67" and otherNumber="89" return [10, 123, 45, 89].
        
        For oneInSubnet="10.123.45.67" and otherNumber="89.34" and netmask="255.255.0.0" return [10, 123, 89, 34]."""
        if not isinstance(oneInSubnet, (list, tuple)):
            oneInSubnet = cls.asList(oneInSubnet)
        # less than stellar decoding of otherNumber, but it works in actual use cases
        if isinstance(otherNumber, int):
            # in theory handling more than 16 bits' 65536 would be desirable,
            # practically handling up to 16 bits' 65535 is enough
            if otherNumber <= 255:
                otherNumber = [otherNumber]
            else:
                otherNumber = [otherNumber >> 8, otherNumber & 255]
        if not isinstance(otherNumber, (list, tuple)):
            otherNumber = otherNumber.split(".")
            otherNumber = map(int, otherNumber)
        if not isinstance(netmask, (list, tuple)):
            netmask = cls.asList(netmask)
        complementOfNetmask = cls.bitNot(netmask)
        contributedBySubnet = cls.bitAnd(oneInSubnet, netmask)
        otherNumber = [0] * (len(contributedBySubnet) - len(otherNumber)) + otherNumber
        contributedByNumber = cls.bitAnd(otherNumber, complementOfNetmask)
        result = cls.bitOr(contributedBySubnet, contributedByNumber)
        return result

if __name__ == "__main__":
    print IPAddress.asList("10.123.45.67")
    print IPAddress.asList((192, 168, 95, 17))
    print IPAddress.asList([192, 168, 95, 17])
    print IPAddress.asList(175844675)
    print IPAddress.asTuple("10.123.45.67")
    print IPAddress.asTuple([192, 168, 95, 17])
    print IPAddress.asTuple((192, 168, 95, 17))
    print IPAddress.asTuple(175844675)
    print IPAddress.asString([192, 168, 95, 17])
    print IPAddress.asString((192, 168, 95, 17))
    print IPAddress.asString("10.123.45.67")
    print IPAddress.asString(175844675)
    print IPAddress.asInteger("10.123.45.67")
    print IPAddress.asInteger([10,123,45,67])
    print IPAddress.bitAnd("10.123.45.67", "255.255.255.0")
    print IPAddress.bitOr(IPAddress.bitAnd("10.123.45.67", "255.255.255.0"), "0.0.0.1")
    print IPAddress.bitNot("1.2.3.4")
    print IPAddress.nameWithNumber("example", "10.123.45.67")
    print IPAddress.nameWithNumber("example", "10.123.45.67", octets=2)
    print IPAddress.nameWithNumber("example", "10.123.45.67", octets=3)
    print IPAddress.nameWithNumber("example", "10.123.45.67", octets=4)
    print IPAddress.numberWithinSubnet("10.123.45.67", "89")
    print IPAddress.numberWithinSubnet("10.123.45.67", 89)
    print IPAddress.numberWithinSubnet("10.123.45.67", "89.34", netmask="255.255.0.0")
    print IPAddress.numberWithinSubnet("10.123.45.67", 22818, netmask="255.255.0.0")
