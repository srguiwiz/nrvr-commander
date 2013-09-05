#!/usr/bin/python

"""nrvr.distros.common.gnome - Manipulate Linux distribution GNOME

Class provided by this module is Gnome.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import re

class Gnome():
    """Utilities for manipulating a Gnome installation."""

    @classmethod
    def commandToTellWhetherGuiIsAvailable(cls):
        """Build command to tell whether GUI of GNOME is available.
        
        Should be user to be meaningful.
        
        Command output first word is "available" or with "unavailable".
        
        Return command to tell whether GUI of GNOME is available."""
        command = "if xset -d :0.0 q &> /dev/null ; then echo 'available' ; else echo 'unavailable' ; fi"
        return command

    @classmethod
    def commandToStartApplicationInGui(cls, application):
        """Build command to start application in GNOME.
        
        Must be user to succeed.
        Also, GUI must be available to succeed.
        
        Puts application into background and returns.
        
        application
            e.g. firefox.
        
        Return command to start application in GNOME."""
        command = "export DISPLAY=:0.0 ; nohup " + application + " &> /dev/null &"
        return command

if __name__ == "__main__":
    print Gnome.commandToTellWhetherGuiIsAvailable()
    print Gnome.commandToStartApplicationInGui("gedit")
