#!/usr/bin/python

"""Example use of NrvrCommander.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import os.path
import shutil
import sys
import tempfile
import time

from nrvr.diskimage.isoimage import IsoImage
from nrvr.distros.common.ssh import LinuxSshCommand
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
    # long comment solely regarding .iso files larger than exactly 4GB, e.g. x86_64 Install-DVD
    #
    # this is just a temporary minor nuisance that will go away
    #
    # looking forward to smoother solution soon
    #
    # had some issues with some files in the original .iso not coming through right with iso-read,
    # test with
    # iso-read -i ~/Downloads/SL-61-x86_64-2011-07-27-Install-DVD.iso -e isolinux/isolinux.cfg -o ~/test.txt ; more ~/test.txt ; ls ~/test.txt -al
    # iso-read -i ~/Downloads/SL-61-x86_64-2011-11-09-Install-DVD.iso -e repodata/repomd.xml -o ~/test.txt ; more ~/test.txt ; ls ~/test.txt -al
    # trying workaround with expanding in GNOME
    # TODO document command line for it from comment at
    #   http://rwmj.wordpress.com/2010/05/05/tip-ways-to-extract-an-iso-without-needing-root/
    # then because problem is with > 4GB .iso file size
    #   http://lists.gnu.org/archive/html/libcdio-help/2011-12/msg00001.html
    #   http://savannah.gnu.org/bugs/?39373
    # a solution is to make a smaller .iso file by removing large package which will not be used
    # find ~/Downloads/tmp-SL61-64bit-iso/ -name 'kdegames-*' -exec rm {} \;
    # find ~/Downloads/tmp-SL61-64bit-iso/ -name 'kdebase-workspace-wallpapers-*' -exec rm {} \;
    # find ~/Downloads/tmp-SL61-64bit-iso/ -name 'scenery-backgrounds-*' -exec rm {} \;
    # find ~/Downloads/tmp-SL61-64bit-iso/ -name 'gimp-help-[0-9]' -exec rm {} \;
    # possibly to avoid time consuming confusion, explain in a top level file REMOVED.TXT
    # and some more cleanup
    # find ~/Downloads/tmp-SL61-64bit-iso/ -name 'TRANS.TBL'
    # find ~/Downloads/tmp-SL61-64bit-iso/ -name 'TRANS.TBL' -exec rm -rf {} \;
    # and make the new .iso image
    # genisoimage -r -J -T -f -no-emul-boot -boot-load-size 4 -boot-info-table -b isolinux/isolinux.bin -c isolinux/boot.cat -V remastered -o ~/Downloads/SL-61-x86_64-2011-11-09-Install-DVD-less-some.iso ~/Downloads/tmp-SL61-64bit-iso/
    # and you might want to check it is smaller than 2^32 == 4294967296 bytes
    #
    #downloadedDistroIsoImage = ElIsoImage(ScriptUser.loggedIn.userHomeRelative \
    #                                      ("Downloads/SL-64-i386-2013-03-18-Install-DVD.iso"))
    downloadedDistroIsoImage = ElIsoImage(Download.fromUrl
                                          ("http://ftp.scientificlinux.org/linux/scientific/6.4/i386/iso/SL-64-i386-2013-03-18-Install-DVD.iso"))
    # some possible choices pointed out
    # server w command line only
    kickstartFileContent = ElKickstartFileContent(ElKickstartTemplates.usableKickstartTemplate001)
    kickstartFileContent.replaceRootpw(rootpw)
    kickstartFileContent.elReplaceHostname(exampleVm.basenameStem)
    kickstartFileContent.elReplaceStaticIP(ipaddress, nameservers=Nameserver.list)
    # put in DHCP at eth0, to be used with NAT, works well if before hostonly
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
    (kickstartFileContent, os.path.join(exampleVm.directory, "made-to-order-os-install.iso"))
    # some necessary choices pointed out
    # 32-bit versus 64-bit linux, memsizeMegabytes needs to be more for 64-bit, guestOS is "centos" versus "centos-64"
    exampleVm.create(memsizeMegabytes=1200, guestOS="centos", ideDrives=[20000, 300, modifiedDistroIsoImage])
    exampleVm.portsFile.setSsh(ipaddress=ipaddress, user="root", pwd=rootpw)
    exampleVm.portsFile.setShutdown()
    for additionalUser in additionalUsers:
        exampleVm.portsFile.setSsh(ipaddress=ipaddress, user=additionalUser[0], pwd=additionalUser[1])
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

# some possible choices pointed out
#if len(additionalUsers):
#    exampleVm.sshCommand([ElGnome.elCommandToEnableAutoLogin(additionalUsers[0][0])])
#    exampleVm.sshCommand([ElGnome.elCommandToDisableScreenSaver()], user=additionalUsers[0][0])
#    exampleVm.sshCommand([ElGnome.elCommandToSetSolidColorBackground()], user=additionalUsers[0][0])
#    exampleVm.sshCommand([ElGnome.elCommandToDisableUpdateNotifications()], user=additionalUsers[0][0])

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
#exampleSshParameters = exampleVm.sshParameters(user=additionalUsers[0][0])
#LinuxSshCommand.sleepUntilIsGuiAvailable(exampleSshParameters, ticker=True)

# a possible modification pointed out
# just a demo
#exampleSshParameters = exampleVm.sshParameters(user=additionalUsers[0][0])
#SshCommand(exampleSshParameters, [ElGnome.commandToStartApplicationInGui("firefox")])

#
print "%s is done with %s, it is ready for you to use at %s" % \
(__file__, exampleVm.basenameStem, exampleVm.portsFile.getPorts(protocol="ssh", user="root")[0]["ipaddress"])
# END essential example code
