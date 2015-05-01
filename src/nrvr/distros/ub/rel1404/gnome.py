#!/usr/bin/python

"""nrvr.distros.ub.rel1404.gnome - Manipulate Ubuntu 12.04 GNOME

Class provided by this module is Gnome.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

import re

import nrvr.distros.common.gnome

class Ub1404Gnome(nrvr.distros.common.gnome.Gnome):
    """Utilities for manipulating a Gnome installation."""

    @classmethod
    def ubCommandToLimitCompizGpuUse(cls):
        """Build command to limit Compiz GPU use.
        
        Must be root to succeed.
        
        Return command to limit Compiz GPU user."""
        # see https://bugs.launchpad.net/compiz/+bug/1293384
        # note: the export never executes when /usr/share/gnome-session/sessions/ubuntu.session
        # still in line RequiredComponents has compiz
        # hence consider this an experimental stub to be improved upon
        return r"sed -i -e '/^export\s*COMPIZ_CONFIG_PROFILE/a #\nenv UNITY_LOW_GFX_MODE=\"1\"\nexport UNITY_LOW_GFX_MODE'" + \
               r" /usr/share/upstart/sessions/unity7.conf"

    @classmethod
    def ubCommandToDisableScreenSaver(cls):
        """Build command to disable screen saver of GNOME.
        
        Must be user to succeed.
        Also, GUI must be available to succeed.
        
        Return command to disable screen saver of GNOME."""
        # see http://askubuntu.com/questions/109120/how-do-i-turn-off-the-screen-saver-using-the-command-line
        # maybe also see http://www.lucidelectricdreams.com/2011/06/disabling-screensaverlock-screen-on.html
        command = r"dbus-launch --exit-with-session gsettings set org.gnome.desktop.screensaver lock-enabled false ; " + \
                  r"dbus-launch --exit-with-session gsettings set org.gnome.desktop.screensaver idle-activation-enabled false ; " + \
                  r"dbus-launch --exit-with-session gsettings set org.gnome.desktop.session idle-delay 0"
        return command

    @classmethod
    def ubCommandToEnableScreenSaver(cls, idleDelaySeconds=300):
        """Build command to enable screen saver of GNOME.
        
        Must be user to succeed.
        Also, GUI must be available to succeed.
        
        Return command to enable screen saver of GNOME."""
        command = r"dbus-launch --exit-with-session gsettings set org.gnome.desktop.screensaver lock-enabled true ; " + \
                  r"dbus-launch --exit-with-session gsettings set org.gnome.desktop.screensaver idle-activation-enabled true ; " + \
                  r"dbus-launch --exit-with-session gsettings set org.gnome.desktop.session idle-delay " + str(idleDelaySeconds)
        return command

    @classmethod
    def ubCommandToSetSolidColorBackground(cls, color="#2f4f6f"):
        """Build command to set solid color background of GNOME.
        
        Must be user to succeed.
        Also, GUI must be available to succeed.
        
        Return command to set solid color background of GNOME."""
        command = r"dbus-launch --exit-with-session gsettings set org.gnome.desktop.background picture-options none ; " + \
                  r"dbus-launch --exit-with-session gsettings set org.gnome.desktop.background color-shading-type solid ; " + \
                  r"dbus-launch --exit-with-session gsettings set org.gnome.desktop.background primary-color " + re.escape(color)
        return command

    @classmethod
    def ubCommandToInstallSystemMonitorPanel(cls):
        """Build command to install System Load Indicator for Panel of GNOME.
        
        Must be root to succeed.
        Then, as user must invoke ubCommandToAddSystemMonitorPanel().
        
        Return command to install System Load Indicator for Panel of GNOME."""
        command = "apt-get -y install indicator-multiload"
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
                  r"if which indicator-multiload &> /dev/null ; then " + \
                  r"mkdir -p ~/.config/autostart ; " + \
                  r"gsettings set de.mh21.indicator.multiload.general autostart true ; " + \
                  r"( nohup indicator-multiload &> /dev/null & ) ; " + \
                  r"while [ ! -f ~/.config/autostart/indicator-multiload* ] ; do sleep 1 ; done ; " + \
                  r"( if pidofim=`pidof indicator-multiload` ; then /bin/kill $pidofim ; fi ) ; " + \
                  r"( while pidof indicator-multiload ; do sleep 1 ; done ) ; " + \
                  r"gsettings set de.mh21.indicator.multiload.general autostart true ; " + \
                  r"gsettings set de.mh21.indicator.multiload.graphs.cpu enabled true ; " + \
                  r"gsettings set de.mh21.indicator.multiload.graphs.mem enabled true ; " + \
                  r"gsettings set de.mh21.indicator.multiload.graphs.net enabled true ; " + \
                  r"gsettings set de.mh21.indicator.multiload.graphs.swap enabled true ; " + \
                  r"gsettings set de.mh21.indicator.multiload.graphs.load enabled true ; " + \
                  r"gsettings set de.mh21.indicator.multiload.graphs.disk enabled true ; " + \
                  r"gsettings set de.mh21.indicator.multiload.general speed 2000 ; " + \
                  r"fi"
        return command

if __name__ == "__main__":
    print Ub1404Gnome.ubCommandToDisableScreenSaver()
    print Ub1404Gnome.ubCommandToEnableScreenSaver()
    print Ub1404Gnome.ubCommandToSetSolidColorBackground("#4f6f8f")
    print Ub1404Gnome.commandToTellWhetherGuiIsAvailable()
    print Ub1404Gnome.ubCommandToAddSystemMonitorPanel()
