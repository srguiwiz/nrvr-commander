#!/usr/bin/python

"""To use in developing and testing handling of process concurrency.
A useful utility by itself, try its --help option.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2015.
Simplified BSD License"""

from optparse import OptionParser
import os
import os.path
import sys
import time

optionsParser = OptionParser(usage="%prog [options]",
                             description=
"""Utility to use in developing and testing handling of process concurrency.
Sleep any number of seconds, less than one to thousands, optionally repeatedly.
Optionally output repetition of 'o' with any character count, useful for testing buffering.
Exit with status number.  If exit status number not 0 then final message to stderr.
Optional identity string in prefix of output lines, defaults to process id.
Works without options %prog or with options e.g. %prog -s 0.5 -r 3 -c 40 -x 1 -i A.
Also useful hilite %prog -s 0.5 -r 3 -c 40 -x 1 -i A ; echo $?.""",
                             version="%prog 1.0")
optionsParser.add_option("-s", "--sleep", type="float", dest="sleep",
                         help="seconds to sleep, default %default", default=5)
optionsParser.add_option("-r", "--repeat", type="int", dest="repeat",
                         help="repeat sleeping, default %default", default=1)
optionsParser.add_option("-c", "--charcount", type="int", dest="charcount",
                         help="character count for repetition of 'o', default %default", default=0)
optionsParser.add_option("-l", "--line", type="int", dest="line",
                         help="line length of repetition of 'o', default %default", default=100)
optionsParser.add_option("-x", "--exit", type="int", dest="exit",
                         help="exit with status, default %default", default=0)
optionsParser.add_option("-i", "--identity", type="string", dest="identity",
                         help="identity in prefix of output lines, default process id",
                         default="pid" + str(os.getpid()))
optionsParser.add_option("-f", "--flush", action="store_true", dest="flush",
                         help="flush after each line of output, default %default", default=False)
(options, args) = optionsParser.parse_args()

commandName = os.path.basename(sys.argv[0])
outputPrefix = "[" + commandName + "-" + options.identity + "]"
print outputPrefix + " begin"
if options.flush:
    sys.stdout.flush()
for i in range(1, options.repeat + 1):
    goingToSleepMessage = "going to sleep for %(sleep).6g seconds - %(i)d of %(n)d" % \
    {"sleep":options.sleep, "i":i, "n":options.repeat}
    if options.charcount > 0:
        goingToSleepMessage = \
        "after " + str(options.charcount) + " repetitions of 'o' " + goingToSleepMessage
    print outputPrefix + " " + goingToSleepMessage
    if options.flush:
        sys.stdout.flush()
    if options.charcount > 0:
        numberOfLines = (options.charcount - 1) // options.line + 1
        numberOfFullLines = options.charcount // options.line
        for j in range(numberOfLines):
            if j < numberOfFullLines:
                line = "o" * options.line
            else:
                line = "o" * (options.charcount % options.line)
            if j == 0:
                line = "<os>" + line
            if j == numberOfLines - 1:
                line = line + "</os>"
            print outputPrefix + " " + line
            if options.flush:
                sys.stdout.flush()
    time.sleep(options.sleep)
    print outputPrefix + " woke up"
    if options.flush:
        sys.stdout.flush()
print outputPrefix + " end"
if options.flush:
    sys.stdout.flush()
if options.exit != 0:
    print >> sys.stderr, outputPrefix + " exiting with status " + str(options.exit)
    if options.flush:
        sys.stderr.flush()
sys.exit(options.exit)
