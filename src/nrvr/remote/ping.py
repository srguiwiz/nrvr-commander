#!/usr/bin/python

"""nrvr.remote.ping - Ping IP addresses

Class provided by this module is Ping.

As implemented works in Linux.
As implemented requires ping command with option -c count.

First implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2015.
Simplified BSD License"""

import sys
from threading import Thread

from nrvr.process.commandcapture import CommandCapture

class Ping(object):
    """Ping IP addresses."""

    @classmethod
    def commandsUsedInImplementation(cls):
        """Return a list to be passed to SystemRequirements.commandsRequired().
        
        This class can be passed to SystemRequirements.commandsRequiredByImplementations()."""
        return ["ping"]

    @classmethod
    def respondingIpAddressesOf(cls, ipaddresses, numberOfTries=3, maxConcurrency=50, ticker=True):
        """Return a new list constructed from those IP addresses that have responded."""
        threads = [None] * len(ipaddresses)
        results = ['?'] * len(ipaddresses)
        
        def ping(ipaddress, i):
            ping = CommandCapture(["ping", "-c", str(numberOfTries), str(ipaddress)],
                                  copyToStdio=False, exceptionIfNotZero=False)
            if not ping.returncode: # returncode 0 means success
                results[i] = ipaddress
            else:
                results[i] = "-"
        
        # ceiling division as shown at http://stackoverflow.com/questions/14822184/is-there-a-ceiling-equivalent-of-operator-in-python
        blocks = -(-len(ipaddresses) // maxConcurrency)
        if ticker:
            sys.stdout.write("[ping")
            sys.stdout.flush()
        for block in range(blocks):
            for i in range(block * maxConcurrency, min((block + 1) * maxConcurrency, len(ipaddresses))):
                ipaddress = ipaddresses[i]
                thread = Thread(target=ping, args=[ipaddress, i])
                threads[i] = thread
                thread.start()
            for i in range(block * maxConcurrency, min((block + 1) * maxConcurrency, len(ipaddresses))):
                thread = threads[i]
                thread.join()
                threads[i] = None
                if ticker:
                    sys.stdout.write(".")
                    sys.stdout.flush()
        if ticker:
            sys.stdout.write("]\n")
        return filter(lambda result: result != '-', results)

if __name__ == "__main__":
    from nrvr.util.requirements import SystemRequirements
    SystemRequirements.commandsRequiredByImplementations([Ping], verbose=True)
    #
    print Ping.respondingIpAddressesOf(["127.0.0.1", "127.0.0.2"])
    print Ping.respondingIpAddressesOf(map(lambda number: "127.0.0." + str(number), range(1, 31)))
    print Ping.respondingIpAddressesOf(map(lambda number: "127.0.0." + str(number), range(1, 132)))
