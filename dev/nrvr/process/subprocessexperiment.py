#!/usr/bin/python

"""A number of tests of the subprocess and pty modules
that have led to knowledge jotted down in its comments and knowledge
being used in making src/nrvr/process/commandcapture.py.
Keep around for code and comments.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

from io import BlockingIOError
from optparse import OptionParser
import os
import subprocess
import sys
import threading
import time

gotPty = False
if sys.platform.startswith('linux'):
    try:
        import pty
        gotPty = True
    except ImportError:
        pass

class StreamCollector(threading.Thread):
    def __init__(self, fromStream, teeStream=None, flushTeeStream=False,
                 slowDown=0 # just for testing purposes
                 ):
        threading.Thread.__init__(self)
        self.fromStream = fromStream
        self.collected = ""
        self.teeStream = teeStream
        self.flushTeeStream = flushTeeStream
        self.slowDown = slowDown
        self.done = False
        self.start()
    def run(self):
        try:
            while True:
                line = self.fromStream.readline()
                if line != '':
                    self.collected += line
                    if self.teeStream:
                        print >> self.teeStream, line.rstrip()
                        if self.flushTeeStream:
                            try:
                                self.teeStream.flush()
                            except BlockingIOError:
                                pass # i.e. ignore for now
                else:
                    break
                if self.slowDown > 0:
                    time.sleep(self.slowDown)
        except IOError:
            # e.g. seen when going through an openpty() and then after the subprocess.Popen's wait()
            # doing an os.close(slave)
            pass
        finally:
            self.done = True

optionsParser = OptionParser()
optionsParser.add_option("-t", "--test", type="int", dest="test",
                         help="which test to run, default %default", default=1)
(options, args) = optionsParser.parse_args()

scriptDirectory = os.path.dirname(os.path.abspath(__file__))
sleeperScript = os.path.join(scriptDirectory, "sleeper.py")

print "Begin of test #" + str(options.test) + ".",
print "pid=" + str(os.getpid())

if options.test == 1:
    subprocess.Popen([sleeperScript, "-s10", "-r3", "-c300", "-x1"])
    """If you watch here with ps -ef | grep \\.py you will find both process ids."""
    time.sleep(15)
    """If you watch here with ps -ef | grep \\.py you will find the subprocess id only
    before it exits too.
    But if you go looking with ps -ef | grep for the pid you will find a line saying
    [subprocess-expe] <defunct>.
    Also, a following command sequenced e.g. by ; will not execute until the subprocess
    has exited too."""

elif options.test == 2:
    sleeper = subprocess.Popen([sleeperScript, "-s1", "-r3", "-c300", "-x1"])
    returncode = sleeper.wait()
    print "returncode=" + str(returncode)
    """You may want to test wait doesn't block even with a very large character count,
    e.g. -c30000000.
    You also may want to test wait really returns the returncode."""

elif options.test == 3:
    sleeper = subprocess.Popen([sleeperScript, "-s1", "-r3", "-c300", "-x1"],
                               stdout=subprocess.PIPE)
    for line in sleeper.stdout:
        print "From sleeper: " + line.rstrip()
    returncode = sleeper.wait()
    print "returncode=" + str(returncode)
    """With this one you see the problems of buffering.
    See the sleeper's stderr "exiting with status 1" coming through first?
    Nothing comes through from stdout until it is done, or its buffer is full.
    On the upside, apparently it doesn't lose anything or doesn't block
    if used just like this, even with -c30000.
    But this code isn't trying to get read large stderr at the same time."""

