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

    # a preseed file template known to work well with Ubuntu 14.04
    # for creating generally usable machines
    usableUbPreseedTemplate001 = r"""# A preseed file made for Ubuntu 14.04 LTS,
# http://releases.ubuntu.com/14.04.1/ubuntu-14.04.1-desktop-amd64.iso .
#
# Edited manually as needed.
# Could use further automated configuration as needed.
#
# some of this file has been taken from parts of /preseed/ubuntu.seed,
# possibly also from other .seed files,
# some answers from https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt,
# per https://help.ubuntu.com/14.04/installation-guide/i386/index.html
# and https://help.ubuntu.com/14.04/installation-guide/i386/apb.html
#
# BEGIN adapted from /preseed/ubuntu.seed
#
# Enable extras.ubuntu.com.
d-i   apt-setup/extras   boolean  true
# Install the Ubuntu desktop.
tasksel   tasksel/first   multiselect   ubuntu-desktop
# On live DVDs, don't spend huge amounts of time removing substantial
# application packages pulled in by language packs. Given that we clearly
# have the space to include them on the DVD, they're useful and we might as
# well keep them installed.
ubiquity   ubiquity/keep-installed   string   icedtea6-plugin openoffice.org
#
# END adapted from /preseed/ubuntu.seed
#
# tell netcfg a specific interface to use instead of looking or asking
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
# END adapted from https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
#
"""
