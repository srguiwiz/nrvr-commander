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
        Also, GUI must be available to succeed.
        
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
                  r" ; gconftool-2 --set /desktop/gnome/background/color_shading_type --type=string solid" + \
                  r" ; gconftool-2 --set /desktop/gnome/background/primary_color --type=string " + re.escape(color)
        return command

    @classmethod
    def commandToDisableUpdateNotifications(cls):
        """Build command to disable software update notifications of GNOME.
        
        Must be user to succeed.
        
        Return command to disable software update notifications of GNOME."""
        command = r"gconftool-2 --set /apps/gnome-packagekit/update-icon/notify_available --type=bool false" + \
                  r" ; gconftool-2 --set /apps/gnome-packagekit/update-icon/notify_critical --type=bool false" + \
                  r" ; gconftool-2 --set /apps/gnome-packagekit/update-icon/notify_distro_upgrades --type=bool false"
        return command

    @classmethod
    def commandToAddSystemMonitorPanel(cls):
        """Build command to add System Monitor to Panel of GNOME.
        
        Must be user to succeed.
        Also, GUI must be available to succeed.
        
        As implemented doesn't prevent multiple additions.
        
        Return command to add System Monitor to Panel of GNOME."""
        # necessary is
        #   export DISPLAY=:0.0 ; /usr/libexec/gnome-panel-add --applet=OAFIID:GNOME_MultiLoadApplet
        # rest is optional to show all loads, possibly only after logout and login
        command = r"export DISPLAY=:0.0 ; " + \
                  r"/usr/libexec/gnome-panel-add --applet=OAFIID:GNOME_MultiLoadApplet" + \
                  r" && dbuslaunch=`dbus-launch`" + \
                  r" && export DBUS_SESSION_BUS_ADDRESS=`printf \"%s\" \"$dbuslaunch\" | sed -r -n -e 's/^DBUS_SESSION_BUS_ADDRESS=(.*)/\1/p'`" + \
                  r" && export DBUS_SESSION_BUS_PID=`printf \"%s\" \"$dbuslaunch\" | sed -r -n -e 's/^DBUS_SESSION_BUS_PID=(.*)/\1/p'`" + \
                  r" && gconftool-2 --spawn" + \
                  r" && applet=`gconftool-2 --get /apps/panel/general/applet_id_list | sed -r -e 's/^.*,(.+)]$/\1/'`" + \
                  r" && gconftool-2 --set /apps/panel/applets/$applet/prefs/view_cpuload --type=bool true" + \
                  r" && gconftool-2 --set /apps/panel/applets/$applet/prefs/view_memload --type=bool true" + \
                  r" && gconftool-2 --set /apps/panel/applets/$applet/prefs/view_netload --type=bool true" + \
                  r" && gconftool-2 --set /apps/panel/applets/$applet/prefs/view_swapload --type=bool true" + \
                  r" && gconftool-2 --set /apps/panel/applets/$applet/prefs/view_loadavg --type=bool true" + \
                  r" && gconftool-2 --set /apps/panel/applets/$applet/prefs/view_diskload --type=bool true"
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
    print Gnome.commandToDisableUpdateNotifications()
    print Gnome.commandToAddSystemMonitorPanel()
