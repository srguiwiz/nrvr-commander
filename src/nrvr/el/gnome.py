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
    def activateAutoLoginCommand(cls, username=None):
        """Build command to activate auto-login into GNOME.
        
        username
            defaults to None, which effects deactivateAutoLoginCommand.
        
        Return command to activate auto-login into GNOME."""
        command = cls.deactivateAutoLoginCommand()
        if username:
            username = re.escape(username) # precaution
            command += r" ; sed -i -e '/^\[daemon\]/ a \AutomaticLoginEnable=true\nAutomaticLogin=" + username + r"' /etc/gdm/custom.conf"
        return command
    
    @classmethod
    def deactivateAutoLoginCommand(cls):
        """Build command to deactivate auto-login into GNOME.
        
        Return command to deactivate auto-login into GNOME."""
        return r"sed -i -e '/^\s*AutomaticLoginEnable\s*=/ d' -e '/^\s*AutomaticLogin\s*=/ d' /etc/gdm/custom.conf"

if __name__ == "__main__":
    print Gnome.activateAutoLoginCommand("joe")
    print Gnome.deactivateAutoLoginCommand()
    print Gnome.activateAutoLoginCommand()
