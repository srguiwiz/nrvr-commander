#!/usr/bin/python

"""nrvr.vm.vmwaretemplates - Templates for creating VMware virtual machines

The main class provided by this module is VMwareTemplates.

To be expanded as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

class VMwareTemplates(object):
    """Various generally usable templates."""

    # a .vmx file template known to work well with VMware Workstation 8.0 to 10.0 and VMware Player 4.0 to 6.0
    # for creating generally usable virtual machines
    usableVMwareVmxTemplate001 = """#!/usr/bin/vmware
.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "8"

memsize = "480" # megabytes, must be multiple of 4

guestOS = "centos" # e.g. centos

displayName = "_DISPLAY_NAME_"

# see http://sanbarrow.com/vmx/vmx-network.html
ethernet0.present = "TRUE"
ethernet0.startConnected = "TRUE"
ethernet0.virtualDev="e1000"
ethernet0.connectionType="bridged" # one of bridged, nat, hostonly, custom
# see http://sanbarrow.com/vmx/vmx-network-advanced.html
#ethernet0.addressType = "static" # one of generated, static, if not given then will be generated
#ethernet0.address = "00:50:56:00:00:00" # valid 00:50:56:00:00:00 to 00:50:56:3f:ff:ff
ethernet0.wakeOnPcktRcv = "FALSE" # if off less trouble
ethernet0.allowGuestConnectionControl = "FALSE" # if off then safer
ethernet0.disableMorphToVmxnet = "TRUE" # if off then less surprises

svga.autodetect = "FALSE" # means only one screen in VM
svga.vramSize = "16384000" # 16384000 apparently allows up to 2560x1600

usb.present = "TRUE" # enable USB 1.1
ehci.present = "TRUE" # enable USB 2.0

sound.present = "FALSE" # if off less trouble

floppy0.present = "FALSE" # not needed any more

serial0.present = "FALSE" # if off less trouble

vmci0.present = "FALSE" # if off less trouble, why allow guest to know host?

# generally more info at http://sanbarrow.com/vmx.html
# some specific info at http://sanbarrow.com/vmx/vmx-advanced.html

tools.upgrade.policy = "manual" # manual means less trouble
tools.remindInstall = "FALSE" # less distractions or interruptions

snapshot.action = "keep" # one of keep, autoRevert, autoCommit, prompt, maybe only works from GUI

msg.autoAnswer = "TRUE" # supposedly tries to automatically answer all questions when booting
"""
