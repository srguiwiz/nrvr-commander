#!/usr/bin/python

"""nrvr.util.time - Utilities regarding time

Class provided by this module is Timestamp.

It should work in Linux and Windows.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

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
