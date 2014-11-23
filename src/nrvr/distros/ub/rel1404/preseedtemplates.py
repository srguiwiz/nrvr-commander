#!/usr/bin/python

"""nrvr.distros.ub.rel1404.preseedtemplates - Templates for creating Ubuntu preseed files

The main class provided by this module is UbPreseedTemplates.

To be expanded as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

class UbPreseedTemplates(object):
    """Generally usable templates for Ubuntu."""

    # a preseed file template known to work well with Ubuntu 14.04 LTS
    # for creating generally usable machines with GUI (aka desktop)
    usableUbWithGuiPreseedTemplate001 = r"""# A preseed file made for Ubuntu 14.04 LTS,
# http://releases.ubuntu.com/14.04.1/ubuntu-14.04.1-desktop-amd64.iso .
#
# Edited manually as needed.
# Could use further automated configuration as needed.
#
# Some of this file has been taken from parts of /preseed/ubuntu.seed,
# possibly also from other .seed files,
# some answers from https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt ,
# per https://help.ubuntu.com/14.04/installation-guide/i386/index.html
# and https://help.ubuntu.com/14.04/installation-guide/i386/apb.html
#
# BEGIN adapted from /preseed/ubuntu.seed
#
# Enable extras.ubuntu.com.
d-i   apt-setup/extras   boolean  true
# On live DVDs, don't spend huge amounts of time removing substantial
# application packages pulled in by language packs. Given that we clearly
# have the space to include them on the DVD, they're useful and we might as
# well keep them installed.
ubiquity   ubiquity/keep-installed   string   icedtea6-plugin openoffice.org
#
# END adapted from /preseed/ubuntu.seed
#
# Tell netcfg a specific interface to use instead of looking or asking.
# Note: Possibly key netcfg/ is not used by Ubiquity, see https://wiki.ubuntu.com/UbiquityAutomation .
d-i   netcfg/choose_interface   select   eth0
#
# BEGIN adapted from https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
#
# Preseeding only locale sets language, country and locale.
d-i   debian-installer/locale   string   en_US.UTF-8
#
# Keyboard selection.
# Disable automatic (interactive) keymap detection.
d-i   console-setup/ask_detect   boolean   false
d-i   keyboard-configuration/layoutcode   string   us
#
# If you have a slow dhcp server and the installer times out waiting for
# it, this might be useful.
#d-i   netcfg/dhcp_timeout   string   60
#
# Any hostname and domain names assigned from dhcp take precedence over
# values set here. However, setting the values still prevents the questions
# from being shown, even if values come from dhcp.
d-i   netcfg/get_hostname   string   replacethis
#
# Controls whether or not the hardware clock is set to UTC.
d-i   clock-setup/utc   boolean   true
#
# You may set this to any valid setting for $TZ; see the contents of
# /usr/share/zoneinfo/ for valid values.
d-i   time/zone   string   Etc/UTC
#
# Controls whether to use NTP to set the clock during the install
d-i   clock-setup/ntp   boolean   true
#
# You may specify a disk to partition. If the system has only
# one disk the installer will default to using that, but otherwise the device
# name must be given in traditional, non-devfs format (so e.g. /dev/hda or
# /dev/sda, and not e.g. /dev/discs/disc0/disc).
# For example, to use the first SCSI/SATA hard disk:
d-i   partman-auto/disk   string   /dev/sda
#
# In addition, you'll need to specify the method to use.
# The presently available methods are:
# - regular: use the usual partition types for your architecture
# - lvm:     use LVM to partition the disk
# - crypto:  use LVM within an encrypted partition
d-i   partman-auto/method   string   regular
#
# You can choose one of the three predefined partitioning recipes:
# - atomic: all files in one partition
# - home:   separate /home partition
# - multi:  separate /home, /usr, /var, and /tmp partitions
d-i   partman-auto/choose_recipe   select   atomic
#
# If you just want to change the default filesystem from ext3 to something
# else, you can do that without providing a full recipe.
d-i   partman/default_filesystem   string   ext4
#
# This makes partman automatically partition without confirmation, provided
# that you told it what to do using one of the methods above.
d-i   partman-partitioning/confirm_write_new_label   boolean   true
d-i   partman/choose_partition   select   finish
d-i   partman/confirm   boolean   true
d-i   partman/confirm_nooverwrite   boolean   true
#
# Skip creation of a root account (normal user account will be able to
# use sudo). The default is false; preseed this to true if you want to set
# a root password.
d-i   passwd/root-login   boolean   true
# Alternatively, to skip creation of a normal user account.
#d-i passwd/make-user boolean false
#
# Root password, either in clear text
#d-i   passwd/root-password   password   r00tme
#d-i   passwd/root-password-again   password   r00tme
# or encrypted using an MD5 hash.
d-i   passwd/root-password-crypted   password   $1$sodiumch$UqZCYecJ/y5M5pp1x.7C4/
#
# To create a normal user account.
d-i   passwd/user-fullname   string   Full Name
d-i   passwd/username   string   name
# Normal user's password, either in clear text
# or encrypted using an MD5 hash.
d-i   passwd/user-password-crypted   password   $1$sodiumch$UqZCYecJ/y5M5pp1x.7C4/
# The installer will warn about weak passwords. If you are sure you know
# what you're doing and want to override it, use this.
d-i   user-setup/allow-password-weak   boolean   true
#
# The user account will be added to some standard initial groups. To
# override that, use this.
#d-i   passwd/user-default-groups   string   audio cdrom video
#
# Set to true if you want to encrypt the first user's home directory.
d-i   user-setup/encrypt-home   boolean   false
#
### Package selection
# Install the Ubuntu desktop.
# Note: Possibly key tasksel/ is not used by Ubiquity, see https://wiki.ubuntu.com/UbiquityAutomation .
tasksel   tasksel/first   multiselect   ubuntu-desktop
#
# Individual additional packages to install
# Note: Apparently key pkgsel/include is not used by Ubiquity, see https://wiki.ubuntu.com/UbiquityAutomation .
d-i   pkgsel/include   string   openssh-server build-essential
#
# Whether to upgrade packages after debootstrap.
# Allowed values: none, safe-upgrade, full-upgrade
d-i   pkgsel/upgrade   select   none
#
# Language pack selection
#d-i   pkgsel/language-packs   multiselect   en, de, zh
#
# Policy for applying updates. May be "none" (no automatic updates),
# "unattended-upgrades" (install security updates automatically), or
# "landscape" (manage system with Landscape).
d-i   pkgsel/update-policy   select   none
#
# By default, the system's locate database will be updated after the
# installer has finished installing most packages. This may take a while, so
# if you don't want it, you can set this to "false" to turn it off.
d-i   pkgsel/updatedb   boolean   true
#
# Avoid that last message about the install being complete.
# Note: Apparently key finish-install/ is not used by Ubiquity, see https://wiki.ubuntu.com/UbiquityAutomation .
#d-i   finish-install/reboot_in_progress   note
#
# This is how to make the installer shutdown when finished, but not
# reboot into the installed system.
#d-i   debian-installer/exit/halt   boolean   true
# This will power off the machine instead of just halting it.
#d-i   debian-installer/exit/poweroff   boolean   true
#
# ubiquity/reboot per https://wiki.ubuntu.com/UbiquityAutomation
ubiquity   ubiquity/reboot   boolean   false
# ubiquity/poweroff per http://askubuntu.com/questions/478227/how-to-auto-poweroff-after-ubiquity-preseed-install-of-ubuntu-desktop
ubiquity   ubiquity/poweroff   boolean   true
#
# This command is run just before the install finishes, but when there is
# still a usable /target directory. You can chroot to /target and use it
# directly, or use the apt-install and in-target commands to easily install
# packages and run commands in the target system.
#d-i   preseed/late_command   string   in-target echo "`whoami`" > /washere.txt
#
# Per http://askubuntu.com/questions/104135/preseed-late-command-not-running
# with Ubiquity don't use d-i preseed/late_command string your command, but instead use
# ubiquity   ubiquity/success_command   string   your command
# e.g.
# ubiquity   ubiquity/success_command   string   echo "`whoami`" > /target/washere.txt
# shows success_command runs as root.
# Must remain here at least as stub for other code to append to.
# Cannot use \n because ubiquity installer echo apparently doesn't take option -e .
# Set DEBIAN_FRONTEND=noninteractive per http://snowulf.com/2008/12/04/truly-non-interactive-unattended-apt-get-install/ .
# Do what Ubiquity apparently doesn't do for pkgsel/include.
# Do what Ubiquity apparently doesn't do for ufw.
# Make a swap partition of all of sdb.
# Fix up partition options.
ubiquity   ubiquity/success_command   string   \
  export DEBIAN_FRONTEND=noninteractive ; \
  in-target apt-get -y install openssh-server build-essential ; \
  sed -i -e 's/^\s*PermitRootLogin/#PermitRootLogin/' -e '/#\s*PermitRootLogin/ a \PermitRootLogin yes' /target/etc/ssh/sshd_config ; \
  if ! grep -q '^\s*PermitRootLogin' /target/etc/ssh/sshd_config ; then sed -i -e '$ a \PermitRootLogin yes' /target/etc/ssh/sshd_config ; fi ; \
  cp /cdrom/preseed/first-time-start /target/etc/init.d/ ; \
  chmod 755 /target/etc/init.d/first-time-start ; \
  in-target update-rc.d first-time-start defaults 99 01
#
# END adapted from https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
#
# Firewall preseeding mentioned at /usr/share/doc/ufw/README.Debian .
# Note: Apparently ufw is ignored by Ubiquity.
#ufw   ufw/enable   boolean   true
#ufw   ufw/allow_known_ports   multiselect   SSH
"""

    # a script for use with usableUbWithGuiPreseedTemplate001
    # put into a separate constant string in order to avoid too much escaping,
    # specifically there might be undocumented escaping done of ubiquity/success_command,
    # trying to avoid having unreadable code
    usableUbWithGuiPreseedFirstTimeStartScript001 = r"""#!/bin/bash
#
# make sure runs only once ever
update-rc.d -f first-time-start remove
#
# enable ufw and allow ssh
ufw allow ssh
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
