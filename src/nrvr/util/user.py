#!/usr/bin/python

"""nrvr.util.user - Utilities regarding user running script

Class provided by this module is ScriptUser.

As implemented works in Linux.  Probably limited compatibility with Windows.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import getpass
import os.path

from nrvr.util.classproperty import classproperty

class ScriptUser(object):
    """A user running the script."""

    def __init__(self, userName):
        """Create new user descriptor."""
        self._userName = userName

    @property
    def userName(self):
        """User name.
        
        Maybe better described as the alphanumeric user id."""
        return self._userName

    @property
    def userHome(self):
        """User's home directory."""
        return os.path.expanduser("~" + self.userName)

    def userHomeRelative(self, path=""):
        """Interpret given path relative to user's home directory."""
        return os.path.join(self.userHome, path)

    @classproperty
    def loggedIn(cls):
        """ScriptUser instance for the user logged into the terminal.
        
        In case of sudo then logged in user instead of root."""
        osMethodGetlogin = getattr(os, "getlogin", None) # check whether method is implemented
        if callable(osMethodGetlogin):
            # coded so if sudo then real user instead of root
            loggedInUserName = os.getlogin()
        else:
            loggedInUserName = getpass.getuser()
        return ScriptUser(loggedInUserName)

    @classproperty
    def current(cls):
        """ScriptUser instance for currently effective user."""
        currentUserName = getpass.getuser()
        return ScriptUser(currentUserName)

    @classmethod
    def rootRequired(cls):
        """Raise exception if not running as root."""
        osMethodGetuid = getattr(os, "getuid", None) # check whether method is implemented
        if callable(osMethodGetuid) and os.getuid() != 0:
            raise Exception("must run as root")
        # TODO maybe in Windows check ctypes.windll.shell32.IsUserAnAdmin()
        pass

if __name__ == "__main__":
    print ScriptUser.loggedIn.userName
    print ScriptUser.loggedIn.userHome
    print ScriptUser.loggedIn.userHomeRelative('stuff')
    print ScriptUser.current.userName
    print ScriptUser.current.userHome
    print ScriptUser.current.userHomeRelative('stuff')
    #ScriptUser.rootRequired()
