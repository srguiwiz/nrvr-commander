#!/usr/bin/python

"""nrvr.el.gnome - Manipulate Enterprise Linux GNOME

Classes provided by this module include
* Gnome

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import re

class Gnome():
    """Utilities for manipulating a Gnome installation."""

    @classmethod
    def commandToEnableAutoLogin(cls, username=None):
        """Build command to enable auto-login into GNOME.
        
        Must be root to succeed.
        
        username
            defaults to None, which effects commandToDisableAutoLogin.
        
        Return command to enable auto-login into GNOME."""
        command = cls.commandToDisableAutoLogin()
        if username:
            username = re.escape(username) # precaution
            command += r" ; sed -i -e '/^\[daemon\]/ a \AutomaticLoginEnable=true\nAutomaticLogin=" + username + r"' /etc/gdm/custom.conf"
        return command

    @classmethod
    def commandToDisableAutoLogin(cls):
        """Build command to disable auto-login into GNOME.
        
        Must be root to succeed.
        
        Return command to disable auto-login into GNOME."""
        return r"sed -i -e '/^\s*AutomaticLoginEnable\s*=/ d' -e '/^\s*AutomaticLogin\s*=/ d' /etc/gdm/custom.conf"

    @classmethod
    def commandToDisableScreenSaver(cls):
        """Build command to disable screen saver of GNOME.
        
        Must be user to succeed.
        
        Return command to disable screen saver of GNOME."""
        command = "gconftool-2 -s /apps/gnome-screensaver/idle_activation_enabled --type=bool false"
        return command

    @classmethod
    def commandToEnableScreenSaver(cls):
        """Build command to enable screen saver of GNOME.
        
        Must be user to succeed.
        
        Return command to enable screen saver of GNOME."""
        command = "gconftool-2 -s /apps/gnome-screensaver/idle_activation_enabled --type=bool true"
        return command

if __name__ == "__main__":
    print Gnome.commandToEnableAutoLogin("joe")
    print Gnome.commandToDisableAutoLogin()
    print Gnome.commandToEnableAutoLogin()
    print Gnome.commandToDisableScreenSaver()
    print Gnome.commandToEnableScreenSaver()
