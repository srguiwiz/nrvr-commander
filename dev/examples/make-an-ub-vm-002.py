#!/usr/bin/python

"""Example use of NrvrCommander.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

import os.path
import shutil
import sys
import tempfile
import time

from nrvr.diskimage.isoimage import IsoImage
from nrvr.distros.common.ssh import LinuxSshCommand
from nrvr.distros.ub.util import UbUtil
from nrvr.distros.ub.rel1204.gnome import Ub1204Gnome
from nrvr.distros.ub.rel1204.kickstart import UbIsoImage, UbKickstartFileContent
from nrvr.distros.ub.rel1204.kickstarttemplates import UbKickstartTemplates
from nrvr.machine.ports import PortsFile
from nrvr.process.commandcapture import CommandCapture
from nrvr.remote.ssh import SshCommand, ScpCommand
from nrvr.util.download import Download
from nrvr.util.ipaddress import IPAddress
from nrvr.util.nameserver import Nameserver
from nrvr.util.requirements import SystemRequirements
from nrvr.util.times import Timestamp
from nrvr.util.user import ScriptUser
from nrvr.vm.vmware import VmdkFile, VmxFile, VMwareHypervisor, VMwareMachine
from nrvr.vm.vmwaretemplates import VMwareTemplates

# this is a good way to preflight check
SystemRequirements.commandsRequiredByImplementations([IsoImage,
                                                      VmdkFile, VMwareHypervisor,
                                                      SshCommand, ScpCommand],
                                                     verbose=True)
# this is a good way to preflight check
VMwareHypervisor.localRequired()

# BEGIN essential example code
ipaddress = "192.168.0.166"
# a possible modification pointed out
# makes sense e.g. if used together with whateverVm.vmxFile.setEthernetAdapter(adapter, "hostonly")
#ipaddress = IPAddress.numberWithinSubnet(VMwareHypervisor.localHostOnlyIPAddress, 166)
rootpw = "redwood"
# Ubuntu kickstart supports only one regular user
regularUser = ("jack","rainbow")
# one possible way of making new VM names and directories
name = IPAddress.nameWithNumber("example", ipaddress, separator=None)
exampleVm = VMwareMachine(ScriptUser.loggedIn.userHomeRelative("vmware/examples/%s/%s.vmx" % (name, name)))
# make the virtual machine
exists = exampleVm.vmxFile.exists()
if exists == False:
    exampleVm.mkdir()
    # several packages installed OK until Ubuntu 12.04.4, but apparently not in Ubuntu 12.04.5
    downloadedDistroIsoImage = UbIsoImage(Download.fromUrl
                                          ("http://releases.ubuntu.com/12.04.4/ubuntu-12.04.4-alternate-i386.iso"))
    # some possible choices pointed out
    # server w command line only
    kickstartFileContent = UbKickstartFileContent(UbKickstartTemplates.usableUbKickstartTemplate001)
    kickstartFileContent.replaceRootpw(rootpw)
    kickstartFileContent.ubReplaceHostname(exampleVm.basenameStem)
    kickstartFileContent.ubCreateNetworkConfigurationSection()
    kickstartFileContent.ubAddNetworkConfigurationStatic(device="eth0", ipaddress=ipaddress, nameservers=Nameserver.list)
    # put in DHCP at eth0, to be used with NAT, works well if before hostonly
    #kickstartFileContent.ubAddNetworkConfigurationDhcp("eth0")
    #kickstartFileContent.ubAddNetworkConfigurationStatic(device="eth1", ipaddress=ipaddress, nameservers=Nameserver.list)
    # some possible modifications pointed out
    #kickstartFileContent.ubSetUpgradeNone()
    #kickstartFileContent.ubSetUpgradeSafe()
    #kickstartFileContent.ubSetUpgradeFull()
    kickstartFileContent.ubSetUpdatePolicyNone()
    # some possible modifications pointed out
    #kickstartFileContent.ubSetUpdatePolicyUnattended()
    # some possible modifications pointed out
    #kickstartFileContent.removePackage("system-config-kickstart")
    #kickstartFileContent.addPackage("httpd")
    # some other possible modifications pointed out
    #kickstartFileContent.replaceAllPackages(UbKickstartTemplates.packagesForUbuntuDesktop)
    #kickstartFileContent.ubActivateGraphicalLogin()
    kickstartFileContent.ubSetUser(regularUser[0], pwd=regularUser[1])
    # some possible modifications pointed out
    #kickstartFileContent.setSwappiness(10)
    # pick right temporary directory, ideally same as VM
    modifiedDistroIsoImage = downloadedDistroIsoImage.cloneWithAutoBootingKickstart \
    (kickstartFileContent,
     cloneIsoImagePath=os.path.join(exampleVm.directory, "made-to-order-os-install.iso"))
    # some necessary choices pointed out
    # 32-bit versus 64-bit linux, memsizeMegabytes needs to be more for 64-bit, guestOS is "ubuntu" versus "ubuntu-64"
    exampleVm.create(memsizeMegabytes=1200, guestOS="ubuntu", ideDrives=[20000, 300, modifiedDistroIsoImage])
    # some possible modifications pointed out
    #exampleVm.vmxFile.setMemorySize(1280)
    #exampleVm.vmxFile.setNumberOfProcessors(2)
    #exampleVm.vmxFile.setAccelerate3D()
    exampleVm.portsFile.setSsh(ipaddress=ipaddress, user="root", pwd=rootpw)
    exampleVm.portsFile.setShutdown()
    exampleVm.portsFile.setSsh(ipaddress=ipaddress, user=regularUser[0], pwd=regularUser[1])
    exampleVm.portsFile.setRegularUser(regularUser[0])
    # some possible modifications pointed out
    #exampleVm.vmxFile.setEthernetAdapter(0, "bridged")
    # NAT works well if before hostonly
    # NAT works well if before hostonly
    #exampleVm.vmxFile.setEthernetAdapter(0, "nat")
    #exampleVm.vmxFile.setEthernetAdapter(1, "hostonly")
    # start up for operating system install
    VMwareHypervisor.local.start(exampleVm.vmxFilePath, gui=True, extraSleepSeconds=0)
    VMwareHypervisor.local.sleepUntilNotRunning(exampleVm.vmxFilePath, ticker=True)
    exampleVm.vmxFile.removeAllIdeCdromImages()
    modifiedDistroIsoImage.remove()

# start up for accepting known host key
VMwareHypervisor.local.start(exampleVm.vmxFilePath, gui=True)
exampleVm.sleepUntilHasAcceptedKnownHostKey(ticker=True)

# a possible choice pointed out
#exampleVm.sshCommand([UbUtil.commandToEnableSudo(exampleVm.regularUser)])

# a possible choice pointed out
#exampleVm.sshCommand([UbUtil.ubCommandToEnableAutoLogin(exampleVm.regularUser)])

# these ssh commands here are just a demo
print "------"
print exampleVm.sshCommand(["ls", "-al"]).output
print "------"
print exampleVm.sshCommand(["ls nonexistent ; echo `hostname`"]).output
print "------"
# these scp commands here are just a demo
exampleDir = os.path.join(tempfile.gettempdir(), Timestamp.microsecondTimestamp())
os.mkdir(exampleDir, 0755)
try:
    sendDir = os.path.join(exampleDir, "send")
    os.mkdir(sendDir, 0755)
    exampleFile1 = os.path.join(sendDir, "example1.txt")
    with open(exampleFile1, "w") as outputFile:
        outputFile.write("this is an example\n" * 1000000)
    scpExample1 = exampleVm.scpPutCommand(fromHostPath=exampleFile1, toGuestPath="~/example1.txt")
    print "returncode=" + str(scpExample1.returncode)
    print "output=" + scpExample1.output
    scpExample2 = exampleVm.scpGetCommand(fromGuestPath="/etc/hosts", toHostPath=exampleFile1)
    print "returncode=" + str(scpExample2.returncode)
    print "output=" + scpExample2.output
    with open(exampleFile1, "r") as inputFile:
        exampleFile1Content = inputFile.read()
    print "content=\n" + exampleFile1Content
finally:
    shutil.rmtree(exampleDir)

# a good way to shut down the virtual machine,
# wait longer because apparently Ubuntu (with GUI) the first time does something important that must be
# allowed to finish before shutdown, lest the machine could be in an unusable state
exampleVm.shutdownCommand(extraSleepSeconds=60)
VMwareHypervisor.local.sleepUntilNotRunning(exampleVm.vmxFilePath, ticker=True)

# a possible modification pointed out
# start up again so it is running for use
#VMwareHypervisor.local.start(exampleVm.vmxFilePath, gui=True, extraSleepSeconds=0)
#exampleVm.sleepUntilSshIsAvailable(ticker=True)

# a possible modification pointed out
# start up for showing successful login into GUI
#VMwareHypervisor.local.start(exampleVm.vmxFilePath, gui=True, extraSleepSeconds=0)
#regularUserSshParameters = exampleVm.sshParameters(user=exampleVm.regularUser)
#LinuxSshCommand.sleepUntilIsGuiAvailable(regularUserSshParameters, ticker=True)

# a possible modification pointed out
# just a demo
#regularUserSshParameters = exampleVm.sshParameters(user=exampleVm.regularUser)
#SshCommand(regularUserSshParameters, [Ub1204Gnome.commandToStartApplicationInGui("firefox about:blank")])

# possible modifications pointed out
# start up until successful login into GUI
#VMwareHypervisor.local.start(exampleVm.vmxFilePath, gui=True, extraSleepSeconds=0)
#regularUserSshParameters = exampleVm.sshParameters(user=exampleVm.regularUser)
#LinuxSshCommand.sleepUntilIsGuiAvailable(regularUserSshParameters, ticker=True)
# some possible choices pointed out
#exampleVm.sshCommand([Ub1204Gnome.ubCommandToDisableScreenSaver()], user=exampleVm.regularUser)
#exampleVm.sshCommand([Ub1204Gnome.ubCommandToSetSolidColorBackground()], user=exampleVm.regularUser)
#exampleVm.sshCommand([Ub1204Gnome.ubCommandToAddSystemMonitorPanel()], user=exampleVm.regularUser)
#exampleVm.shutdownCommand()
#VMwareHypervisor.local.sleepUntilNotRunning(exampleVm.vmxFilePath, ticker=True)

#
print "%s is done with %s, it is ready for you to use at %s" % \
(__file__, exampleVm.basenameStem, exampleVm.portsFile.getPorts(protocol="ssh", user="root")[0]["ipaddress"])
# END essential example code
