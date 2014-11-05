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
from nrvr.distros.common.util import LinuxUtil
from nrvr.distros.el.gnome import ElGnome
from nrvr.distros.el.kickstart import ElIsoImage, ElKickstartFileContent
from nrvr.distros.el.kickstarttemplates import ElKickstartTemplates
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
ipaddress = "192.168.0.161"
# a possible modification pointed out
# makes sense e.g. if used together with whateverVm.vmxFile.setEthernetAdapter(adapter, "hostonly")
#ipaddress = IPAddress.numberWithinSubnet(VMwareHypervisor.localHostOnlyIPAddress, 161)
rootpw = "redwood"
additionalUsers = []
# some possible choices pointed out
#additionalUsers [("jack","rainbow"),("jill","sunshine")]
# one possible way of making new VM names and directories
name = IPAddress.nameWithNumber("example", ipaddress, separator=None)
exampleVm = VMwareMachine(ScriptUser.loggedIn.userHomeRelative("vmware/examples/%s/%s.vmx" % (name, name)))
# make the virtual machine
exists = exampleVm.vmxFile.exists()
if exists == False:
    exampleVm.mkdir()
    #
    # comment solely regarding .iso files larger than 4GB, e.g. x86_64 Install-DVD,
    # there had been issues that almost have gone away with a fixed newer version iso-read,
    # there is a fix in libcdio (which provides iso-read) 0.92,
    # the remaining issue is you need to make sure you have libcdio 0.92 installed
    #
    #downloadedDistroIsoImage = ElIsoImage(ScriptUser.loggedIn.userHomeRelative \
    #                                      ("Downloads/CentOS-6.6-i386-bin-DVD1.iso"))
    downloadedDistroIsoImage = ElIsoImage(Download.fromUrl
                                          ("http://mirrors.usc.edu/pub/linux/distributions/centos/6.6/isos/i386/CentOS-6.6-i386-bin-DVD1.iso"))
    # some possible choices pointed out
    # server w command line only
    kickstartFileContent = ElKickstartFileContent(ElKickstartTemplates.usableElKickstartTemplate001)
    kickstartFileContent.replaceRootpw(rootpw)
    kickstartFileContent.elReplaceHostname(exampleVm.basenameStem)
    kickstartFileContent.elReplaceStaticIP(ipaddress, nameservers=Nameserver.list)
    # put in DHCP at eth0, to be used with NAT, works well if before hostonly
    #kickstartFileContent.elReplaceStaticIP(ipaddress, nameservers=[])
    #kickstartFileContent.elAddNetworkConfigurationWithDhcp("eth0")
    # some possible modifications pointed out
    #kickstartFileContent.replaceAllPackages(ElKickstartTemplates.packagesOfSL64Minimal)
    #kickstartFileContent.removePackage("@office-suite")
    #kickstartFileContent.addPackage("httpd")
    # some other possible modifications pointed out
    #kickstartFileContent.replaceAllPackages(ElKickstartTemplates.packagesOfSL64MinimalDesktop)
    #kickstartFileContent.elActivateGraphicalLogin()
    for additionalUser in additionalUsers:
        kickstartFileContent.elAddUser(additionalUser[0], pwd=additionalUser[1])
    # some possible modifications pointed out
    #kickstartFileContent.setSwappiness(10)
    # pick right temporary directory, ideally same as VM
    modifiedDistroIsoImage = downloadedDistroIsoImage.cloneWithAutoBootingKickstart \
    (kickstartFileContent,
     cloneIsoImagePath=os.path.join(exampleVm.directory, "made-to-order-os-install.iso"))
    # some necessary choices pointed out
    # 32-bit versus 64-bit linux, memsizeMegabytes needs to be more for 64-bit, guestOS is "centos" versus "centos-64"
    exampleVm.create(memsizeMegabytes=1200, guestOS="centos", ideDrives=[20000, 300, modifiedDistroIsoImage])
    # some possible modifications pointed out
    #exampleVm.vmxFile.setMemorySize(1280)
    #exampleVm.vmxFile.setNumberOfProcessors(2)
    #exampleVm.vmxFile.setAccelerate3D()
    exampleVm.portsFile.setSsh(ipaddress=ipaddress, user="root", pwd=rootpw)
    exampleVm.portsFile.setShutdown()
    for additionalUser in additionalUsers:
        exampleVm.portsFile.setSsh(ipaddress=ipaddress, user=additionalUser[0], pwd=additionalUser[1])
    if additionalUsers:
        exampleVm.portsFile.setRegularUser(additionalUsers[0][0])
    # some possible modifications pointed out
    #exampleVm.vmxFile.setEthernetAdapter(0, "bridged")
    # NAT works well if before hostonly
    #exampleVm.vmxFile.setEthernetAdapter(0, "nat")
    #exampleVm.vmxFile.setEthernetAdapter(1, "hostonly")
    # start up for operating system install
    VMwareHypervisor.local.start(exampleVm.vmxFilePath, gui=True, extraSleepSeconds=0)
    VMwareHypervisor.local.sleepUntilNotRunning(exampleVm.vmxFilePath, ticker=True)
    exampleVm.vmxFile.removeAllIdeCdromImages()
    modifiedDistroIsoImage.remove()

