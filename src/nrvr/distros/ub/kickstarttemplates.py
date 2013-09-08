#!/usr/bin/python

"""nrvr.distros.ub.kickstarttemplates - Templates for creating Ubuntu kickstart files

The main class provided by this module is UbKickstartTemplates.

To be expanded as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

class UbKickstartTemplates(object):
    """Various generally usable templates for Ubuntu."""

    # a kickstart file template known to work well with Ubuntu 12.04
    # for creating generally usable machines
    #
    # see https://help.ubuntu.com/lts/installation-guide/i386/automatic-install.html
    # and https://help.ubuntu.com/community/KickstartCompatibility
    # and http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
    # and http://fedoraproject.org/wiki/Anaconda/Kickstart
    usableKickstartTemplate001 = r"""# A kickstart file made for Ubuntu 12.04 LTS,
# http://releases.ubuntu.com/precise/ubuntu-12.04.2-alternate-i386.iso .
#
# As implemented inlines Ubuntu preseed commands into an Enterprise Linux kind of
# kickstart file.
#
# As implemented may or may not contain redundancies between preseed and kickstart.
#
# Edited manually as needed.
# Could use further automated configuration as needed.
#
# some of this file has been translated from parts of /preseed/cli.seed,
# possibly also from other .seed and .cfg files,
# some answers from https://help.ubuntu.com/12.04/installation-guide/example-preseed.txt,
# per https://help.ubuntu.com/lts/installation-guide/i386/automatic-install.html,
# any "d-i abc/def type value" becomes "preseed abc/def type value", and
# any "other abc/def type value" becomes "preseed --owner other abc/def type value"
#
install
cdrom
lang en_US.UTF-8
keyboard us
mouse
#
# possibly two ways of setting hostname
preseed netcfg/get_hostname string replacethis
preseed netcfg/hostname string replacethis
#
preseed user-setup/allow-password-weak boolean true
#
# Should be set.
rootpw --iscrypted $1$sodiumch$UqZCYecJ/y5M5pp1x.7C4/
#
authconfig --enableshadow --enablemd5
#
# Consider whether it needs to be timezone --utc Etc/UTC
timezone --utc Etc/UTC
#
# Inserted to make it work.
# The parameter "yes" is now deprecated per Enterprise Linux kickstart specification,
# used here because not sure what Ubuntu needs.
zerombr yes
#
bootloader --location=mbr
#
# The following is the partition information you requested.
#
# Uncommented and edited to make it work better.
#
# Ubuntu kickstart apparently can only prepare one hard disk.
# To be exact, it could do RAID over more than one hard disk,
# but no other layout over more than one hard disk.
clearpart --all --initlabel
part /boot --fstype=ext4 --asprimary --size=500
# This swap partition on sda is only a placeholder and in %post we will
# make a larger swap partition of all of sdb to use instead.
part swap --asprimary --size=1
part / --fstype=ext4 --asprimary --size=1000 --grow
#
# Inserted for automation.
# Else kickstart would display a message and wait for user to press a key for rebooting.
#
# Avoid that last message about the install being complete.
preseed finish-install/reboot_in_progress note
# This is how to make the installer shutdown when finished, but not
# reboot into the installed system.
# This will power off the machine instead of just halting it.
preseed debian-installer/exit/poweroff boolean true

#
# Note: Apparently in Ubunutu (at least in 12.04.2 LTS) the %packages section and other sections
# must NOT end with a line %end .
# A show stopping error has been observed in /var/log/syslog during installation,
# reading "Unable to locate package %end".
# This is notably different than a possibly new Enterprise Linux requirement
# "The %packages, %pre, %post and %traceback sections are all required to be closed with %end".
%packages
@server
openssh-server
build-essential

#
# Inserted for automation.
%post
#!/bin/bash
# Note: In Ubunutu this apparently runs in another shell, BusyBox, ash possibly, but not bash.
# User home directories have not been created yet.
# Log is in /var/log/syslog with prefix "in-target:".
# To see log, don't automatically shutdown or reboot.
# Ctrl-Alt-F2 for other console.
# Other console's /target directory is seen by this code as / via chroot.
#
# Allow ssh through firewall.
ufw allow 22/tcp
# Enable firewall.
ufw enable
#
# Make a swap partition of all of sdb.
if ( mkswap /dev/sdb ) ; then
    # Modify /etc/fstab to use /dev/sdb as a swap partition.
    # This will have effect from next booting onwards.
    # Then verifiable by looking at cat /proc/swaps .
    sed -i -e 's/^[^# \t]*\([ \t][ \t]*none[ \t][ \t]*swap[ \t].*\)/\/dev\/sdb\1/' /etc/fstab
fi
#
# Fix up partition options for mount point / in second column by prepending to options in fourth column.
# This will have effect from next booting onwards.
sed -i -e 's/^\([^# \t]*[ \t]*\/[ \t][ \t]*[^ \t]*[ \t]*\)\(.*\)/\1noatime,\2/' /etc/fstab
#
# Prevent Grub's menu from infinitely waiting for user input after problematic shutdown and/or boot.
# see https://help.ubuntu.com/community/Grub2
# see http://askubuntu.com/questions/178091/how-to-disable-grubs-menu-from-showing-up-after-failed-boot
if ( grep -q '^GRUB_RECORDFAIL_TIMEOUT=' /etc/default/grub ) ; then
    # replace
    sed -i -e 's/^GRUB_RECORDFAIL_TIMEOUT=.*/GRUB_RECORDFAIL_TIMEOUT=12/' /etc/default/grub
else
    # append
    echo '' >> /etc/default/grub
    echo '#' >> /etc/default/grub
    echo 'GRUB_RECORDFAIL_TIMEOUT=12' >> /etc/default/grub
fi
#
# Set Grub's menu timeout.
# see https://help.ubuntu.com/community/Grub2
# see http://askubuntu.com/a/106706
# replace
sed -i -e 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=3/' /etc/default/grub
sed -i -e 's/^GRUB_HIDDEN_TIMEOUT=.*/#GRUB_HIDDEN_TIMEOUT=3/' /etc/default/grub
sed -i -e 's/^GRUB_HIDDEN_TIMEOUT_QUIET=.*/#GRUB_HIDDEN_TIMEOUT_QUIET=false/' /etc/default/grub
# necessary
update-grub
"""

    # list of packages and a package group known to work well with Ubuntu 12.04
    # for creating generally usable machines
    packagesForUbuntuDesktop = filter(None, """
@ubuntu-desktop
openssh-server
build-essential
indicator-multiload
""".splitlines())
