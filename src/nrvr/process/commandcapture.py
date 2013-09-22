#!/usr/bin/python

"""nrvr.process.commandcapture - Subprocesses wrapped for automation

The main class provided by this module is CommandCapture.

It should work in Linux and Windows.

On the downside, nothing has been coded yet in this module to allow input
into a running subprocess.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

from io import BlockingIOError
import os
import re
import subprocess
import sys
import threading
import time

_gotPty = False
try:
    import pty
    _gotPty = True
except ImportError:
    pass

class CommandCaptureException(Exception):
    def __init__(self, message):
        self._message = message
    def __str__(self):
        return unicode(self._message)
    @property
    def message(self):
        return self._message

class StreamCollector(threading.Thread):
    """Collects from a stream into a string, and optionally also copies
    into another stream."""
    def __init__(self, fromStream, toStream=None, flushToStream=False, slowDown=0.0):
        """Create new StreamCollector thread.
        
        Can be join()ed to wait until the thread terminates."""
        threading.Thread.__init__(self)
        self._fromStream = fromStream
        self._collected = ""
        self._toStream = toStream
        self._flushToStream = flushToStream
        self._slowDown = slowDown
        self._mostRecent = time.time()
        self._done = False
        self.start()
    def run(self):
        try:
            while True:
                line = self._fromStream.readline()
                if line != "":
                    self._collected += line
                    if self._slowDown > 0:
                        now = time.time()
                        stillToSleep = self._slowDown - (now - self._mostRecent)
                        if stillToSleep > 0:
                            time.sleep(stillToSleep)
                    if self._toStream:
                        print >> self._toStream, line.rstrip()
                        if self._flushToStream:
                            try:
                                self._toStream.flush()
                            except BlockingIOError:
                                pass # i.e. ignore for now
                    self._mostRecent = time.time()
                else:
                    break
        except IOError:
            # e.g. seen when going through an openpty() and then
            # after the subprocess.Popen's wait() doing an os.close(slave)
            pass
        finally:
            self._done = True
            try:
                # probably good to flush any remaining output
                self._toStream.flush()
            except:
                pass

    @property
    def collected(self):
        """A string containing all text that has been written to the stream."""
        return self._collected

class CommandCapture(object):
    """A subprocess wrapped for automation.
    
    This class uses subprocess.Popen.
    It further wraps for better use in automation.
    
    This class captures returncode, stdout and stderr.
    
    This class copies to stdio, unless constructed with copyToStdio=False.
    
    If module pty is available (e.g. in Python 2.6 on Linux, but not on Windows)
    and output is copied to stdio, and unless constructed with forgoPty=True,
    then uses pty.openpty() in order to see output right away.  Else uses pipes.
    Reason has been, more commands are flushing their stdout more often when
    they are thinking they are talking to a terminal, e.g. a pseudo-terminal,
    rather than buffering their output when they are thinking they are talking
    to a pipe.
    
    What is nice about this class, it keeps separate stdout and stderr while
    providing streaming output of both.
    Having separate stderr does make a difference not only for easily separately
    processing what the subprocess is writing to stderr, but also by maintaining
    the ability to show stderr in a different color, e.g. in red if using
    http://sourceforge.net/projects/hilite/.
    
    True defaults exceptionIfNotZero=True and exceptionIfAnyStderr=True should
    make for less hidden surprises when a subprocess encounters a problem,
    because exceptions by default would propagate up in a system of scripts,
    rather than being absorbed silently.
    Obviously, these parameters can be set False if needed.
    
    It should work in Linux and Windows.
    
    On the downside, nothing has been coded in this class to allow input
    into a running subprocess."""

    def __init__(self, args, copyToStdio=True, forgoPty=False,
                 exceptionIfNotZero=True, exceptionIfAnyStderr=True):
        """Create new CommandCapture instance.
        
        Will wait until completed.
        
        args
            are passed on to subprocess.Popen().
            
            If given a string instead of a list then fixed by args=[args],
            but that may only work as expected for a command without arguments.
        
        Example use::
        
            example = CommandCapture(["hostname"])
            print "returncode=" + str(example.returncode)
            print "stdout=" + example.stdout
            print >> sys.stderr, "stderr=" + example.stderr"""
        if isinstance(args, basestring):
            if re.search(r"\s", args):
                raise CommandCaptureException("MUST pass command args as list rather than as string: {0}".format(args))
            args = [args]
        self._args = args
        self._copyToStdio = copyToStdio
        self._forgoPty = forgoPty
        if not _gotPty:
            # cannot use pty module if not available, duh
            self._forgoPty = True
        if not self._copyToStdio:
            # if not watching output then no point in extra effort of using pty,
            # hence, for now
            self._forgoPty = True
        self._exceptionIfNotZero = exceptionIfNotZero
        self._exceptionIfAnyStderr = exceptionIfAnyStderr
        self._commandProcess = None
        self._returncode = None
        self._stdoutCollector = None
        self._stderrCollector = None
        self._stdoutSlave = None
        self._stderrSlave = None
        self._done = False
        try:
            if self._forgoPty:
                self._commandProcess = subprocess.Popen(self._args,
                                                        stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE)
                if self._copyToStdio:
                    self._stdoutCollector = StreamCollector(self._commandProcess.stdout,
                                                            toStream=sys.stdout, flushToStream=True)
                    self._stderrCollector = StreamCollector(self._commandProcess.stderr,
                                                            toStream=sys.stderr, flushToStream=True)
                else:
                    self._stdoutCollector = StreamCollector(self._commandProcess.stdout)
                    self._stderrCollector = StreamCollector(self._commandProcess.stderr)
                # note: could return from constructor here
                # and then have a wait() as a separate method,
                # but probably safer to keep here as is because of
                # potential issues around closing
                self._returncode = self._commandProcess.wait()
                self._stdoutCollector.join()
                self._stderrCollector.join()
            else:
                # use a pseudo-terminal (pty) so more commands flush their _stdout more often,
                # to see output right away
                stdoutMaster, self._stdoutSlave = pty.openpty()
                stderrMaster, self._stderrSlave = pty.openpty()
                stdoutMasterStream = os.fdopen(stdoutMaster, "r", 1)
                stderrMasterStream = os.fdopen(stderrMaster, "r", 1)
                self._commandProcess = subprocess.Popen(self._args,
                                                        stdout=self._stdoutSlave,
                                                        stderr=self._stderrSlave)
                if self._copyToStdio:
                    self._stdoutCollector = StreamCollector(stdoutMasterStream,
                                                            toStream=sys.stdout, flushToStream=True)
                    self._stderrCollector = StreamCollector(stderrMasterStream,
                                                            toStream=sys.stderr, flushToStream=True)
                else:
                    self._stdoutCollector = StreamCollector(stdoutMasterStream)
                    self._stderrCollector = StreamCollector(stderrMasterStream)
                # note: could return from constructor here
                # and then have a wait() as a separate method,
                # but probably safer to keep here as is because of
                # potential issues around closing
                self._returncode = self._commandProcess.wait()
                try:
                    os.close(self._stdoutSlave)
                except:
                    pass
                finally:
                    self._stdoutSlave = None
                try:
                    os.close(self._stderrSlave)
                except:
                    pass
                finally:
                    self._stderrSlave = None
                self._stdoutCollector.join()
                self._stderrCollector.join()
        finally:
            # note: could also have some of this cleanup in a __del__,
            # but be aware not all modules might be available
            # at the time Python itself is shutting down,
            # see pexpect spawn __del__,
            # overall probably safer to keep here as is
            if self._stdoutSlave != None:
                try:
                    os.close(self._stdoutSlave)
                except:
                    pass
                finally:
                    self._stdoutSlave = None
            if self._stderrSlave != None:
                try:
                    os.close(self._stderrSlave)
                except:
                    pass
                finally:
                    self._stderrSlave = None
            self._commandProcess = None
            if self._stdoutCollector:
                self._stdout = self._stdoutCollector.collected
                self._stdoutCollector = None
            else:
                self._stdout = None
            if self._stderrCollector:
                self._stderr = self._stderrCollector.collected
                self._stderrCollector = None
            else:
                self._stderr = None
            self._done = True
        # raise an exception if asked to and there is a reason
        self.raiseExceptionIfThereIsAReason()

    def raiseExceptionIfThereIsAReason(self):
        """Raise a CommandCaptureException if there is a reason.
        
        Available to provide standardized exception content in case calling code
        with exceptionIfAnyStderr=False after looking at .stderr decides
        in some circumstances only to raise an exception."""
        exceptionMessage = ""
        if self._exceptionIfAnyStderr and self._stderr:
            exceptionMessage += "stderr:\n" + self._stderr
        if self._exceptionIfNotZero and self._returncode:
            if exceptionMessage:
                exceptionMessage += "\n"
            exceptionMessage += "returncode: " + str(self._returncode)
        if exceptionMessage:
            commandDescription = "command:\n\t" + self._args[0]
            if len(self._args) > 1:
                commandDescription += "\narguments:\n\t" + "\n\t".join(self._args[1:])
            else:
                commandDescription += "\nno arguments"
            exceptionMessage = commandDescription + "\n" + exceptionMessage
            raise CommandCaptureException(exceptionMessage)

    @property
    def returncode(self):
        """Int returncode of subprocess."""
        return self._returncode

    @property
    def stdout(self):
        """Collected stdout string of subprocess."""
        return self._stdout

    @property
    def stderr(self):
        """Collected stderr string of subprocess."""
        return self._stderr

if __name__ == "__main__":
    _example1 = CommandCapture(["hostname"], forgoPty=True)
    print "returncode=" + str(_example1.returncode)
    print "stdout=" + _example1.stdout
    print >> sys.stderr, "stderr=" + _example1.stderr
    #
    _example2 = CommandCapture(["hostname"])
    print "returncode=" + str(_example2.returncode)
    print "stdout=" + _example2.stdout
    print >> sys.stderr, "stderr=" + _example2.stderr
    #
    _example3 = CommandCapture(["netstat"], copyToStdio=False)
    print "returncode=" + str(_example3.returncode)
    print "stdout=" + _example3.stdout
    print >> sys.stderr, "stderr=" + _example3.stderr
    #
    _example4 = CommandCapture(["ls"])
    print "returncode=" + str(_example4.returncode)
    print "stdout=" + _example4.stdout
    print >> sys.stderr, "stderr=" + _example4.stderr
    #
    try:
        _example5 = CommandCapture(["ls", "filethatdoesntexist"])
        print "returncode=" + str(_example5.returncode)
        print "stdout=" + _example5.stdout
        print >> sys.stderr, "stderr=" + _example5.stderr
    except Exception as ex:
        print "Exception ({0}):\n{1}".format(ex.__class__.__name__, str(ex))
    #
    _example6 = CommandCapture("ls")
    print "returncode=" + str(_example6.returncode)
    print "stdout=" + _example6.stdout
    print >> sys.stderr, "stderr=" + _example6.stderr
    #
    _example7 = CommandCapture(["echo", "givenonestring"])
    print "returncode=" + str(_example7.returncode)
    print "stdout=" + _example7.stdout
    print >> sys.stderr, "stderr=" + _example7.stderr
    #
    try:
        _example8 = CommandCapture("echo givenasonestring")
        print "returncode=" + str(_example8.returncode)
        print "stdout=" + _example8.stdout
        print >> sys.stderr, "stderr=" + _example6.stderr
    except Exception as ex:
        print "Exception ({0}):\n{1}".format(ex.__class__.__name__, str(ex))
