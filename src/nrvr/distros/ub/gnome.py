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
        # see http://www.tuxgarage.com/2011/09/setting-lightdm-to-auto-login-oneiric.html
        command = UbGnome.ubCommandToDisableAutoLogin()
        if username:
            username = re.escape(username) # precaution
            # autologin-user-timeout=0 to avoid https://bugs.launchpad.net/ubuntu/+source/lightdm/+bug/902852
            command += r" ; sed -i -e '/^\[SeatDefaults\]/ a \autologin-user=" + username + r"\nautologin-user-timeout=0' /etc/lightdm/lightdm.conf"
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
        Also, GUI must be available to succeed.
        
        Return command to disable screen saver of GNOME."""
        # see http://askubuntu.com/questions/109120/how-do-i-turn-off-the-screen-saver-using-the-command-line
        # maybe also see http://www.lucidelectricdreams.com/2011/06/disabling-screensaverlock-screen-on.html
        command = cls.exportDisplay + \
                  r" ; gsettings set org.gnome.desktop.screensaver lock-enabled false" + \
                  r" ; gsettings set org.gnome.desktop.screensaver idle-activation-enabled false"
        return command

    @classmethod
    def ubCommandToEnableScreenSaver(cls):
        """Build command to enable screen saver of GNOME.
        
        Must be user to succeed.
        Also, GUI must be available to succeed.
        
        Return command to enable screen saver of GNOME."""
        command = cls.exportDisplay + \
                  r" ; gsettings set org.gnome.desktop.screensaver lock-enabled true" + \
                  r" ; gsettings set org.gnome.desktop.screensaver idle-activation-enabled true"
        return command

    @classmethod
    def ubCommandToSetSolidColorBackground(cls, color="#2f4f6f"):
        """Build command to set solid color background of GNOME.
        
        Must be user to succeed.
        Also, GUI must be available to succeed.
        
        Return command to set solid color background of GNOME."""
        command = cls.exportDisplay + \
                  r" ; gsettings set org.gnome.desktop.background picture-options none" + \
                  r" ; gsettings set org.gnome.desktop.background color-shading-type solid" + \
                  r" ; gsettings set org.gnome.desktop.background primary-color " + re.escape(color)
        return command

    @classmethod
    def ubCommandToAddSystemMonitorPanel(cls):
        """Build command to add System Load Indicator to Panel of GNOME.
        
        Must be user to succeed.
        Also, GUI must be available to succeed.
        
        As implemented doesn't prevent multiple additions.
        
        Return command to add System Load Indicator to Panel of GNOME."""
        # see https://bugs.launchpad.net/indicator-multiload/+bug/836893
        # see https://bugs.launchpad.net/indicator-multiload/+bug/942859
        # see https://bugs.launchpad.net/indicator-multiload/+bug/962646
        # essential is
        #   nohup indicator-multiload &> /dev/null &
        # export and mkdir are necessities,
        # gsettings- view are optional to show all loads, possibly only after logout and login
        command = cls.exportDD + \
                  r" ; export XDG_DATA_DIRS='/usr/share/gnome:/usr/local/share/:/usr/share/' ; " + \
                  r"mkdir -p ~/.config/autostart ; " + \
                  r"gsettings set de.mh21.indicator.multiload autostart true ; " + \
                  r"( nohup indicator-multiload &> /dev/null & ) ; " + \
                  r"while [ ! -f ~/.config/autostart/indicator-multiload* ] ; do sleep 1 ; done ; " + \
                  r"( if pidofim=`pidof indicator-multiload` ; then /bin/kill $pidofim ; fi ) ; " + \
                  r"( while pidof indicator-multiload ; do sleep 1 ; done ) ; " + \
                  r"gsettings set de.mh21.indicator.multiload autostart true ; " + \
                  r"gsettings set de.mh21.indicator.multiload view-cpuload true ; " + \
                  r"gsettings set de.mh21.indicator.multiload view-memload true ; " + \
                  r"gsettings set de.mh21.indicator.multiload view-netload true ; " + \
                  r"gsettings set de.mh21.indicator.multiload view-swapload true ; " + \
                  r"gsettings set de.mh21.indicator.multiload view-loadavg true ; " + \
                  r"gsettings set de.mh21.indicator.multiload view-diskload true ; " + \
                  r"gsettings set de.mh21.indicator.multiload speed 2000"
        return command

if __name__ == "__main__":
    print UbGnome.ubCommandToEnableAutoLogin("joe")
    print UbGnome.ubCommandToDisableAutoLogin()
    print UbGnome.ubCommandToEnableAutoLogin()
    print UbGnome.ubCommandToDisableScreenSaver()
    print UbGnome.ubCommandToEnableScreenSaver()
    print UbGnome.ubCommandToSetSolidColorBackground("#4f6f8f")
    print UbGnome.commandToTellWhetherGuiIsAvailable()
    print UbGnome.ubCommandToAddSystemMonitorPanel()
