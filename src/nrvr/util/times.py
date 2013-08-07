#!/usr/bin/python

"""nrvr.util.times - Utilities regarding time

Class provided by this module is Timestamp.

It should work in Linux and Windows.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

# original name of module had been nrvr.util.time but there was an import conflict
# when running a test in the same directory:
#
#mac:nrvr-commander me$ ~/Projects/nrvr-commander/src/nrvr/util/networkinterface.py 
#Traceback (most recent call last):
#  File "~/Projects/nrvr-commander/src/nrvr/util/networkinterface.py", line 18, in <module>
#    from nrvr.process.commandcapture import CommandCapture
#  File "/Library/Python/2.7/site-packages/nrvr/process/commandcapture.py", line 24, in <module>
#    import threading
#  File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/threading.py", line 13, in <module>
#    from time import time as _time, sleep as _sleep
#ImportError: cannot import name time

import datetime

class Timestamp(object):
    """Canonical timestamps."""
    @classmethod
    def microsecondTimestamp(cls):
        """A 22 character timestamp, at least theoretically to the microsecond.
        
        E.g. 20061128T230056Z469534"""
        return datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ%f")

if __name__ == "__main__":
    print Timestamp.microsecondTimestamp()
