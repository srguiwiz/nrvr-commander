#!/usr/bin/python

"""Loop over running a set of test scripts in a directory.

Made for use within NrvrCommander.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

import glob
import os
import os.path
import sys
import time

numberOfIterations = 3
secondsBetweenTests = 5
secondsBetweenIterations = 15

scriptDirectory = os.path.dirname(os.path.abspath(__file__))
testsDirectory = os.path.join(scriptDirectory, "tests")
testsGlob = os.path.join(testsDirectory, "*.py")

tests = glob.glob(testsGlob)
tests.sort()

def stdFlush():
    sys.stdout.flush()
    sys.stderr.flush()

print "STARTING running %s" % (__file__)
print "STARTING running %d iterations of tests in %s" % (numberOfIterations, testsDirectory)
stdFlush()
for iteration in range(0, numberOfIterations):
    for test in tests:
        print "STARTING iteration #%d of %s" % (iteration, test)
        stdFlush()
        try:
            os.system("python " + test)
            stdFlush()
            print "NORMALLY completed iteration #%d of %s" % (iteration, test)
            stdFlush()
        except Exception as ex:
            stdFlush()
            print "EXCEPTION out of iteration #%d of %s:" % (iteration, test)
            print ex
            stdFlush()
            sys.exc_clear()
        #
        print "sleeping %d seconds between tests" % secondsBetweenTests
        stdFlush()
        time.sleep(secondsBetweenTests)
    #
    print "sleeping %d seconds between iterations" % secondsBetweenIterations
    stdFlush()
    time.sleep(secondsBetweenIterations)

print "DONE running %d iterations of tests in %s" % (numberOfIterations, testsDirectory)
print "DONE running %s" % (__file__)
stdFlush()
