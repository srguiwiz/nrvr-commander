#!/usr/bin/python

"""Make a set of virtual machines and use them to run tests;
specifically this script runs Selenium automated tests of a website;
specifically this script should allow load testing, which so far
hasn't been something Selenium has beeen used for.

Example use of NrvrCommander.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

from collections import namedtuple
import os.path
import re
import shutil
import sys
import tempfile
import time

from nrvr.diskimage.isoimage import IsoImage
from nrvr.distros.common.ssh import LinuxSshCommand
from nrvr.distros.el.gnome import ElGnome
from nrvr.distros.el.kickstart import ElIsoImage, ElKickstartFileContent
from nrvr.distros.el.kickstarttemplates import ElKickstartTemplates
from nrvr.distros.el.util import ElUtil
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

# from http://code.google.com/p/selenium/downloads/list
seleniumServerStandaloneJarUrl = "http://selenium.googlecode.com/files/selenium-server-standalone-2.35.0.jar"
# from https://pypi.python.org/pypi/selenium/
seleniumPythonBindingsTarUrl = "https://pypi.python.org/packages/source/s/selenium/selenium-2.35.0.tar.gz"

# specific to the website you are testing
seleniumTestsScript = "selenium-tests.py"

# customize as needed
testVmsRange = range(181, 183)

# trying to approximate the order in which identifiers are used from this tuple
VmIdentifiers = namedtuple("VmIdentifiers", ["vmxFilePath", "name", "number", "ipaddress"])

# customize as needed
def vmIdentifiersForNumber(number):
    """Make various identifiers for a virtual machine.
    
    number
        an int probably best between 2 and 254.
    
    Return a VmIdentifiers instance."""
    # this is the order in which identifiers are derived
    #
    # will use hostonly on eth1
    ipaddress = IPAddress.numberWithinSubnet(VMwareHypervisor.localHostOnlyIPAddress, number)
    name = IPAddress.nameWithNumber("testvm", ipaddress, separator=None)
    vmxFilePath = ScriptUser.loggedIn.userHomeRelative("vmware/testvms/%s/%s.vmx" % (name, name))
    return VmIdentifiers(vmxFilePath=vmxFilePath,
                         name=name,
                         number=number,
                         ipaddress=ipaddress)

testVmsIdentifiers = map(lambda number: vmIdentifiersForNumber(number), testVmsRange)

def makeTestVmWithGui(vmIdentifiers, forceThisStep=False):
    """Make a single virtual machine.
    
    vmIdentifiers
        a VmIdentifiers instance.
    
    Return a VMwareMachine instance."""
    rootpw = "redwood"
    additionalUsers = [("tester","testing"),("tester2","testing")]
    #
    testVm = VMwareMachine(vmIdentifiers.vmxFilePath)
    #
    if forceThisStep:
        testVm.remove()
    #
    vmExists = testVm.vmxFile.exists()
    if vmExists == False:
        # make virtual machine
        testVm.mkdir()
        downloadedDistroIsoImage = ElIsoImage(Download.fromUrl
                                              ("http://ftp.scientificlinux.org/linux/scientific/6.4/i386/iso/SL-64-i386-2013-03-18-Install-DVD.iso"))
        kickstartFileContent = ElKickstartFileContent(ElKickstartTemplates.usableKickstartTemplate001)
        kickstartFileContent.replaceRootpw(rootpw)
        kickstartFileContent.elReplaceHostname(testVm.basenameStem)
        #kickstartFileContent.elReplaceStaticIP(vmIdentifiers.ipaddress, nameservers=Nameserver.list)
        kickstartFileContent.elReplaceStaticIP(vmIdentifiers.ipaddress, nameservers=[])
        kickstartFileContent.replaceAllPackages(ElKickstartTemplates.packagesOfSL64Desktop)
        kickstartFileContent.addPackage("python-setuptools") # needed for installing Python packages
        kickstartFileContent.removePackage("@office-suite") # not used for now
        # put in DHCP at eth0, to be used with NAT, works well if before hostonly
        kickstartFileContent.elAddNetworkConfigurationWithDhcp("eth0")
        kickstartFileContent.elActivateGraphicalLogin()
        for additionalUser in additionalUsers:
            kickstartFileContent.elAddUser(additionalUser[0], pwd=additionalUser[1])
        # pick right temporary directory, ideally same as VM
        modifiedDistroIsoImage = downloadedDistroIsoImage.cloneWithAutoBootingKickstart \
            (kickstartFileContent, os.path.join(testVm.directory, "made-to-order-os-install.iso"))
        # some necessary choices pointed out
        # 32-bit versus 64-bit linux, memsizeMegabytes needs to be more for 64-bit, guestOS is "centos" versus "centos-64"
        testVm.create(memsizeMegabytes=1200, guestOS="centos", ideDrives=[20000, 300, modifiedDistroIsoImage])
        testVm.portsFile.setSsh(ipaddress=vmIdentifiers.ipaddress, user="root", pwd=rootpw)
        testVm.portsFile.setShutdown()
        if len(additionalUsers):
            for additionalUser in additionalUsers:
                testVm.portsFile.setSsh(ipaddress=vmIdentifiers.ipaddress, user=additionalUser[0], pwd=additionalUser[1])
            mainUser = additionalUsers[0][0]
            testVm.portsFile.setMainUser(mainUser)
        else:
            mainUser = None
        # NAT works well if before hostonly
        testVm.vmxFile.setEthernetAdapter(0, "nat")
        testVm.vmxFile.setEthernetAdapter(1, "hostonly")
        # start up for operating system install
        VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
        VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        testVm.vmxFile.removeAllIdeCdromImages()
        modifiedDistroIsoImage.remove()
        #
        # start up for accepting known host key
        VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
        testVm.sleepUntilHasAcceptedKnownHostKey(ticker=True)
        #
        if mainUser:
            # a test machine needs to come up ready to run tests, no manual login
            testVm.sshCommand([ElGnome.elCommandToEnableAutoLogin(mainUser)])
            testVm.sshCommand([ElGnome.elCommandToDisableScreenSaver()], user=mainUser)
            # avoid distracting backgrounds, picks unique color to be clear this is a test machine
            testVm.sshCommand([ElGnome.elCommandToSetSolidColorBackground("#dddd66")], user=mainUser)
            testVm.sshCommand([ElGnome.elCommandToDisableUpdateNotifications()], user=mainUser)
        #
        # shut down
        testVm.shutdownCommand()
        VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        # start up until successful login into GUI
        VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
        userSshParameters = testVm.sshParameters(user=mainUser)
        LinuxSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
        #
        if mainUser:
            testVm.sshCommand([ElGnome.commandToAddSystemMonitorPanel()], user=mainUser)
        #
        # shut down for snapshot
        testVm.shutdownCommand()
        VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        VMwareHypervisor.local.createSnapshot(testVm.vmxFilePath, "OS installed")
    #
    return testVm

def installToolsIntoTestVm(vmIdentifiers, forceThisStep=False):
    if forceThisStep:
        VMwareHypervisor.local.revertToSnapshotAndDeleteDescendants(vmIdentifiers.vmxFilePath, "OS installed")
    #
    snapshots = VMwareHypervisor.local.listSnapshots(vmIdentifiers.vmxFilePath)
    snapshotExists = "tools installed" in snapshots
    if not snapshotExists:
        testVm = VMwareMachine(vmIdentifiers.vmxFilePath)
        # start up until successful login into GUI
        VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
        userSshParameters = testVm.sshParameters(user=testVm.mainUser)
        LinuxSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
        #
        # install tools
        scriptDir = os.path.dirname(os.path.abspath(__file__))
        seleniumServerStandaloneJarPath = Download.fromUrl(seleniumServerStandaloneJarUrl)
        testVm.scpPutCommand(fromHostPath=seleniumServerStandaloneJarPath,
                             toGuestPath="~/Downloads/" + Download.basename(seleniumServerStandaloneJarUrl),
                             guestUser=testVm.mainUser)
        seleniumPythonBindingsTarPath = Download.fromUrl(seleniumPythonBindingsTarUrl)
        seleniumPythonBindingsTarBaseName = Download.basename(seleniumPythonBindingsTarUrl)
        testVm.scpPutCommand(fromHostPath=seleniumPythonBindingsTarPath,
                             toGuestPath="~/" + seleniumPythonBindingsTarBaseName,
                             guestUser="root")
        seleniumPythonBindingsExtracted = re.match(r"^(\S+)(?:\.tar\.gz)$", seleniumPythonBindingsTarBaseName).group(1)
        testVm.sshCommand(["cd ~/"
                           + " && tar -xf ~/" + seleniumPythonBindingsTarBaseName
                           + " && cd " + seleniumPythonBindingsExtracted + "/"
                           + " && chmod +x setup.py"
                           + " && ./setup.py install"], user="root")
        #
        # shut down for snapshot
        testVm.shutdownCommand()
        VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        VMwareHypervisor.local.createSnapshot(testVm.vmxFilePath, "tools installed")

def runTestsInTestVm(vmIdentifiers, forceThisStep=False):
    if forceThisStep:
        VMwareHypervisor.local.revertToSnapshotAndDeleteDescendants(vmIdentifiers.vmxFilePath, "tools installed")
    #
    snapshots = VMwareHypervisor.local.listSnapshots(vmIdentifiers.vmxFilePath)
    snapshotExists = "ran tests" in snapshots
    if not snapshotExists:
        testVm = VMwareMachine(vmIdentifiers.vmxFilePath)
        # start up until successful login into GUI
        VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
        userSshParameters = testVm.sshParameters(user=testVm.mainUser)
        LinuxSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
        #
        # copy tests
        scriptDir = os.path.dirname(os.path.abspath(__file__))
        seleniumTestsScriptPath = os.path.join(scriptDir, seleniumTestsScript)
        testVm.scpPutCommand(fromHostPath=seleniumTestsScriptPath,
                             toGuestPath="~/Downloads/" + seleniumTestsScript,
                             guestUser=testVm.mainUser)
        #
        # apparently on some virtual machines the NAT interface takes some time to come up
        SshCommand(userSshParameters,
                   [ElUtil.commandToWaitForNetworkDevice(device="eth0", maxSeconds=100)])
        #
        # start up Selenium
        SshCommand(userSshParameters,
                   ["nohup "
                    + "java -jar ~/Downloads/" + Download.basename(seleniumServerStandaloneJarUrl)
                    + " &> /dev/null &"])
        # allow some time to start up
        time.sleep(5)
        #
        # run tests
        testVm.sshCommand(["export DISPLAY=:0.0 ; "
                           + "cd ~/Downloads/"
                           + " && chmod +x " + seleniumTestsScript
                           + " && nohup ./" + seleniumTestsScript + " &> /dev/null &"], user=testVm.mainUser)
        #time.sleep(60)
        #
        # shut down for snapshot
        #testVm.shutdownCommand()
        #VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        #VMwareHypervisor.local.createSnapshot(testVm.vmxFilePath, "ran tests")

# make sure virtual machines are no longer running from previous activities if any
for vmIdentifiers in testVmsIdentifiers:
    VMwareHypervisor.local.notRunningRequired(vmIdentifiers.vmxFilePath)

testVms = []
for vmIdentifiers in testVmsIdentifiers:
    testVm = makeTestVmWithGui(vmIdentifiers)
    testVms.append(testVm)

for vmIdentifiers in testVmsIdentifiers:
    testVm = installToolsIntoTestVm(vmIdentifiers) #, forceThisStep=True)

for vmIdentifiers in testVmsIdentifiers:
    testVm = runTestsInTestVm(vmIdentifiers) #, forceThisStep=True)

# alternate kind of loop we are not using right now
for testVm in testVms:
    pass

print "DONE for now, processed %s" % ", ".join(map(lambda vmdentifier: vmdentifier.name, testVmsIdentifiers))