# start up for accepting known host key
VMwareHypervisor.local.start(exampleVm.vmxFilePath, gui=True, extraSleepSeconds=0)
exampleVm.sleepUntilHasAcceptedKnownHostKey(ticker=True)

# a possible choice pointed out
#if exampleVm.regularUser:
#    exampleVm.sshCommand([LinuxUtil.commandToEnableSudo(exampleVm.regularUser)])

# some possible choices pointed out
#if exampleVm.regularUser:
#    exampleVm.sshCommand([ElGnome.elCommandToEnableAutoLogin(exampleVm.regularUser)])
#    exampleVm.sshCommand([ElGnome.elCommandToDisableScreenSaver()], user=exampleVm.regularUser)
#    exampleVm.sshCommand([ElGnome.elCommandToSetSolidColorBackground()], user=exampleVm.regularUser)
#    exampleVm.sshCommand([ElGnome.elCommandToDisableUpdateNotifications()], user=exampleVm.regularUser)

# a possible modification pointed out
# append an ipaddress hostname line to /etc/hosts for a smooth automated install of something
# only if no line yet
#print exampleVm.sshCommand(["fgrep -q -e '" + name + "' /etc/hosts || " + 
#                       "echo " + "'" + ipaddress + " " + name + "'" + " >> /etc/hosts"]).output

# a possible modification pointed out
# open firewall port 80 for httpd
# only if no line yet
#print exampleVm.sshCommand(["fgrep -q -e '--dport 80 ' /etc/sysconfig/iptables || " + 
#                       "sed -i -e '/--dport 22 / p' -e 's/--dport 22 /--dport 80 /' /etc/sysconfig/iptables"]).output
# restart firewall
#print exampleVm.sshCommand(["service iptables restart"]).output

# a possible modification pointed out
# copy over some custom installer
#customInstaller = "custom-1.2.3-installer-linux.bin"
#downloadedCustomInstaller = ScriptUser.loggedIn.userHomeRelative(os.path.join("Downloads", customInstaller))
#guestDownloadsDirectory = "/root/Downloads"
#exampleVm.sshCommand(["mkdir -p " + guestDownloadsDirectory])
#guestDownloadedCustomInstaller = os.path.join(guestDownloadsDirectory, customInstaller)
#exampleVm.scpPutCommand(downloadedCustomInstaller, guestDownloadedCustomInstaller)

# a possible modification pointed out
#customInstallPwd = "oakwood"
# install custom software
#print exampleVm.sshCommand([guestDownloadedCustomInstaller + 
#                       " --mode unattended" + 
#                       " --install_password '" + customInstallPwd + "'"]).output

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

# a good way to shut down the virtual machine
exampleVm.shutdownCommand()
VMwareHypervisor.local.sleepUntilNotRunning(exampleVm.vmxFilePath, ticker=True)

# a possible modification pointed out
# start up again so it is running for use
#VMwareHypervisor.local.start(exampleVm.vmxFilePath, gui=True, extraSleepSeconds=0)
#exampleVm.sleepUntilSshIsAvailable(ticker=True)

# a possible modification pointed out
# start up for showing successful login into GUI
#VMwareHypervisor.local.start(exampleVm.vmxFilePath, gui=True, extraSleepSeconds=0)
#exampleSshParameters = exampleVm.sshParameters(user=exampleVm.regularUser)
#LinuxSshCommand.sleepUntilIsGuiAvailable(exampleSshParameters, ticker=True)

# a possible modification pointed out
# just a demo
#exampleSshParameters = exampleVm.sshParameters(user=exampleVm.regularUser)
#SshCommand(exampleSshParameters, [ElGnome.commandToStartApplicationInGui("firefox about:blank")])

#
print "%s is done with %s, it is ready for you to use at %s" % \
(__file__, exampleVm.basenameStem, exampleVm.portsFile.getPorts(protocol="ssh", user="root")[0]["ipaddress"])
# END essential example code