elif options.test == 4:
    sleeper = subprocess.Popen([sleeperScript, "-s10", "-r3", "-c300", "-x1"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutCollector = StreamCollector(sleeper.stdout, sys.stdout, True)
    stderrCollector = StreamCollector(sleeper.stderr, sys.stderr, True)
    returncode = sleeper.wait()
    stdoutCollector.join()
    stderrCollector.join()
    print "returncode=" + str(returncode)
    print "stdout=" + stdoutCollector.collected
    print >> sys.stderr, "stderr=" + stderrCollector.collected
    """Nicely has collected copies available in strings, for use as needed.
    Still, with this one you see the problems of buffering.
    Nothing comes through from stdout until it is done, or its buffer is full.
    Also, see the sleeper's stderr "exiting with status 1" coming through first?
    On the upside, apparently it doesn't lose anything or doesn't block
    if used just like this, even with -c30000."""

elif options.test == 5:
    sleeper = subprocess.Popen([sleeperScript, "-s10", "-r3", "-c300", "-x1", "-f"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutCollector = StreamCollector(sleeper.stdout, sys.stdout, True)
    stderrCollector = StreamCollector(sleeper.stderr, sys.stderr, True)
    returncode = sleeper.wait()
    stdoutCollector.join()
    stderrCollector.join()
    print "returncode=" + str(returncode)
    print "stdout=" + stdoutCollector.collected
    print >> sys.stderr, "stderr=" + stderrCollector.collected
    """If the program you call flushes all the time then there is
    no delay because of buffering.
    But when they notice they're talking to a pipe, many programs don't flush.
    They only flush if they're thinking they're talking to a terminal."""

elif options.test == 6:
    sleeper = subprocess.Popen(sleeperScript + " -s10 -r3 -c300 -x1",
                               shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutCollector = StreamCollector(sleeper.stdout, sys.stdout, True)
    stderrCollector = StreamCollector(sleeper.stderr, sys.stderr, True)
    returncode = sleeper.wait()
    stdoutCollector.join()
    stderrCollector.join()
    print "returncode=" + str(returncode)
    print "stdout=" + stdoutCollector.collected
    print >> sys.stderr, "stderr=" + stderrCollector.collected
    """Nicely has collected copies available in strings, for use as needed.
    Still, with this one you see the problems of buffering.
    Nothing comes through from stdout until it is done, or its buffer is full.
    Also, see the sleeper's stderr "exiting with status 1" coming through first?
    On the upside, apparently it doesn't lose anything or doesn't block
    if used just like this, even with -c30000."""

elif options.test == 7:
    stdoutMaster, stdoutSlave = pty.openpty()
    stderrMaster, stderrSlave = pty.openpty()
    stdoutMasterStream = os.fdopen(stdoutMaster, "r", 1)
    stderrMasterStream = os.fdopen(stderrMaster, "r", 1)
    sleeper = subprocess.Popen([sleeperScript, "-s2", "-r3", "-c300", "-x1"],
                               stdout=stdoutSlave, stderr=stderrSlave)
    stdoutCollector = StreamCollector(stdoutMasterStream, sys.stdout, True)
    stderrCollector = StreamCollector(stderrMasterStream, sys.stderr, True)
    print "BEFORE WAIT"
    returncode = sleeper.wait()
    print "AFTER WAIT"
    os.close(stdoutSlave)
    os.close(stderrSlave)
    print "AFTER CLOSE"
    stdoutCollector.join()
    print "AFTER FIRST JOIN"
    stderrCollector.join()
    print "AFTER SECOND JOIN"
    print "returncode=" + str(returncode)
    print "stdout=" + stdoutCollector.collected
    print >> sys.stderr, "stderr=" + stderrCollector.collected
    """Coming through nicely and timely and being captured.
    Must watch out though according to man page of openpty
    http://www.kernel.org/doc/man-pages/online/pages/man3/openpty.3.html
    http://linux.die.net/man/3/openpty
    "The openpty() function finds an available pseudoterminal" and
    "openpty() will fail if ENOENT There are no available ttys."
    Which may mean this only is safe to use if one doesn't run too many at once.
    But luckily according to man page of pty
    http://www.kernel.org/doc/man-pages/online/pages/man7/pty.7.html
    http://linux.die.net/man/7/pty
    "Since kernel 2.6.4, the limit is dynamically adjustable via
    /proc/sys/kernel/pty/max, and a corresponding file, /proc/sys/kernel/pty/nr,
    indicates how many pseudoterminals are currently in use."
    A quick check on one machine showed safe margins:
    cat /proc/sys/kernel/pty/max gave 4096,
    cat /proc/sys/kernel/pty/nr gave 8.
    Apparently /proc/sys/kernel/pty/nr is broken, possibly since Linux kernel 2.6.28,
    described in Peter Anvin's http://lkml.org/lkml/2009/11/5/401.
    Closing of a pseudo-terminal is discussed in man page of close
    http://linux.die.net/man/3/close."""

elif options.test == 8:
    stdoutMaster, stdoutSlave = pty.openpty()
    stderrMaster, stderrSlave = pty.openpty()
    stdoutMasterStream = os.fdopen(stdoutMaster, "r", 1)
    stderrMasterStream = os.fdopen(stderrMaster, "r", 1)
    sleeper = subprocess.Popen([sleeperScript, "-s2", "-r3", "-c300", "-x1"],
                               stdout=stdoutSlave, stderr=stderrSlave)
    stdoutCollector = StreamCollector(stdoutMasterStream, sys.stdout, True, 1.0)
    stderrCollector = StreamCollector(stderrMasterStream, sys.stderr, True, 1.0)
    print "BEFORE WAIT"
    returncode = sleeper.wait()
    print "AFTER WAIT"
    os.close(stdoutSlave)
    os.close(stderrSlave)
    print "AFTER CLOSE"
    stdoutCollector.join()
    print "AFTER FIRST JOIN"
    stderrCollector.join()
    print "AFTER SECOND JOIN"
    print "returncode=" + str(returncode)
    print "stdout=" + stdoutCollector.collected
    print >> sys.stderr, "stderr=" + stderrCollector.collected
    """Checking whether it works correctly with artificial slowDown in StreamCollector."""

    """Next to implement:  Wrapper class for Popen, ask whether to copy to stdout and stderr,
    if so then if Linux use pty unless flag set not to use it
    (i.e. in most cases show output sooner,
    but can't if not Linux,
    and allow to switch off if child process would e.g. wait for input if on terminal or just be different"""

else:
    print >> sys.stderr, "Unknown test number " + str(options.test)
    sys.exit(2)

print "End of test."
