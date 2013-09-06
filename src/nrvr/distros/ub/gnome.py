#!/usr/bin/python

"""nrvr.distros.ub.gnome - Manipulate Ubuntu GNOME

Class provided by this module is Gnome.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import re

import nrvr.distros.common.gnome

class UbGnome(nrvr.distros.common.gnome.Gnome):
    """Utilities for manipulating a Gnome installation."""

    @classmethod
    def ubCommandToEnableAutoLogin(cls, username=None):
        """Build command to enable auto-login into GNOME.
        
        Must be root to succeed.
        
        username
            defaults to None, which effects disabling auto-login.
        
        Return command to enable auto-login into GNOME."""
        command = UbGnome.ubCommandToDisableAutoLogin()
        if username:
            username = re.escape(username) # precaution
            command += r" ; sed -i -e '/^\[SeatDefaults\]/ a \autologin-user=" + username + r"\nautologin-user-timeout=3' /etc/lightdm/lightdm.conf"
        return command

    @classmethod
    def ubCommandToDisableAutoLogin(cls):
        """Build command to disable auto-login into GNOME.
        
        Must be root to succeed.
        
        Return command to disable auto-login into GNOME."""
        return r"sed -i -e '/^\s*autologin-user\s*=/ d' -e '/^\s*autologin-user-timeout\s*=/ d' /etc/lightdm/lightdm.conf"

    @classmethod
    def ubCommandToDisableScreenSaver(cls):
        """Build command to disable screen saver of GNOME.
        
        Must be user to succeed.
        
        Return command to disable screen saver of GNOME."""
        # see http://askubuntu.com/questions/109120/how-do-i-turn-off-the-screen-saver-using-the-command-line
        # maybe also see http://www.lucidelectricdreams.com/2011/06/disabling-screensaverlock-screen-on.html
        command = "export DISPLAY=:0.0 ; " + \
                  "gsettings set org.gnome.desktop.screensaver lock-enabled false" + \
                  " ; gsettings set org.gnome.desktop.screensaver idle-activation-enabled false"
        return command

    @classmethod
    def ubCommandToEnableScreenSaver(cls):
        """Build command to enable screen saver of GNOME.
        
        Must be user to succeed.
        
        Return command to enable screen saver of GNOME."""
        command = "export DISPLAY=:0.0 ; " + \
                  "gsettings set org.gnome.desktop.screensaver lock-enabled true" + \
                  " ; gsettings set org.gnome.desktop.screensaver idle-activation-enabled true"
        return command

    @classmethod
    def ubCommandToSetSolidColorBackground(cls, color="#2f4f6f"):
        """Build command to set solid color background of GNOME.
        
        Must be user to succeed.
        
        Return command to set solid color background of GNOME."""
        command = "export DISPLAY=:0.0 ; " + \
                  "gsettings set org.gnome.desktop.background picture-options none" + \
                  " ; gsettings set org.gnome.desktop.background color-shading-type solid" + \
                  " ; gsettings set org.gnome.desktop.background primary-color " + re.escape(color)
        return command

if __name__ == "__main__":
    print UbGnome.ubCommandToEnableAutoLogin("joe")
    print UbGnome.ubCommandToDisableAutoLogin()
    print UbGnome.ubCommandToEnableAutoLogin()
    print UbGnome.ubCommandToDisableScreenSaver()
    print UbGnome.ubCommandToEnableScreenSaver()
    print UbGnome.ubCommandToSetSolidColorBackground("#4f6f8f")
    print UbGnome.commandToTellWhetherGuiIsAvailable()
