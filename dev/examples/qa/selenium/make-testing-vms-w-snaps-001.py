#!/usr/bin/python

"""Make a set of virtual machines and use them to run tests;
specifically this script runs Selenium automated tests of a website;
specifically this script should allow load testing, which so far
hasn't been something Selenium has beeen used for.

As implemented uses virtual machine snapshots.

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
from nrvr.distros.common.util import LinuxUtil
from nrvr.distros.el.gnome import ElGnome
from nrvr.distros.el.kickstart import ElIsoImage, ElKickstartFileContent
from nrvr.distros.el.kickstarttemplates import ElKickstartTemplates
from nrvr.distros.ub.gnome import UbGnome
from nrvr.distros.ub.kickstart import UbIsoImage, UbKickstartFileContent
from nrvr.distros.ub.kickstarttemplates import UbKickstartTemplates
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
VMwareHypervisor.snapshotsRequired()

# from https://www.scientificlinux.org/download/
scientificLinuxDistro32IsoUrl = "http://ftp.scientificlinux.org/linux/scientific/6.4/i386/iso/SL-64-i386-2013-03-18-Install-DVD.iso"
scientificLinuxDistro64IsoUrl = "http://ftp.scientificlinux.org/linux/scientific/6.4/x86_64/iso/SL-64-x86_64-2013-03-18-Install-DVD.iso"

# from http://releases.ubuntu.com/
ubuntuDistro32IsoUrl = "http://releases.ubuntu.com/12.04.3/ubuntu-12.04.3-alternate-i386.iso"
ubuntuDistro64IsoUrl = "http://releases.ubuntu.com/12.04.3/ubuntu-12.04.3-alternate-amd64.iso"

# from http://code.google.com/p/selenium/downloads/list
seleniumServerStandaloneJarUrl = "http://selenium.googlecode.com/files/selenium-server-standalone-2.35.0.jar"
# from https://pypi.python.org/pypi/selenium/
seleniumPythonBindingsTarUrl = "https://pypi.python.org/packages/source/s/selenium/selenium-2.35.0.tar.gz"
#
googleChromeUbuntu32InstallerUrl = "https://dl.google.com/linux/direct/google-chrome-stable_current_i386.deb"
googleChromeUbuntu64InstallerUrl = "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
# from https://code.google.com/p/chromedriver/downloads/list
chromeDriverLinux32InstallerZipUrl = "https://chromedriver.googlecode.com/files/chromedriver_linux32_2.3.zip"
chromeDriverLinux64InstallerZipUrl = "https://chromedriver.googlecode.com/files/chromedriver_linux64_2.3.zip"

# used to be specific to the website you are testing,
# no probably just the files inside testsDirectory will change
testsInvokerScript = "tests-invoker.py"
testsDirectory = "tests"

# will modulo over machinesPattern,
# customize as needed
testVmsRange = range(181, 183) #189) # or more

# customize as needed
rootpw = "redwood"

UserProperties = namedtuple("UserProperties", ["username", "pwd"])
# customize as needed
# normally at least one
testUsersProperties = [UserProperties(username="tester", pwd="testing"),
                       UserProperties(username="tester2", pwd="testing")
                       ]

MachineParameters = namedtuple("MachineParameters", ["distro", "arch", "browser", "lang", "memsize"])
class Arch(str): pass # make sure it is a string to avoid string-number unequality
# customize as needed
machinesPattern = [MachineParameters(distro="el", arch=Arch(32), browser="firefox", lang="en_US.UTF-8", memsize=900),
                   MachineParameters(distro="ub", arch=Arch(32), browser="chrome", lang="en_US.UTF-8", memsize=960),
                   MachineParameters(distro="el", arch=Arch(32), browser="firefox", lang="de_DE.UTF-8", memsize=920),
                   MachineParameters(distro="ub", arch=Arch(32), browser="chrome", lang="de_DE.UTF-8", memsize=980),
                   MachineParameters(distro="el", arch=Arch(32), browser="firefox", lang="zh_CN.UTF-8", memsize=1000),
                   MachineParameters(distro="ub", arch=Arch(32), browser="chrome", lang="zh_CN.UTF-8", memsize=1060),
                   MachineParameters(distro="el", arch=Arch(64), browser="firefox", lang="en_US.UTF-8", memsize=1400),
                   MachineParameters(distro="ub", arch=Arch(64), browser="chrome", lang="en_US.UTF-8", memsize=1460)
                   ]

# trying to approximate the order in which identifiers are used from this tuple
VmIdentifiers = namedtuple("VmIdentifiers", ["vmxFilePath", "name", "number", "ipaddress", "mapas"])

# customize as needed
def vmIdentifiersForNumber(number, index):
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
    indexModulo = index % len(machinesPattern)
    mapas = machinesPattern[indexModulo]
    return VmIdentifiers(vmxFilePath=vmxFilePath,
                         name=name,
                         number=number,
                         ipaddress=ipaddress,
                         mapas=mapas)

#testVmsIdentifiers = map(lambda number: vmIdentifiersForNumber(number), testVmsRange)
testVmsIdentifiers = []
for index, number in enumerate(testVmsRange):
    testVmsIdentifiers.append(vmIdentifiersForNumber(number, index))

def makeTestVmWithGui(vmIdentifiers, forceThisStep=False):
    """Make a single virtual machine.
    Enterprise Linux or Ubuntu.
    
    vmIdentifiers
        a VmIdentifiers instance.
    
    Return a VMwareMachine instance."""
    testVm = VMwareMachine(vmIdentifiers.vmxFilePath)
    distro = vmIdentifiers.mapas.distro
    arch = vmIdentifiers.mapas.arch
    browser = vmIdentifiers.mapas.browser
    #
    if not distro in ["el", "ub"]:
        raise Exception("unknown distro %s" % (distro))
    if not arch in [Arch(32), Arch(64)]:
        raise Exception("unknown architecture arch=%s" % (arch))
    if distro == "el" and browser == "chrome":
        raise Exception("cannot run browser %s in distro %s" % (browser, distro))
    #
    if distro == "el":
        additionalUsersProperties = testUsersProperties
        regularUserProperties = testUsersProperties[0]
    elif distro == "ub":
        # Ubuntu kickstart supports only one regular user
        regularUserProperties = testUsersProperties[0]
    #
    if forceThisStep:
        if VMwareHypervisor.local.isRunning(testVm.vmxFilePath):
            testVm.shutdownCommand(ignoreException=True)
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        testVm.remove()
    #
    vmExists = testVm.vmxFile.exists()
    if vmExists == False:
        # make virtual machine
        testVm.mkdir()
        #
        if distro == "el":
            if arch == Arch(32):
                downloadedDistroIsoImage = ElIsoImage(Download.fromUrl(scientificLinuxDistro32IsoUrl))
            elif arch == Arch(64):
                downloadedDistroIsoImage = ElIsoImage(Download.fromUrl(scientificLinuxDistro64IsoUrl))
            kickstartFileContent = ElKickstartFileContent(ElKickstartTemplates.usableElKickstartTemplate001)
            kickstartFileContent.replaceLang(vmIdentifiers.mapas.lang)
            kickstartFileContent.replaceRootpw(rootpw)
            kickstartFileContent.elReplaceHostname(testVm.basenameStem)
            #kickstartFileContent.elReplaceStaticIP(vmIdentifiers.ipaddress, nameservers=Nameserver.list)
            # put in DHCP at eth0, to be used with NAT, works well if before hostonly
            kickstartFileContent.elReplaceStaticIP(vmIdentifiers.ipaddress, nameservers=[])
            kickstartFileContent.elAddNetworkConfigurationWithDhcp("eth0")
            kickstartFileContent.replaceAllPackages(ElKickstartTemplates.packagesOfSL64Desktop)
            kickstartFileContent.addPackage("python-setuptools") # needed for installing Python packages
            kickstartFileContent.removePackage("@office-suite") # not used for now
            kickstartFileContent.elActivateGraphicalLogin()
            for additionalUserProperties in additionalUsersProperties:
                kickstartFileContent.elAddUser(additionalUserProperties.username, pwd=additionalUserProperties.pwd)
            kickstartFileContent.setSwappiness(10)
            # pick right temporary directory, ideally same as VM
            modifiedDistroIsoImage = downloadedDistroIsoImage.cloneWithAutoBootingKickstart \
                (kickstartFileContent, os.path.join(testVm.directory, "made-to-order-os-install.iso"))
            # some necessary choices pointed out
            # 32-bit versus 64-bit linux, memsizeMegabytes needs to be more for 64-bit, guestOS is "centos" versus "centos-64"
            if arch == Arch(32):
                guestOS = "centos"
            elif arch == Arch(64):
                guestOS = "centos-64"
            testVm.create(memsizeMegabytes=vmIdentifiers.mapas.memsize,
                          guestOS=guestOS,
                          ideDrives=[20000, 300, modifiedDistroIsoImage])
            testVm.portsFile.setSsh(ipaddress=vmIdentifiers.ipaddress, user="root", pwd=rootpw)
            testVm.portsFile.setShutdown()
            for additionalUserProperties in additionalUsersProperties:
                testVm.portsFile.setSsh(ipaddress=vmIdentifiers.ipaddress,
                                        user=additionalUserProperties.username,
                                        pwd=additionalUserProperties.pwd)
            testVm.portsFile.setRegularUser(regularUserProperties.username)
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
            # a test machine needs to come up ready to run tests, no manual login
            testVm.sshCommand([ElGnome.elCommandToEnableAutoLogin(regularUserProperties.username)])
            testVm.sshCommand([ElGnome.elCommandToDisableScreenSaver()], user=regularUserProperties.username)
            # avoid distracting backgrounds, picks unique color to be clear this is a test machine
            testVm.sshCommand([ElGnome.elCommandToSetSolidColorBackground("#dddd66")], user=regularUserProperties.username)
            testVm.sshCommand([ElGnome.elCommandToDisableUpdateNotifications()], user=regularUserProperties.username)
            #
            # might as well
            testVm.sshCommand([LinuxUtil.commandToEnableSudo(regularUserProperties.username)])
            #
            # shut down
            testVm.shutdownCommand()
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
            # start up until successful login into GUI
            VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
            userSshParameters = testVm.sshParameters(user=regularUserProperties.username)
            LinuxSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
            #
            testVm.sshCommand([ElGnome.elCommandToAddSystemMonitorPanel()], user=regularUserProperties.username)
            #
            # shut down for snapshot
            testVm.shutdownCommand()
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        elif distro == "ub":
            if arch == Arch(32):
                downloadedDistroIsoImage = ElIsoImage(Download.fromUrl(ubuntuDistro32IsoUrl))
            elif arch == Arch(64):
                downloadedDistroIsoImage = ElIsoImage(Download.fromUrl(ubuntuDistro64IsoUrl))
            kickstartFileContent = UbKickstartFileContent(UbKickstartTemplates.usableUbKickstartTemplate001)
            kickstartFileContent.replaceLang(vmIdentifiers.mapas.lang)
            kickstartFileContent.replaceRootpw(rootpw)
            kickstartFileContent.ubReplaceHostname(testVm.basenameStem)
            kickstartFileContent.ubCreateNetworkConfigurationSection()
            #kickstartFileContent.ubAddNetworkConfigurationStatic(device="eth0", ipaddress=ipaddress, nameservers=Nameserver.list)
            # put in DHCP at eth0, to be used with NAT, works well if before hostonly
            kickstartFileContent.ubAddNetworkConfigurationDhcp("eth0")
            kickstartFileContent.ubAddNetworkConfigurationStatic(device="eth1",
                                                                 ipaddress=vmIdentifiers.ipaddress,
                                                                 nameservers=Nameserver.list)
            kickstartFileContent.ubSetUpgradeNone()
            kickstartFileContent.ubSetUpdatePolicyNone()
            kickstartFileContent.replaceAllPackages(UbKickstartTemplates.packagesForUbuntuDesktop)
            kickstartFileContent.addPackage("default-jre") # Java needed for Selenium Server standalone .jar
            kickstartFileContent.addPackage("python-setuptools") # needed for installing Python packages
            kickstartFileContent.addPackage("libxss1") # needed for Google Chrome
            kickstartFileContent.ubActivateGraphicalLogin()
            kickstartFileContent.ubSetUser(regularUserProperties.username, pwd=regularUserProperties.pwd)
            kickstartFileContent.setSwappiness(10)
            # pick right temporary directory, ideally same as VM
            modifiedDistroIsoImage = downloadedDistroIsoImage.cloneWithAutoBootingKickstart \
                (kickstartFileContent, os.path.join(testVm.directory, "made-to-order-os-install.iso"))
            # some necessary choices pointed out
            # 32-bit versus 64-bit linux, memsizeMegabytes needs to be more for 64-bit, guestOS is "ubuntu" versus "ubuntu-64"
            if arch == Arch(32):
                guestOS = "ubuntu"
            elif arch == Arch(64):
                guestOS = "ubuntu-64"
            testVm.create(memsizeMegabytes=vmIdentifiers.mapas.memsize,
                          guestOS=guestOS,
                          ideDrives=[20000, 300, modifiedDistroIsoImage])
            testVm.portsFile.setSsh(ipaddress=vmIdentifiers.ipaddress, user="root", pwd=rootpw)
            testVm.portsFile.setShutdown()
            testVm.portsFile.setSsh(ipaddress=vmIdentifiers.ipaddress,
                                    user=regularUserProperties.username,
                                    pwd=regularUserProperties.pwd)
            testVm.portsFile.setRegularUser(regularUserProperties.username)
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
            # a test machine needs to come up ready to run tests, no manual login
            testVm.sshCommand([UbGnome.ubCommandToEnableAutoLogin(regularUserProperties.username)])
            #
            # might as well
            testVm.sshCommand([LinuxUtil.commandToEnableSudo(regularUserProperties.username)])
            #
            # shut down
            testVm.shutdownCommand()
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
            # start up until successful login into GUI
            VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
            userSshParameters = testVm.sshParameters(user=regularUserProperties.username)
            LinuxSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
            #
            testVm.sshCommand([UbGnome.ubCommandToDisableScreenSaver()], user=regularUserProperties.username)
            # avoid distracting backgrounds, picks unique color to be clear this is a test machine
            testVm.sshCommand([UbGnome.ubCommandToSetSolidColorBackground("#dddd66")], user=regularUserProperties.username)
            testVm.sshCommand([UbGnome.ubCommandToAddSystemMonitorPanel()], user=regularUserProperties.username)
            #
            # shut down for snapshot
            testVm.shutdownCommand()
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        #
        VMwareHypervisor.local.createSnapshot(testVm.vmxFilePath, "OS installed")
    #
    return testVm

def installToolsIntoTestVm(vmIdentifiers, forceThisStep=False):
    testVm = VMwareMachine(vmIdentifiers.vmxFilePath)
    distro = vmIdentifiers.mapas.distro
    arch = vmIdentifiers.mapas.arch
    browser = vmIdentifiers.mapas.browser
    #
    snapshots = VMwareHypervisor.local.listSnapshots(vmIdentifiers.vmxFilePath)
    snapshotExists = "tools installed" in snapshots
    if not snapshotExists or forceThisStep:
        if VMwareHypervisor.local.isRunning(testVm.vmxFilePath):
            testVm.shutdownCommand(ignoreException=True)
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        VMwareHypervisor.local.revertToSnapshotAndDeleteDescendants(vmIdentifiers.vmxFilePath, "OS installed")
        #
        # start up until successful login into GUI
        VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
        userSshParameters = testVm.sshParameters(user=testVm.regularUser)
        LinuxSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
        #
        # a necessity on some international version OS
        testVm.sshCommand(["mkdir -p ~/Downloads"], user=testVm.regularUser)
        #
        # install Google Chrome
        if browser == "chrome" and distro == "ub":
            if arch == Arch(32):
                googleChromeUbuntuInstallerUrl = googleChromeUbuntu32InstallerUrl
            elif arch == Arch(64):
                googleChromeUbuntuInstallerUrl = googleChromeUbuntu64InstallerUrl
            chromeInstallerOnHostPath = Download.fromUrl(googleChromeUbuntuInstallerUrl)
            chromeInstallerOnGuestPath = "~/" + Download.basename(googleChromeUbuntuInstallerUrl)
            testVm.scpPutCommand(fromHostPath=chromeInstallerOnHostPath,
                                 toGuestPath=chromeInstallerOnGuestPath,
                                 guestUser="root")
            # install
            testVm.sshCommand(["cd ~/"
                               + " && dpkg -i " + chromeInstallerOnGuestPath],
                              user="root")
            # run once, wait, terminate
            testVm.sshCommand(["export DISPLAY=:0.0 ; "
                               + "( nohup"
                               + " google-chrome --cancel-first-run --no-default-browser-check about:blank"
                               + " &> /dev/null & )"
                               + " && sleep 5"
                               + " && kill `pidof chrome`"],
                              user=testVm.regularUser)
        #
        # install Selenium Server standalone
        seleniumServerStandaloneJarPath = Download.fromUrl(seleniumServerStandaloneJarUrl)
        testVm.scpPutCommand(fromHostPath=seleniumServerStandaloneJarPath,
                             toGuestPath="~/Downloads/" + Download.basename(seleniumServerStandaloneJarUrl),
                             guestUser=testVm.regularUser)
        #
        if browser == "chrome":
            # install ChromeDriver
            # see http://code.google.com/p/selenium/wiki/ChromeDriver
            if arch == Arch(32):
                chromeDriverLinuxInstallerZipUrl = chromeDriverLinux32InstallerZipUrl
            elif arch == Arch(64):
                chromeDriverLinuxInstallerZipUrl = chromeDriverLinux64InstallerZipUrl
            chromeDriverInstallerZipPath = Download.fromUrl(chromeDriverLinuxInstallerZipUrl)
            chromeDriverInstallerZipBaseName = Download.basename(chromeDriverLinuxInstallerZipUrl)
            testVm.scpPutCommand(fromHostPath=chromeDriverInstallerZipPath,
                                 toGuestPath="~/" + chromeDriverInstallerZipBaseName,
                                 guestUser="root")
            chromeDriverInstallerExtracted = re.match(r"^(\S+)(?:\.zip)$", chromeDriverInstallerZipBaseName).group(1)
            testVm.sshCommand(["cd ~/"
                               + " && unzip -o ~/" + chromeDriverInstallerZipBaseName + " -d ~/" + chromeDriverInstallerExtracted
                               + " && chmod +x ~/" + chromeDriverInstallerExtracted + "/chromedriver"
                               + " && cp ~/" + chromeDriverInstallerExtracted + "/chromedriver /usr/local/bin/chromedriver"],
                              user="root")
        #
        # install Python bindings
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
                           + " && ./setup.py install"],
                          user="root")
        #
        # shut down for snapshot
        testVm.shutdownCommand()
        VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        VMwareHypervisor.local.createSnapshot(testVm.vmxFilePath, "tools installed")

def runTestsInTestVm(vmIdentifiers, forceThisStep=False):
    testVm = VMwareMachine(vmIdentifiers.vmxFilePath)
    distro = vmIdentifiers.mapas.distro
    browser = vmIdentifiers.mapas.browser
    #
    snapshots = VMwareHypervisor.local.listSnapshots(vmIdentifiers.vmxFilePath)
    snapshotExists = "ran tests" in snapshots
    if not snapshotExists or forceThisStep:
        if VMwareHypervisor.local.isRunning(testVm.vmxFilePath):
            testVm.shutdownCommand(ignoreException=True)
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        VMwareHypervisor.local.revertToSnapshotAndDeleteDescendants(vmIdentifiers.vmxFilePath, "tools installed")
        #
        # start up until successful login into GUI
        VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
        userSshParameters = testVm.sshParameters(user=testVm.regularUser)
        LinuxSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
        #
        # copy tests
        scriptDir = os.path.dirname(os.path.abspath(__file__))
        testsInvokerScriptPath = os.path.join(scriptDir, testsInvokerScript)
        testsDirectoryPath = os.path.join(scriptDir, testsDirectory)
        testVm.scpPutCommand(fromHostPath=[testsInvokerScriptPath, testsDirectoryPath],
                             toGuestPath="~/Downloads/",
                             guestUser=testVm.regularUser)
        # fix up tests, if necessary
        if browser == "chrome":
            # switch from webdriver.Firefox() to webdriver.Chrome()
            testVm.sshCommand(["sed -i -e 's/webdriver\.Firefox/webdriver.Chrome/'"
                               + " ~/Downloads/" + testsDirectory + "/*.py"],
                              user=testVm.regularUser)
        #
        # apparently on some virtual machines the NAT interface takes some time to come up
        SshCommand(userSshParameters,
                   [LinuxUtil.commandToWaitForNetworkDevice(device="eth0", maxSeconds=100)])
        #
        # start up Selenium Server
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
                           + " && chmod +x " + testsInvokerScript
                           + " && chmod +x " + testsDirectory + "/*.py"
                           + " && ( nohup ./" + testsInvokerScript + " &> ./" + testsInvokerScript + ".log & )"],
                          user=testVm.regularUser)
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

print "DONE for now, processed %s" % (", ".join(map(lambda vmdentifier: vmdentifier.name, testVmsIdentifiers)))
