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
import ntpath
import os.path
import posixpath
import random
import re
import shutil
import string
import sys
import tempfile
import time

from nrvr.diskimage.isoimage import IsoImage, IsoImageModificationFromString, IsoImageModificationFromPath
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
from nrvr.util.registering import RegisteringUser
from nrvr.util.requirements import SystemRequirements
from nrvr.util.times import Timestamp
from nrvr.util.user import ScriptUser
from nrvr.vm.vmware import VmdkFile, VmxFile, VMwareHypervisor, VMwareMachine
from nrvr.vm.vmwaretemplates import VMwareTemplates
from nrvr.wins.common.autounattend import WinUdfImage
from nrvr.wins.common.cygwin import CygwinDownload
from nrvr.wins.common.javaw import JavawDownload
from nrvr.wins.common.ssh import CygwinSshCommand
from nrvr.wins.win7.autounattend import Win7UdfImage, Win7AutounattendFileContent
from nrvr.wins.win7.autounattendtemplates import Win7AutounattendTemplates

# this is a good way to preflight check
SystemRequirements.commandsRequiredByImplementations([IsoImage, WinUdfImage,
                                                      VmdkFile, VMwareHypervisor,
                                                      SshCommand, ScpCommand,
                                                      CygwinDownload, JavawDownload],
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

# from http://social.technet.microsoft.com/Forums/windows/en-US/653d34d9-ac99-42db-80c8-6300f01f7aae/windows-7downloard
# or http://forums.mydigitallife.info/threads/14709-Windows-7-Digital-River-direct-links-Multiple-Languages-X86-amp-X64/page60
windows7ProInstaller32EnIsoUrl = "http://msft.digitalrivercontent.net/win/X17-59183.iso"
windows7ProInstaller64EnIsoUrl = "http://msft.digitalrivercontent.net/win/X17-59186.iso"

# from http://code.google.com/p/selenium/downloads/list
seleniumServerStandaloneJarUrl = "http://selenium.googlecode.com/files/selenium-server-standalone-2.35.0.jar"
# from https://pypi.python.org/pypi/selenium/
seleniumPythonBindingsTarUrl = "https://pypi.python.org/packages/source/s/selenium/selenium-2.35.0.tar.gz"
# from https://pypi.python.org/pypi/setuptools
pythonSetuptoolsTarUrl = "https://pypi.python.org/packages/source/s/setuptools/setuptools-2.0.1.tar.gz"
#
googleChromeUbuntu32InstallerUrl = "https://dl.google.com/linux/direct/google-chrome-stable_current_i386.deb"
googleChromeUbuntu64InstallerUrl = "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
# from https://code.google.com/p/chromedriver/downloads/list
chromeDriverLinux32InstallerZipUrl = "https://chromedriver.googlecode.com/files/chromedriver_linux32_2.3.zip"
chromeDriverLinux64InstallerZipUrl = "https://chromedriver.googlecode.com/files/chromedriver_linux64_2.3.zip"

# from http://code.google.com/p/selenium/downloads/list
seleniumIeDriverServer32ZipUrl = "http://selenium.googlecode.com/files/IEDriverServer_Win32_2.39.0.zip"
seleniumIeDriverServer64ZipUrl = "http://selenium.googlecode.com/files/IEDriverServer_x64_2.39.0.zip"

# from http://www.python.org/download/
python2xWindows32InstallerMsiUrl = "http://www.python.org/ftp/python/2.7.6/python-2.7.6.msi"
python2xWindows64InstallerMsiUrl = "http://www.python.org/ftp/python/2.7.6/python-2.7.6.amd64.msi"

# used to be specific to the website you are testing,
# no probably just the files inside testsDirectory will change
testsInvokerScript = "tests-invoker.py"
testsDirectory = "tests"

# will modulo over machinesPattern,
# customize as needed
testVmsRange = range(181, 183) #189) # or more

# customize as needed
rootpw = "redwood"

# customize as needed
# normally at least one
testUsers = [RegisteringUser(username="tester", pwd="testing"),
             RegisteringUser(username="tester2", pwd="testing")
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
                   MachineParameters(distro="ub", arch=Arch(64), browser="chrome", lang="en_US.UTF-8", memsize=1460),
                   #MachineParameters(distro="win", arch=Arch(32), browser="ie", lang="en-US", memsize=1020),
                   #MachineParameters(distro="win", arch=Arch(64), browser="ie", lang="en-US", memsize=1520),
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

# this example use of NrvrCommander makes use of features provided of different components
# of NrvrCommander,
# it may be important to understand that other uses (use patterns) are possible and reasonable
#
# specifically this example use has first been written for and maybe with better understanding
# of Linux operating systems,
# therefore this example use probably has (shows) a different, maybe better, style of
# separation between root and additional (regular) users in Linux than in Windows
#
# it should be possible to spend some time on making it do things differently in Windows,
# not saying this is bad, just saying different styles are possible

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
    if not distro in ["el", "ub", "win"]:
        raise Exception("unknown distro %s" % (distro))
    if not arch in [Arch(32), Arch(64)]:
        raise Exception("unknown architecture arch=%s" % (arch))
    if not browser in ["firefox", "chrome", "iexplorer"]:
        raise Exception("unknown distro %s" % (distro))
    if distro == "el" and browser == "chrome":
        raise Exception("cannot run browser %s in distro %s" % (browser, distro))
    if (distro == "el" or distro == "ub") and browser == "iexplorer":
        raise Exception("cannot run browser %s in distro %s" % (browser, distro))
    #
    if distro == "el":
        additionalUsers = testUsers
        regularUser = testUsers[0]
    elif distro == "ub":
        # Ubuntu kickstart supports only one regular user
        regularUser = testUsers[0]
    elif distro == "win":
        additionalUsers = testUsers
        regularUser = testUsers[0]
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
            for additionalUser in additionalUsers:
                kickstartFileContent.elAddUser(additionalUser.username, pwd=additionalUser.pwd)
            kickstartFileContent.setSwappiness(10)
            # pick right temporary directory, ideally same as VM
            modifiedDistroIsoImage = downloadedDistroIsoImage.cloneWithAutoBootingKickstart \
                (kickstartFileContent,
                 cloneIsoImagePath=os.path.join(testVm.directory, "made-to-order-os-install.iso"))
            # some necessary choices pointed out
            # 32-bit versus 64-bit Linux, memsizeMegabytes needs to be more for 64-bit
            if arch == Arch(32):
                guestOS = "centos"
            elif arch == Arch(64):
                guestOS = "centos-64"
            testVm.create(memsizeMegabytes=vmIdentifiers.mapas.memsize,
                          guestOS=guestOS,
                          ideDrives=[20000, 300, modifiedDistroIsoImage])
            testVm.portsFile.setSsh(ipaddress=vmIdentifiers.ipaddress, user="root", pwd=rootpw)
            testVm.portsFile.setShutdown()
            for additionalUser in additionalUsers:
                testVm.portsFile.setSsh(ipaddress=vmIdentifiers.ipaddress,
                                        user=additionalUser.username,
                                        pwd=additionalUser.pwd)
            testVm.portsFile.setRegularUser(regularUser.username)
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
            testVm.sshCommand([ElGnome.elCommandToEnableAutoLogin(regularUser.username)])
            testVm.sshCommand([ElGnome.elCommandToDisableScreenSaver()], user=regularUser.username)
            # avoid distracting backgrounds, picks unique color to be clear this is a test machine
            testVm.sshCommand([ElGnome.elCommandToSetSolidColorBackground("#dddd66")], user=regularUser.username)
            testVm.sshCommand([ElGnome.elCommandToDisableUpdateNotifications()], user=regularUser.username)
            #
            # might as well
            testVm.sshCommand([LinuxUtil.commandToEnableSudo(regularUser.username)])
            #
            # shut down
            testVm.shutdownCommand()
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
            # start up until successful login into GUI
            VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
            userSshParameters = testVm.sshParameters(user=regularUser.username)
            LinuxSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
            #
            testVm.sshCommand([ElGnome.elCommandToAddSystemMonitorPanel()], user=regularUser.username)
            #
            # shut down for snapshot
            testVm.shutdownCommand()
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        elif distro == "ub":
            if arch == Arch(32):
                downloadedDistroIsoImage = UbIsoImage(Download.fromUrl(ubuntuDistro32IsoUrl))
            elif arch == Arch(64):
                downloadedDistroIsoImage = UbIsoImage(Download.fromUrl(ubuntuDistro64IsoUrl))
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
            kickstartFileContent.ubSetUser(regularUser.username, pwd=regularUser.pwd, fullname=regularUser.fullname)
            kickstartFileContent.setSwappiness(10)
            # pick right temporary directory, ideally same as VM
            modifiedDistroIsoImage = downloadedDistroIsoImage.cloneWithAutoBootingKickstart \
                (kickstartFileContent,
                 cloneIsoImagePath=os.path.join(testVm.directory, "made-to-order-os-install.iso"))
            # some necessary choices pointed out
            # 32-bit versus 64-bit Linux, memsizeMegabytes needs to be more for 64-bit
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
                                    user=regularUser.username,
                                    pwd=regularUser.pwd)
            testVm.portsFile.setRegularUser(regularUser.username)
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
            testVm.sshCommand([UbGnome.ubCommandToEnableAutoLogin(regularUser.username)])
            #
            # might as well
            testVm.sshCommand([LinuxUtil.commandToEnableSudo(regularUser.username)])
            #
            # shut down
            testVm.shutdownCommand()
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
            # start up until successful login into GUI
            VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
            userSshParameters = testVm.sshParameters(user=regularUser.username)
            LinuxSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
            #
            testVm.sshCommand([UbGnome.ubCommandToDisableScreenSaver()], user=regularUser.username)
            # avoid distracting backgrounds, picks unique color to be clear this is a test machine
            testVm.sshCommand([UbGnome.ubCommandToSetSolidColorBackground("#dddd66")], user=regularUser.username)
            testVm.sshCommand([UbGnome.ubCommandToAddSystemMonitorPanel()], user=regularUser.username)
            #
            # shut down for snapshot
            testVm.shutdownCommand()
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
        elif distro == "win":
            if arch == Arch(32):
                downloadedDistroIsoImage = Win7UdfImage(Download.fromUrl(windows7ProInstaller32EnIsoUrl))
            elif arch == Arch(64):
                downloadedDistroIsoImage = Win7UdfImage(Download.fromUrl(windows7ProInstaller64EnIsoUrl))
            # some necessary choices pointed out
            # 32-bit versus 64-bit windows, memsizeMegabytes needs to be more for 64-bit
            if arch == Arch(32):
                guestOS = "windows7"
            elif arch == Arch(64):
                guestOS = "windows7-64"
            testVm.create(memsizeMegabytes=vmIdentifiers.mapas.memsize,
                          guestOS=guestOS,
                          ideDrives=[20000]) #, modifiedDistroIsoImage])
            # some possible choices pointed out
            #testVm.vmxFile.setNumberOfProcessors(2)
            #testVm.vmxFile.setAccelerate3D()
            cygServerRandomPwd = ''.join(random.choice(string.letters) for i in xrange(20))
            # were considering doing  ssh-host-config --yes --pwd $( openssl rand -hex 16 )
            # and intentionally not knowing how to log in as user cyg_server;
            # but even knowing pwd apparently we cannot log in via ssh, hence for now we do not
            #testVm.portsFile.setSsh(ipaddress=vmIdentifiers.ipaddress, user="cyg_server", pwd=cygServerRandomPwd)
            # hence we do not
            #testVm.portsFile.setShutdown(command="shutdown -h now", user="cyg_server")
            # instead do something that works
            #
            # important to know difference in Cygwin between PATH when logged in via ssh interactively,
            # in which case Cygwin directories such as /usr/local/bin and /usr/bin come first,
            # versus sending a command via ssh command line,
            # in which case it is Windows system directories only,
            # also see http://cygwin.com/ml/cygwin/2005-05/msg00012.html ,
            # which you can verify by remotely viewing
            #   ssh -l tester 10.123.45.67 echo \$PATH
            # hence this shutdown command invokes the Windows shutdown command
            testVm.portsFile.setShutdown(command="shutdown -s -t 20", user=regularUser.username)
            for additionalUser in additionalUsers:
                testVm.portsFile.setSsh(ipaddress=vmIdentifiers.ipaddress,
                                        user=additionalUser.username,
                                        pwd=additionalUser.pwd)
            testVm.portsFile.setRegularUser(regularUser.username)
            # NAT works well if before hostonly
            testVm.vmxFile.setEthernetAdapter(0, "nat")
            testVm.vmxFile.setEthernetAdapter(1, "hostonly")
            # generated MAC addresses are available only after first start of a virtual machine
            VMwareHypervisor.local.startAndStopWithIdeDrivesDisabled(testVm.vmxFilePath, gui=True)
            ethernetAdapter0MacAddress = testVm.vmxFile.getEthernetMacAddress(0)
            ethernetAdapter1MacAddress = testVm.vmxFile.getEthernetMacAddress(1)
            # autounattend file content
            autounattendFileContent = Win7AutounattendFileContent(Win7AutounattendTemplates.usableWin7AutounattendTemplate001)
            if arch == Arch(32):
                autounattendFileContent.adjustFor32Bit()
            elif arch == Arch(64):
                autounattendFileContent.adjustFor64Bit()
            autounattendFileContent.replaceLanguageAndLocale(vmIdentifiers.mapas.lang)
            autounattendFileContent.replaceAdminPw(rootpw)
            autounattendFileContent.replaceComputerName(testVm.basenameStem)
            # a network interface with static configuration
            autounattendFileContent.addNetworkConfigurationStatic(mac=ethernetAdapter1MacAddress,
                                                                  ipaddress=vmIdentifiers.ipaddress,
                                                                  limitRoutingToLocalByNetmask=True)
            # simplified use of acceptEula
            autounattendFileContent.acceptEula(fullname=regularUser.fullname, organization=regularUser.organization)
            for additionalUser in additionalUsers:
                autounattendFileContent.addLocalAccount(username=additionalUser.username,
                                                        pwd=additionalUser.pwd,
                                                        fullname=additionalUser.fullname,
                                                        groups=["Administrators"])
            autounattendFileContent.enableAutoLogon(regularUser.username, regularUser.pwd)
            # additional modifications
            modifications = []
            customDirectoryPathOnIso = "custom"
            #
            # shutdown only while installer disk is present
            shutdownRandomScriptName = ''.join(random.choice(string.letters) for i in xrange(8))
            shutdownScriptPathOnIso = os.path.join(customDirectoryPathOnIso, shutdownRandomScriptName + ".bat")
            modifications.extend([
                # an intentionally transient shutdown script
                IsoImageModificationFromString
                (shutdownScriptPathOnIso,
                 r'shutdown -s -t 20 -c "Running shutdown script ' + shutdownScriptPathOnIso +
                 r' intended as part of installation process."'),
                ])
            shutdownScriptPathForCommandLine = shutdownScriptPathOnIso.replace("/", "\\")
            shutdownScriptInvocationCommandLine = \
                ntpath.join("D:\\", shutdownScriptPathForCommandLine)
            autounattendFileContent.addLogonCommand(order=490,
                                                    commandLine=shutdownScriptInvocationCommandLine,
                                                    description="Shutdown - intentionally transient")
            #
            # locally downloaded Cygwin packages directory
            # see http://www.cygwin.com/install.html
            # see http://www.cygwin.com/faq/faq.html#faq.setup.cli
            cygwinPackagesPathOnHost = CygwinDownload.forArch(arch, CygwinDownload.usablePackageDirs001)
            cygwinPackagesPathOnIso = os.path.join(customDirectoryPathOnIso, os.path.basename(cygwinPackagesPathOnHost))
            cygwinPackagesPathForCommandLine = cygwinPackagesPathOnIso.replace("/", "\\")
            # run Cygwin installer, intentionally only while installer disk is present
            cygwinInstallRandomScriptName = ''.join(random.choice(string.letters) for i in xrange(7))
            cygwinInstallScriptPathOnIso = os.path.join(customDirectoryPathOnIso, cygwinInstallRandomScriptName + ".bat")
            # Cygwin installer
            cygwinInstallCommandLine = \
                ntpath.join("D:\\", cygwinPackagesPathForCommandLine, CygwinDownload.installerName(arch)) + \
                r" --local-install" + \
                r" --local-package-dir " + ntpath.join("D:\\", cygwinPackagesPathForCommandLine) + \
                r" --root C:\cygwin" + \
                r" --quiet-mode" + \
                r" --no-desktop" + \
                r" --packages " + CygwinDownload.usablePackageList001
            # ssh-host-config
            cygwinSshdConfigCommandLine = \
                r"C:\cygwin\bin\bash --login -c " '"' + \
                r"ssh-host-config --yes --pwd " + cygServerRandomPwd + \
                '"'
            # in /etc/sshd_config set MaxAuthTries 2, minimum to get prompted, less than default 6
            cygwinSshdFixUpConfigCommandLine = \
                r"C:\cygwin\bin\bash --login -c " '"' + \
                r"( sed -i -e 's/.*MaxAuthTries\s.*/MaxAuthTries 2/g' /etc/sshd_config )" + \
                '"'
            # allow incoming ssh
            openFirewallForSshdCommandLine = \
                r"C:\cygwin\bin\bash --login -c " '"' + \
                r"if ! netsh advfirewall firewall show rule name=SSHD ; then " + \
                r"netsh advfirewall firewall add rule name=SSHD dir=in action=allow protocol=tcp localport=22" + \
                r" ; fi" + \
                '"'
            # start service
            startSshdCommandLine = \
                "net start sshd"
            modifications.extend([
                # the Cygwin packages
                IsoImageModificationFromPath(cygwinPackagesPathOnIso, cygwinPackagesPathOnHost),
                # an intentionally transient install script;
                # also pre-makes /etc/setup directory to prevent subtle setup defects,
                # those defects being caused by not writing files which will be needed to rebase;
                # also rebaseall in those defective circumstances could not help against:
                # sshd child_info_fork::abort cygwrap-0.dll Loaded to different address,
                # and that command line must use ash, not bash,
                # not doing it for now but would be
                #   r"C:\cygwin\bin\ash -c " '"' r"/bin/rebaseall" + '"'
                IsoImageModificationFromString
                (cygwinInstallScriptPathOnIso,
                 #"mkdir C:\\" + cygwinPackagesPathForCommandLine + "\n" + \
                 #"xcopy D:\\" + cygwinPackagesPathForCommandLine + " C:\\" + cygwinPackagesPathForCommandLine + " /S /E" + "\n" + \
                 "mkdir C:\\cygwin\\etc\\setup\n" + \
                 cygwinInstallCommandLine + "\n" + \
                 cygwinSshdConfigCommandLine + "\n" + \
                 cygwinSshdFixUpConfigCommandLine + "\n" + \
                 openFirewallForSshdCommandLine + "\n" + \
                 startSshdCommandLine),
                ])
            cygwinInstallScriptPathForCommandLine = cygwinInstallScriptPathOnIso.replace("/", "\\")
            cygwinInstallScriptInvocationCommandLine = \
                ntpath.join("D:\\", cygwinInstallScriptPathForCommandLine)
            autounattendFileContent.addFirstLogonCommand(order=400,
                                                         commandLine=cygwinInstallScriptInvocationCommandLine,
                                                         description="Install Cygwin - intentionally transient")
            #
            # a detached instance of screen (per logged in user) to be able to start GUI programs from ssh,
            # basic idea from http://superuser.com/questions/531787/starting-windows-gui-program-in-windows-through-cygwin-sshd-from-ssh-client
            # and then needed more exploration and experimentation;
            # also to expand variable out of registry before command line gets it,
            # first must get % into registry value,
            # see http://stackoverflow.com/questions/3620388/how-to-use-reg-expand-sz-from-the-commandline
            runDetachedScreenRegistryValueCommandLine = \
                r"""cmd.exe /c reg.exe add HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run """ + \
                r"""/v CygwinScreen /t REG_EXPAND_SZ """ + \
                r"""/d "C:\cygwin\bin\bash.exe --login -c 'screen -wipe ; screen -d -m -S for_"^%USERNAME^%"'" """ + \
                r"""/f"""
            autounattendFileContent.addFirstLogonCommand(order=401,
                                                         commandLine=runDetachedScreenRegistryValueCommandLine,
                                                         description="Add registry value for running detached screen")
            #
            # various
            disableIExplorerFirstRunWizardCommandLine = \
                r"""reg.exe add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Internet Explorer\Main" """ + \
                r"""/v DisableFirstRunCustomize /t REG_DWORD /d 1 /f"""
            autounattendFileContent.addFirstLogonCommand(order=410,
                                                         commandLine=disableIExplorerFirstRunWizardCommandLine,
                                                         description="Disable Internet Explorer first run wizard")
            #
            # pick right temporary directory, ideally same as VM
            modifiedDistroIsoImage = downloadedDistroIsoImage.cloneWithAutounattend \
                (autounattendFileContent,
                 modifications=modifications,
                 cloneIsoImagePath=os.path.join(testVm.directory, "made-to-order-os-install.iso"))
            # set CD-ROM .iso file, which had been kept out intentionally for first start for generating MAC addresses
            testVm.vmxFile.setIdeCdromIsoFile(modifiedDistroIsoImage.isoImagePath, 1, 0)
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
    if distro == "el" or distro == "ub":
        rootOrAnAdministrator = "root"
    elif distro == "win":
        rootOrAnAdministrator = testVm.regularUser
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
        if distro == "el" or distro == "ub":
            LinuxSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
        elif distro == "win":
            CygwinSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
        #
        # a necessity on some international version OS
        testVm.sshCommand(["mkdir -p ~/Downloads"], user=testVm.regularUser)
        if distro == "win":
            testVm.sshCommand(['mkdir -p "$( cygpath -u "$USERPROFILE/Downloads" )"'], user=testVm.regularUser)
            echo = testVm.sshCommand(['echo "$( cygpath -u "$USERPROFILE/Downloads" )"'], user=testVm.regularUser)
            windowsUserDownloadDirCygwinPath = echo.output.strip()
            echo = testVm.sshCommand([r"cmd.exe /C 'echo %USERPROFILE%\Downloads'"], user=testVm.regularUser)
            windowsUserDownloadDirWindowsPath = echo.output.strip()
        # for symmetry and comprehensibility
        testVm.sshCommand(["mkdir -p ~/Downloads"], user=rootOrAnAdministrator)
        #
        # install Java
        if distro == "win":
            # Java for Windows
            javawInstallerOnHostPath = JavawDownload.now()
            javawInstallerBasename = os.path.basename(javawInstallerOnHostPath)
            javawInstallerOnGuestCygwinPath = posixpath.join(windowsUserDownloadDirCygwinPath, javawInstallerBasename)
            javawInstallerOnGuestWindowsPath = ntpath.join(windowsUserDownloadDirWindowsPath, javawInstallerBasename)
            testVm.scpPutCommand(fromHostPath=javawInstallerOnHostPath,
                                 toGuestPath=javawInstallerOnGuestCygwinPath,
                                 guestUser=testVm.regularUser)
            # run installer
            testVm.sshCommand(["chmod +x " + javawInstallerOnGuestCygwinPath],
                              user=testVm.regularUser)
            # see http://java.com/en/download/help/silent_install.xml
            # also, tolerate like Error opening file C:\Users\tester\AppData\LocalLow\Sun\Java\jre1.7.0_45\Java3BillDevices.jpg
            # also, tolerate Error: 2
            # also, work around Java for Windows installer program despite success not exiting if invoked this way
            testVm.sshCommand(["( nohup cmd.exe /C '" + javawInstallerOnGuestWindowsPath
                               + " /s /L " + javawInstallerOnGuestWindowsPath + ".log' &> /dev/null & )"],
                              user=testVm.regularUser,
                              exceptionIfNotZero=False)
            waitingForJavawInstallerSuccess = True
            while waitingForJavawInstallerSuccess:
                time.sleep(5.0)
                javaVersion = testVm.sshCommand(
                    ["java -version"],
                    user=testVm.regularUser,
                    exceptionIfNotZero=False)
                if not javaVersion.returncode:
                    waitingForJavawInstallerSuccess = False
            #
            # Python for Windows
            if arch == Arch(32):
                python2xWindowsInstallerMsiUrl = python2xWindows32InstallerMsiUrl
            elif arch == Arch(64):
                python2xWindowsInstallerMsiUrl = python2xWindows64InstallerMsiUrl
            pythonInstallerOnHostPath = Download.fromUrl(python2xWindowsInstallerMsiUrl)
            pythonInstallerBasename = os.path.basename(pythonInstallerOnHostPath)
            pythonInstallerOnGuestCygwinPath = posixpath.join(windowsUserDownloadDirCygwinPath, pythonInstallerBasename)
            pythonInstallerOnGuestWindowsPath = ntpath.join(windowsUserDownloadDirWindowsPath, pythonInstallerBasename)
            testVm.scpPutCommand(fromHostPath=pythonInstallerOnHostPath,
                                 toGuestPath=pythonInstallerOnGuestCygwinPath,
                                 guestUser=testVm.regularUser)
            # run installer
            # see http://www.python.org/download/releases/2.4/msi/
            testVm.sshCommand(["cmd.exe /C 'msiexec.exe /i " + pythonInstallerOnGuestWindowsPath
                               + " ALLUSERS=1 /qb! /log " + pythonInstallerOnGuestWindowsPath + ".log'"],
                              user=testVm.regularUser)
            # add to PATH for system
            # Cygwin regtool syntax see http://cygwin.com/cygwin-ug-net/using-utils.html
            machineWidePathRegistryKeyValue = "/HKEY_LOCAL_MACHINE/SYSTEM/CurrentControlSet/Control/Session Manager/Environment/Path"
            # assuming python.exe is in C:\Python27 or so
            testVm.sshCommand(['PYDIR="$( cygpath -w "$( echo /cygdrive/c/Py* )" )"'
                               + ' && '
                               + 'regtool --wow64 --expand-string set "' + machineWidePathRegistryKeyValue
                               + '" "$( regtool --wow64 get "' + machineWidePathRegistryKeyValue + '" );$PYDIR"'],
                              user=testVm.regularUser)
            # must restart for change of PATH to be effective
            # shut down
            testVm.shutdownCommand()
            VMwareHypervisor.local.sleepUntilNotRunning(testVm.vmxFilePath, ticker=True)
            # start up until successful login into GUI
            VMwareHypervisor.local.start(testVm.vmxFilePath, gui=True, extraSleepSeconds=0)
            CygwinSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
        #
        # install Google Chrome
        if browser == "chrome" and distro == "ub":
            if arch == Arch(32):
                googleChromeUbuntuInstallerUrl = googleChromeUbuntu32InstallerUrl
            elif arch == Arch(64):
                googleChromeUbuntuInstallerUrl = googleChromeUbuntu64InstallerUrl
            chromeInstallerOnHostPath = Download.fromUrl(googleChromeUbuntuInstallerUrl)
            chromeInstallerOnGuestPath = posixpath.join("~/Downloads", Download.basename(googleChromeUbuntuInstallerUrl))
            testVm.scpPutCommand(fromHostPath=chromeInstallerOnHostPath,
                                 toGuestPath=chromeInstallerOnGuestPath,
                                 guestUser="root")
            # install
            testVm.sshCommand(["cd ~/Downloads"
                               + " && dpkg -i " + chromeInstallerOnGuestPath],
                              user="root")
            # run once, wait, terminate
            testVm.sshCommand(["export DISPLAY=:0.0 ; "
                               + "( nohup"
                               + " google-chrome --cancel-first-run --no-default-browser-check about:blank"
                               + " &> /dev/null & )"
                               + " && sleep 5"
                               + " && kill $( pidof chrome )"],
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
            chromeDriverInstallerZipOnHostPath = Download.fromUrl(chromeDriverLinuxInstallerZipUrl)
            chromeDriverInstallerZipBaseName = Download.basename(chromeDriverLinuxInstallerZipUrl)
            chromeDriverInstallerZipOnGuestPath = posixpath.join("~/Downloads", chromeDriverInstallerZipBaseName)
            testVm.scpPutCommand(fromHostPath=chromeDriverInstallerZipOnHostPath,
                                 toGuestPath=chromeDriverInstallerZipOnGuestPath,
                                 guestUser=rootOrAnAdministrator)
            chromeDriverInstallerExtracted = re.match(r"^(\S+)(?:\.zip)$", chromeDriverInstallerZipBaseName).group(1)
            chromeDriverInstallerExtractedPath = posixpath.join("~/Downloads", chromeDriverInstallerExtracted)
            # unzip and copy to where it is on PATH
            testVm.sshCommand(["cd ~/Downloads"
                               + " && unzip -o " + chromeDriverInstallerZipOnGuestPath + " -d " + chromeDriverInstallerExtractedPath
                               + " && chmod +x " + chromeDriverInstallerExtractedPath + "/chromedriver"
                               + " && cp " + chromeDriverInstallerExtractedPath + "/chromedriver /usr/local/bin"],
                              user=rootOrAnAdministrator)
        #
        if browser == "iexplorer":
            # install IeDriver
            # see http://code.google.com/p/selenium/wiki/InternetExplorerDriver
            if arch == Arch(32):
                seleniumIeDriverServerZipUrl = seleniumIeDriverServer32ZipUrl
            elif arch == Arch(64):
                seleniumIeDriverServerZipUrl = seleniumIeDriverServer64ZipUrl
            seleniumIeDriverServerZipOnHostPath = Download.fromUrl(seleniumIeDriverServerZipUrl)
            seleniumIeDriverServerZipBaseName = Download.basename(seleniumIeDriverServerZipUrl)
            seleniumIeDriverServerZipOnGuestPath = posixpath.join("~/Downloads", seleniumIeDriverServerZipBaseName)
            testVm.scpPutCommand(fromHostPath=seleniumIeDriverServerZipOnHostPath,
                                 toGuestPath=seleniumIeDriverServerZipOnGuestPath,
                                 guestUser=rootOrAnAdministrator)
            seleniumIeDriverServerExtracted = re.match(r"^(\S+)(?:\.zip)$", seleniumIeDriverServerZipBaseName).group(1)
            seleniumIeDriverServerExtractedPath = posixpath.join("~/Downloads", seleniumIeDriverServerExtracted)
            # unzip and copy to where it is on PATH, e.g. /cygdrive/c/Windows/system32
            testVm.sshCommand(["cd ~/Downloads"
                               + " && unzip -o " + seleniumIeDriverServerZipOnGuestPath + " -d " + seleniumIeDriverServerExtractedPath
                               + " && chmod +x " + seleniumIeDriverServerExtractedPath + "/IEDriverServer.exe"
                               + " && cp " + seleniumIeDriverServerExtractedPath + "/IEDriverServer.exe"
                               + " `echo $PATH | grep -o -i '/cyg[^:]*Win[^:]*' | grep -m1 ''`"],
                              user=rootOrAnAdministrator)
        #
        # install Python bindings
        if distro == "win":
            # first an auxiliary tool
            pythonSetuptoolsTarOnHostPath = Download.fromUrl(pythonSetuptoolsTarUrl)
            pythonSetuptoolsTarBaseName = Download.basename(pythonSetuptoolsTarUrl)
            pythonSetuptoolsTarOnGuestPath = posixpath.join("~/Downloads", pythonSetuptoolsTarBaseName)
            testVm.scpPutCommand(fromHostPath=pythonSetuptoolsTarOnHostPath,
                                 toGuestPath=pythonSetuptoolsTarOnGuestPath,
                                 guestUser=rootOrAnAdministrator)
            pythonSetuptoolsExtracted = re.match(r"^(\S+)(?:\.tar\.gz)$", pythonSetuptoolsTarBaseName).group(1)
            testVm.sshCommand(["cd ~/Downloads"
                               + " && tar -xf " + pythonSetuptoolsTarOnGuestPath
                               + " && cd " + pythonSetuptoolsExtracted + "/"
                               + " && chmod +x setup.py"
                               + " && python ./setup.py install"],
                              user=rootOrAnAdministrator)
        seleniumPythonBindingsTarOnHostPath = Download.fromUrl(seleniumPythonBindingsTarUrl)
        seleniumPythonBindingsTarBaseName = Download.basename(seleniumPythonBindingsTarUrl)
        seleniumPythonBindingsTarOnGuestPath = posixpath.join("~/Downloads", seleniumPythonBindingsTarBaseName)
        testVm.scpPutCommand(fromHostPath=seleniumPythonBindingsTarOnHostPath,
                             toGuestPath=seleniumPythonBindingsTarOnGuestPath,
                             guestUser=rootOrAnAdministrator)
        seleniumPythonBindingsExtracted = re.match(r"^(\S+)(?:\.tar\.gz)$", seleniumPythonBindingsTarBaseName).group(1)
        testVm.sshCommand(["cd ~/Downloads"
                           + " && tar -xf " + seleniumPythonBindingsTarOnGuestPath
                           + " && cd " + seleniumPythonBindingsExtracted + "/"
                           + " && chmod +x setup.py"
                           + " && python ./setup.py install"],
                          user=rootOrAnAdministrator)
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
        if distro == "el" or distro == "ub":
            LinuxSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
        elif distro == "win":
            CygwinSshCommand.sleepUntilIsGuiAvailable(userSshParameters, ticker=True)
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
        elif browser == "iexplorer":
            # switch from webdriver.Firefox() to webdriver.Ie()
            testVm.sshCommand(["sed -i -e 's/webdriver\.Firefox/webdriver.Ie/'"
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
        if distro == "el" or distro == "ub":
            testVm.sshCommand(["export DISPLAY=:0.0 ; "
                               + "cd ~/Downloads/"
                               + " && chmod +x " + testsInvokerScript
                               + " && chmod +x " + testsDirectory + "/*.py"
                               + " && ( nohup python ./" + testsInvokerScript + " &> ./" + testsInvokerScript + ".log & )"],
                              user=testVm.regularUser)
        elif distro == "win":
            testVm.sshCommand(["screen -wipe ; screen -S for_$USERNAME -X stuff '"
                               + "cd ~/Downloads/"
                               + " && chmod +x " + testsInvokerScript
                               + " && chmod +x " + testsDirectory + "/*.py"
                               + " && ( nohup python ./" + testsInvokerScript + " &> ./" + testsInvokerScript + ".log & )\n'"],
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
