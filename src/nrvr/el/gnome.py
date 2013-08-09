#!/usr/bin/python

"""nrvr.el.gnome - Manipulate Enterprise Linux GNOME

Class provided by this module is Gnome.

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
        command = Gnome.commandToDisableAutoLogin()
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
        command = "gconftool-2 --set /apps/gnome-screensaver/idle_activation_enabled --type=bool false"
        return command

    @classmethod
    def commandToEnableScreenSaver(cls):
        """Build command to enable screen saver of GNOME.
        
        Must be user to succeed.
        
        Return command to enable screen saver of GNOME."""
        command = "gconftool-2 --set /apps/gnome-screensaver/idle_activation_enabled --type=bool true"
        return command

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
        
        Puts application into background and returns.
        
        application
            e.g. firefox.
        
        Return command to start application in GNOME."""
        command = "export DISPLAY=:0.0 ; nohup " + application + " &> /dev/null &"
        return command

    @classmethod
    def commandToSetSolidColorBackground(cls, color="#2f4f6f"):
        """Build command to set solid color background of GNOME.
        
        Must be user to succeed.
        
        Return command to set solid color background of GNOME."""
        command = r"gconftool-2 --set /desktop/gnome/background/picture_options --type=string none" + \
                  r" && gconftool-2 --set /desktop/gnome/background/color_shading_type --type=string solid" + \
                  r" && gconftool-2 --set /desktop/gnome/background/primary_color --type=string " + re.escape(color)
        return command

if __name__ == "__main__":
    print Gnome.commandToEnableAutoLogin("joe")
    print Gnome.commandToDisableAutoLogin()
    print Gnome.commandToEnableAutoLogin()
    print Gnome.commandToDisableScreenSaver()
    print Gnome.commandToEnableScreenSaver()
    print Gnome.commandToTellWhetherGuiIsAvailable()
    print Gnome.commandToStartApplicationInGui("gedit")
    print Gnome.commandToSetSolidColorBackground("#4f6f8f")
