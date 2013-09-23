#!/usr/bin/python

"""nrvr.vm.vmware - Create and manipulate VMware virtual machines

Classes provided by this module include
* VmdkFile
* VmxFileContent
* VmxFile
* VMwareHypervisor
* VMwareMachine

The file path of the .vmx file is used as identifier,
which seems reasonably consistent with VMware APIs.
What really is used is the normalized, absolutized, possibly expanded::

    os.path.abspath(os.path.expanduser(vmxFilePath))

Files related to a machine are essentially expected to be in the same directory.

The purpose is automation.
The purpose isn't to support all features of the hypervisor.
As implemented only known to support VMware Workstation 9, VMware Player 5, and VMware Fusion 5.
As implemented requires vmrun, which is known to be available when installing VMware VIX 1.12.
As implemented only tested with VMware Workstation 9.0.2, VMware Player 5.0.2, VIX 1.12.2, and VMware Fusion 5.0.3.
Should work with newer versions VMware Workstation, VMware Player, and VIX.
Other hypervisors may be added as needed.

As implemented works in Linux.
As implemented requires vmrun, and vmware-vdiskmanager or qemu-img commands.
Nevertheless essential.  To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import codecs
import os.path
import re
import shutil
import sys
import tempfile
import time

from nrvr.diskimage.isoimage import IsoImage
from nrvr.machine.ports import PortsFile
from nrvr.process.commandcapture import CommandCapture
from nrvr.remote.ssh import SshParameters, SshCommand, ScpCommand
from nrvr.util.classproperty import classproperty
from nrvr.util.networkinterface import NetworkInterface
from nrvr.util.requirements import SystemRequirements
from nrvr.util.times import Timestamp
from nrvr.util.user import ScriptUser
from nrvr.vm.vmwaretemplates import VMwareTemplates

class VmdkFile(object):
    """A .vmdk file for VMware."""

    @classmethod
    def commandsUsedInImplementation(cls):
        """Return a list to be passed to SystemRequirements.commandsRequired().
        
        This class can be passed to SystemRequirements.commandsRequiredByImplementations()."""
        return [(["vmware-vdiskmanager"], ["qemu-img"])]

    def __init__(self, vmdkFilePath):
        """Create new .vmdk file descriptor.
        
        A descriptor can describe a .vmdk file that does or doesn't yet exist on the host disk."""
        object.__init__(self)
        # really want abspath and expanduser
        self._vmdkFilePath = os.path.abspath(os.path.expanduser(vmdkFilePath))
        # sanity check filename extension
        extension = os.path.splitext(os.path.basename(self._vmdkFilePath))[1]
        if extension != ".vmdk":
            raise Exception("won't accept .vmdk filename not ending in .vmdk: {0}".format(self._vmdkFilePath))

    @property
    def vmdkFilePath(self):
        """Path of the .vmdk file."""
        return self._vmdkFilePath

    def compliantDiskSize(self, megabytes=1000):
        """Disk size must be a multiple of 4.
        
        If necessary rounds up to next multiple of 4.
        
        Is megabytes."""
        megabytes = long(megabytes)
        if megabytes % 4 == 0:
            return megabytes
        else:
            # round up
            return (megabytes / 4 + 1) * 4

    def exists(self):
        """Return True if file exists on the host disk."""
        return os.path.exists(self._vmdkFilePath)

    def create(self, megabytes=1000, preallocated=False):
        """Create a .vmdk file.
        
        As implemented only supports a limited number of features.
        Nevertheless essential.  To be improved as needed."""
        if self.exists():
            raise Exception("won't overwrite already existing {0}".format(self._vmdkFilePath))
        megabytes = self.compliantDiskSize(megabytes)
        if SystemRequirements.which("vmware-vdiskmanager"):
            # see vmware-vdiskmanager --help
            #
            # note: since VMware Workstation 10, vmware-vdiskmanager build 1295980
            # stderr output has been observed reading
            #   VixDiskLib: Invalid configuration file parameter.  Failed to read configuration file.
            # while at the same time stdout ends with a line
            #   Virtual disk creation successful.
            # and returncode is 0,
            # hence we are detecting and tolerating that specific stderr content, but no other
            creationCommand = CommandCapture(
                ["vmware-vdiskmanager",
                 "-c", # create
                 "-a", "ide",
                 "-s", "{0:d}MB".format(megabytes),
                 "-t", "0" if not preallocated else "2", # 0 growable, 2 preallocated
                 self._vmdkFilePath],
                exceptionIfAnyStderr=False)
            # BEGIN workaround
            looksOk = False
            creationCommandStderr = creationCommand.stderr
            creationCommandStdout = creationCommand.stdout
            if creationCommandStderr:
                if re.match(
                    r"(?si)^\s*VixDiskLib:\s+Invalid\s+configuration\s+file\s+parameter.\s+Failed\s+to\s+read\s+configuration\s+file.\s*$",
                    creationCommandStderr): # expected
                    if re.match(
                        r"(?si)^.*Virtual\s+disk\s+creation\s+successful.\s*$",
                        creationCommandStdout): # expected
                        looksOk = True
                    else: # unexpected other text in stdout
                        looksOk = False
                else: # unexpected other text in stderr
                    looksOk = False
            else: # not any text in stderr is expected
                looksOk = True
            if not looksOk:
                creationCommand.raiseExceptionIfThereIsAReason()
            # END workaround
        else:
            warning = "Warning: lacking vmware-vdiskmanager, using qemu-img for creating " + self._vmdkFilePath
            if preallocated:
                warning += ", therefore CANNOT make preallocated"
            print warning
            # see man qemu-img
            CommandCapture(
                ["qemu-img",
                 "create",
                 "-f", "vmdk",
                 "-o", "compat6", # .vmdk version 6 instead of older 4
                 self._vmdkFilePath,
                 "{0:d}M".format(megabytes)])

if __name__ == "__main__":
    SystemRequirements.commandsRequiredByImplementations([VmdkFile], verbose=True)
    #
    _testDir = os.path.join(tempfile.gettempdir(), Timestamp.microsecondTimestamp())
    os.mkdir(_testDir, 0755)
    try:
        _vmdkFile1 = VmdkFile(os.path.join(_testDir, "test1.vmdk"))
        _vmdkFile1.create(4000)
        _vmdkFile2 = VmdkFile(os.path.join(_testDir, "test2.vmdk"))
        _vmdkFile2.create(4, preallocated=True)
    finally:
        shutil.rmtree(_testDir)


class VmxFileContent(object):
    """The text content of a .vmx file for VMware.
    
    VMware describes the .vmx file as the primary configuration file."""

    def __init__(self, string):
        """Create new .vmx file content container.
        
        Does unicode(string), as befits the 21st century."""
        self.string = unicode(string)
        self._newline = None # determine on demand

    @classmethod
    def compliantMemsize(cls, given):
        """.vmx file parameter memsize must be a multiple of 4.
        
        If necessary rounds up to next multiple of 4.
        
        Unit is megabytes."""
        given = long(given)
        if given % 4 == 0:
            return given
        else:
            # round up
            return (given / 4 + 1) * 4

    @classmethod
    def ideBusDevice(cls, driveNumber):
        """Return IDE bus 0 or 1 device 0 or 1 for IDE drive number 0, 1, 2 or 3.
        
        Return e.g. (0,0)."""
        driveNumber = int(driveNumber)
        if driveNumber < 0 or driveNumber > 4:
            raise Exception("IDE drive number must be 0 to 3, cannot be {0}".format(driveNumber))
        return driveNumber / 2, driveNumber % 2

    @classmethod
    def ideDriveNumber(cls, bus, device):
        """For IDE bus 0 or 1 device 0 or 1 return IDE drive number 0, 1, 2 or 3.
        
        Return e.g. 0."""
        bus = int(bus)
        if bus < 0 or bus > 1:
            raise Exception("IDE bus must be 0 or 1, cannot be {0}".format(bus))
        device = int(device)
        if device < 0 or device > 1:
            raise Exception("IDE device must be 0 or 1, cannot be {0}".format(device))
        return bus * 2 + device

    def replaceSettingValue(self, name, newValue, placeholder=None):
        """Replace one setting value.
        
        Tolerates string or number for newValue because it does unicode(newValue).
        
        As implemented would have problems with backslash escapes in newValue.
        Don't use \ in newValue.
        
        E.g. if original containts a line::
        
            memsize="_MEMSIZE_" # megabytes, must be multiple of 4
        
        then would call::
        
            vmxFile.replaceSettingValue("memsize", 256, "_MEMSIZE_")"""
        # (?m) effects MULTILINE, which is used for ^
        patternString = r'(?m)^[ \t]*(_NAME_)([ \t]*=[ \t]*)"?[ \t]*_PLACEHOLDER_[ \t]*"?'
        # make pattern match actual setting name,
        # tolerate regular expression metacharacters
        patternString = re.sub(r"_NAME_", re.escape(name), patternString)
        if placeholder:
            # make pattern match actual placeholder for setting value,
            # tolerate regular expression metacharacters
            patternString = re.sub(r"_PLACEHOLDER_", re.escape(placeholder), patternString)
        else:
            # anything as placeholder for setting value
            patternString = re.sub(r"_PLACEHOLDER_", r'[^"]*', patternString)
        # tolerate various newValue, e.g. string or number
        replacementString = r'\g<1>\g<2>"' + unicode(newValue) + r'"'
        # actual replacement
        modifiedSettings = re.sub(patternString, replacementString, self.string)
        # here an opportunity to compare in debugger
        self.string = modifiedSettings

    def setSettingValue(self, name, newValue, extraEmptyLine=False):
        """Replace one setting value or create and append that setting.
        
        See method replaceSettingValue."""
        # (?m) effects MULTILINE, which is used for ^
        patternString = r'(?m)^[ \t]*name[ \t]*=.*'
        # make pattern match actual setting name,
        # tolerate regular expression metacharacters
        patternString = re.sub(r"name", re.escape(name), patternString)
        if re.search(patternString, self.string):
            # if an existing setting then replace
            return self.replaceSettingValue(name, newValue)
        # tolerate various newValue, e.g. string or number
        newSettingLine = name + '="' + unicode(newValue) + '"'
        # make sure there is exactly one newline at the end before appending
        modifiedSettings = re.sub(r"(\r?\n)*$", self.newline, self.string)
        if extraEmptyLine:
            # one extra newline
            modifiedSettings += self.newline
        # append
        modifiedSettings += newSettingLine
        # here an opportunity to compare in debugger
        self.string = modifiedSettings
        self.normalizeLineRuns()

    def removeSetting(self, name):
        """Remove a setting."""
        # (?m) effects MULTILINE, which is used for ^
        patternString = r'(?m)^[ \t]*name[ \t]*=.*$'
        # make pattern match actual setting name,
        # tolerate regular expression metacharacters
        patternString = re.sub(r"name", re.escape(name), patternString)
        # actual replacement
        modifiedSettings = re.sub(patternString, r"", self.string)
        # here an opportunity to compare in debugger
        self.string = modifiedSettings
        self.normalizeLineRuns()

    def removeSettingsStartingWith(self, prefix):
        """Remove settings having prefix in front of name."""
        # (?m) effects MULTILINE, which is used for ^
        patternString = r'(?m)^[ \t]*prefix[^\s=]*[ \t]*=.*$'
        # make pattern match actual setting prefix,
        # tolerate regular expression metacharacters
        patternString = re.sub(r"prefix", re.escape(prefix), patternString)
        # actual replacement
        modifiedSettings = re.sub(patternString, r"", self.string)
        # here an opportunity to compare in debugger
        self.string = modifiedSettings
        self.normalizeLineRuns()

    newlineRegex = re.compile(r"\r?\n")

    @property
    def newline(self):
        """Sample which kind of newline."""
        if not self._newline:
            newlineMatch = VmxFileContent.newlineRegex.search(self.string)
            if newlineMatch:
                self._newline = newlineMatch.group(0)
            else:
                self._newline = "\r\n"
        return self._newline

    def normalizeLineRuns(self):
        """Normalize empty line runs.
        
        One empty line is made from two newlines.  Reduce any more than two down to two.
        
        At the end make exactly two newlines, so that lines added by VMware will be separated.
        
        Auxiliary."""
        # limit more than two newlines down to two
        modifiedSettings = re.sub(r"(\r?\n\r?\n)(?:\r?\n)+", r"\g<1>", self.string)
        # remove at the end one or more than one newline down to zero
        modifiedSettings = re.sub(r"(\r?\n)(?:\r?\n)*$", r"", modifiedSettings)
        # insert at the end exactly two newlines,
        # the purpose is so that additional lines added by VMware running will be separated,
        # more easily recognizable
        modifiedSettings = modifiedSettings + self.newline * 2
        # here an opportunity to compare in debugger
        self.string = modifiedSettings

    @classmethod
    def ideSettingPrefix(cls, bus=0, device=0):
        """.vmx file parameters for IDE drives have a naming convention.
        
        Return e.g. "ide0:0" for bus=0 and device=0."""
        return "ide" + str(bus) + ":" + str(device)

    def setIdeDrive(self, pathOnHost, deviceType, bus=0, device=0):
        """Set .vmx file parameters for a virtual IDE drive served from a file.
        
        pathOnHost
            can be relative.
        
        E.g.::
        
            ide0:0.present = "TRUE"
            ide0:0.deviceType = "disk"
            ide0:0.fileName = "demomachine01-0.vmdk" """
        bus = int(bus)
        if bus < 0 or bus > 1:
            raise Exception("IDE bus must be 0 or 1, cannot be {0}".format(bus))
        device = int(device)
        if device < 0 or device > 1:
            raise Exception("IDE device must be 0 or 1, cannot be {0}".format(device))
        ideSettingPrefix = self.ideSettingPrefix(bus, device)
        self.setSettingValue(ideSettingPrefix + ".present", "TRUE", extraEmptyLine=True)
        if deviceType:
            self.setSettingValue(ideSettingPrefix + ".deviceType", deviceType)
        self.setSettingValue(ideSettingPrefix + ".fileName", pathOnHost)
    def setIdeDiskVmdkFile(self, pathOnHost, bus=0, device=0):
        """Set .vmx file parameters for a virtual IDE hard disk drive served from a .vmdk disk file."""
        self.setIdeDrive(pathOnHost, "disk", bus, device)
    def setIdeCdromIsoFile(self, pathOnHost, bus=0, device=0):
        """Set .vmx file parameters for a virtual IDE CD-ROM drive served from an .iso image file."""
        self.setIdeDrive(pathOnHost, "cdrom-image", bus, device)
    def removeIdeDrive(self, bus=0, device=0):
        """Remove all .vmx file parameters for a virtual IDE drive."""
        self.removeSettingsStartingWith(self.ideSettingPrefix(bus, device) + ".")
    def removeAllIdeCdromImages(self):
        """Remove all .vmx file parameters for all virtual IDE CD-ROM drives served from image files."""
        foundPrefixes = re.findall(r'(?m)^[ \t]*(ide[0-9]*:[0-9]*)\.deviceType[ \t]*=[ \t]*"?[ \t]*cdrom-image[ \t]*"?',
                                   self.string)
        for foundPrefix in foundPrefixes:
            self.removeSettingsStartingWith(foundPrefix + ".")

    @classmethod
    def ethernetSettingPrefix(cls, adapter=0):
        """.vmx file parameters for Ethernet adapters have a naming convention.
        
        Return e.g. "ethernet0" for adapter=0."""
        return "ethernet" + str(adapter)

    def setEthernetAdapter(self, adapter=0, connectionType="bridged", change="enable"):
        """Set .vmx file parameters for a virtual Ethernet adapter.
        
        connectionType
            "bridged", "hostonly", or "nat".
        
        change
            "enable", "disable", or "remove".
        
        E.g.::
        
            ethernet0.present = "TRUE"
            ethernet0.connectionType = "bridged"
            ethernet0.virtualDev = "e1000"
            ethernet0.startConnected = "TRUE"
            ethernet0.wakeOnPcktRcv = "FALSE"
            ethernet0.allowGuestConnectionControl = "FALSE"
            ethernet0.disableMorphToVmxnet = "TRUE" """
        adapter = int(adapter)
        if adapter < 0 or adapter > 9:
            raise Exception("Ethernet adapter must be a single digit, 0, 1, etc., cannot be {0}".format(adapter))
        ethernetSettingPrefix = self.ethernetSettingPrefix(adapter)
        validConnectionTypes = ["bridged", "hostonly", "nat"]
        if not connectionType in validConnectionTypes:
            raise Exception("Ethernet connectionType must be one of {0}, cannot be {1}".format(validConnectionTypes, connectionType))
        validChanges = ["enable", "disable", "remove"]
        if not change in validChanges:
            raise Exception("Ethernet change must be one of {0}, cannot be {1}".format(validChanges, change))
        if change == "enable":
            self.setSettingValue(ethernetSettingPrefix + ".present", "TRUE", extraEmptyLine=True)
            self.setSettingValue(ethernetSettingPrefix + ".connectionType", connectionType)
            self.setSettingValue(ethernetSettingPrefix + ".virtualDev", "e1000")
            self.setSettingValue(ethernetSettingPrefix + ".startConnected", "TRUE")
            self.setSettingValue(ethernetSettingPrefix + ".wakeOnPcktRcv", "FALSE")
            self.setSettingValue(ethernetSettingPrefix + ".allowGuestConnectionControl", "FALSE")
            self.setSettingValue(ethernetSettingPrefix + ".disableMorphToVmxnet", "TRUE")
        elif change == "disable":
            self.setSettingValue(ethernetSettingPrefix + ".present", "FALSE", extraEmptyLine=True)
        else: # change == "remove"
            self.removeSettingsStartingWith(ethernetSettingPrefix + ".")

if __name__ == "__main__":
    _vmxFileContent1 = VmxFileContent(VMwareTemplates.usableVMwareVmxTemplate001)
    _vmxFileContent1.setIdeDiskVmdkFile("test1-disk0.vmdk", 0, 0)
    _vmxFileContent1.setIdeDiskVmdkFile("test1-disk1.vmdk", 0, 1)
    _vmxFileContent1.removeSetting("vmci0.present")
    _vmxFileContent1.removeSetting("svga.vramSize")
    _vmxFileContent1.removeSetting("usb.present")
    _vmxFileContent1.removeIdeDrive(0, 1)
    _vmxFileContent1.setEthernetAdapter(1, "hostonly")
    _vmxFileContent1.setEthernetAdapter(2, "nat")
    _vmxFileContent1.setEthernetAdapter(3, "nat")
    _vmxFileContent1.setEthernetAdapter(3, change="remove")
    print _vmxFileContent1.string


class VmxFile(object):
    """A .vmx file for VMware."""

    def __init__(self, vmxFilePath):
        """Create new .vmx file descriptor.
        
        A descriptor can describe a .vmx file that does or doesn't yet exist on the host disk."""
        # really want abspath and expanduser
        self._vmxFilePath = os.path.abspath(os.path.expanduser(vmxFilePath))
        # sanity check filename extension
        extension = os.path.splitext(os.path.basename(self._vmxFilePath))[1]
        if extension != ".vmx":
            raise Exception("won't accept .vmx filename not ending in .vmx: {0}".format(self._vmxFilePath))
        self._vmxFileContent = None
        # keep up-to-date
        self._load()

    @property
    def vmxFilePath(self):
        """Path of the .vmx file."""
        return self._vmxFilePath

    def exists(self):
        """Return True if file exists on the host disk."""
        return os.path.exists(self._vmxFilePath)

    @property
    def directory(self):
        """Directory .vmx file is in."""
        return os.path.dirname(self._vmxFilePath)

    @property
    def basenameStem(self):
        """Stem of basename of .vmx file.
        
        Used as default for displayName.
        Useful for making names of related files."""
        return os.path.splitext(os.path.basename(self._vmxFilePath))[0]

    def _load(self):
        """Load content from file into a VmxFileContent instance.
        
        If not self.exists() then does nothing.
        
        Auxiliary."""
        if self.exists():
            # read existing file
            with codecs.open(self._vmxFilePath, "r", encoding="utf-8") as inputFile:
                self._vmxFileContent = VmxFileContent(inputFile.read())

    @property
    def vmxFileContent(self):
        """A VmxFileContent instance.
        
        If not self.exists() may be None.
        
        Auxiliary."""
        return self._vmxFileContent

    def create(self,
               memsizeMegabytes=512,
               guestOS="centos",
               ideDrives=None,
               displayName=None,
               template=VMwareTemplates.usableVMwareVmxTemplate001):
        """Create a .vmx file.
        
        As implemented only supports a limited number of features.
        Nevertheless essential.  To be improved as needed.
        
        ideDrives
            a list of at most four VmdkFile or IsoImage.
            If given a number as an element then make a VmdkFile with that many megabytes capactiy.
            If None then default to one VmdkFile with 20000 megabytes capacity.
        
        displayName
            defaults to self.basenameStem.
        
        template
            a string."""
        if self.exists():
            raise Exception("won't overwrite already existing {0}".format(self._vmxFilePath))
        # start with a template
        vmxFileContent = VmxFileContent(template)
        # replace some settings values
        memsizeMegabytes = VmxFileContent.compliantMemsize(memsizeMegabytes)
        vmxFileContent.replaceSettingValue("memsize", memsizeMegabytes)
        vmxFileContent.replaceSettingValue("guestOS", guestOS)
        #
        if ideDrives is None:
            # default to one hard disk
            ideDrives = [20000]
        if len(ideDrives) > 4:
            raise Exception("cannot have more than 4 IDE drives, cannot have {0}".format(len(ideDrives)))
        # for a number make a hard disk with that many megabytes capactiy
        for index, element in enumerate(ideDrives):
            if isinstance(element, (int, long, float)):
                ideDiskVmdkFile = VmdkFile(os.path.join(self.directory,
                                                        self.basenameStem + "-{0}.vmdk".format(index)))
                ideDiskVmdkFile.create(megabytes=element, preallocated=False)
                ideDrives[index] = ideDiskVmdkFile
        # if given drives then add them
        for index, element in enumerate(ideDrives):
            ideBus, ideDevice = VmxFileContent.ideBusDevice(index)
            if isinstance(element, VmdkFile):
                vmxFileContent.setIdeDiskVmdkFile(element.vmdkFilePath, ideBus, ideDevice)
            elif isinstance(element, IsoImage):
                vmxFileContent.setIdeCdromIsoFile(element.isoImagePath, ideBus, ideDevice)
            else:
                raise Exception("ideDevice must be VmdkFile instance or IsoImage instance"
                                ", won't accept {0}".format(element))
        #
        if not displayName:
            displayName = self.basenameStem
        vmxFileContent.replaceSettingValue("displayName", displayName)
        #
        # consistent encoding
        vmxFileContent.replaceSettingValue(".encoding", "UTF-8")
        # write
        with codecs.open(self._vmxFilePath, "w", encoding="utf-8") as outputFile:
            outputFile.write(vmxFileContent.string)
        # keep up-to-date
        self._load()

    def modify(self, vmxFileContentModifyingMethod):
        """Recommended safe wrapper to modify .vmx file.
        
        May raise exception if .vmx file locally listed as running."""
        # help avoid trouble
        VMwareHypervisor.localNotRunningRequired(self._vmxFilePath)
        # read existing file
        with codecs.open(self._vmxFilePath, "r", encoding="utf-8") as inputFile:
            vmxFileContent = VmxFileContent(inputFile.read())
        # modify
        vmxFileContentModifyingMethod(vmxFileContent)
        # overwrite
        with codecs.open(self._vmxFilePath, "w", encoding="utf-8") as outputFile:
            outputFile.write(vmxFileContent.string)
        # keep up-to-date
        self._load()

    def removeAllIdeCdromImages(self):
        """Remove all .vmx file parameters for all virtual IDE CD-ROM drives served from image files."""
        # recommended safe wrapper
        self.modify(lambda vmxFileContent: vmxFileContent.removeAllIdeCdromImages())

    def setEthernetAdapter(self, adapter=0, connectionType="bridged", change="enable"):
        """Set .vmx file parameters for a virtual Ethernet adapter.
        
        connectionType
            "bridged", "hostonly", or "nat".
        
        change
            "enable", "disable", or "remove"."""
        # recommended safe wrapper
        self.modify(lambda vmxFileContent:
            vmxFileContent.setEthernetAdapter(adapter=adapter, connectionType=connectionType, change=change))

if __name__ == "__main__":
    _testDir = os.path.join(tempfile.gettempdir(), Timestamp.microsecondTimestamp())
    os.mkdir(_testDir, 0755)
    try:
        _vmxFile1 = VmxFile(os.path.join(_testDir, "test1.vmx"))
        _vmxFile1.create()
    finally:
        shutil.rmtree(_testDir)


class VMwareHypervisor(object):
    """A VMware hypervisor."""

    @classmethod
    def commandsUsedInImplementation(cls):
        """Return a list to be passed to SystemRequirements.commandsRequired().
        
        This class can be passed to SystemRequirements.commandsRequiredByImplementations()."""
        return ["vmrun"] + NetworkInterface.commandsUsedInImplementation()

    def __init__(self, hostType):
        """Create new VMware hypervisor descriptor."""
        self._hostType = hostType

    # as implemented MUST match -T <hostType> parameter of vmrun command,
    # except UNKNOWN
    WORKSTATION = "ws"
    PLAYER = "player"
    UNKNOWN = "unknown"

    @classmethod
    def localHostType(cls):
        """Determine and return host type of VMware hypervisor available locally."""
        # as implemented does NOT require vmrun command, absence means not any
        vmrun = CommandCapture(["vmrun", "-T", VMwareHypervisor.WORKSTATION, "list"],
                               copyToStdio=False,
                               exceptionIfNotZero=False, exceptionIfAnyStderr=False)
        if vmrun.returncode == 0 and not vmrun.stderr:
            return VMwareHypervisor.WORKSTATION
        vmrun = CommandCapture(["vmrun", "-T", VMwareHypervisor.PLAYER, "list"],
                               copyToStdio=False,
                               exceptionIfNotZero=False, exceptionIfAnyStderr=False)
        if vmrun.returncode == 0 and not vmrun.stderr:
            return VMwareHypervisor.PLAYER
        # not any
        return VMwareHypervisor.UNKNOWN # intentionally different than None

    _localHostType = None
    _local = None

    @classproperty
    def local(cls):
        """VMware hypervisor available locally.
        
        May return None."""
        if VMwareHypervisor._localHostType is None:
            # determine on first use
            VMwareHypervisor._localHostType = VMwareHypervisor.localHostType()
            if VMwareHypervisor._localHostType != VMwareHypervisor.UNKNOWN:
                # if any
                VMwareHypervisor._local = VMwareHypervisor(VMwareHypervisor._localHostType)
        return VMwareHypervisor._local

    @classmethod
    def localRequired(cls):
        """Raises exception if no supported VMware hypervisor available locally."""
        if not VMwareHypervisor.local:
            raise Exception("must have supported VMware hypervisor available locally"
                            ", which as implemented means VMware Workstation 9.0 or newer"
                            " or VMware Player 5.0 or newer"
                            " or VMware Fusion 5.0 or newer"
                            ", and requires vmrun"
                            ", which is known to be available when installing VMware VIX 1.12")

    @property
    def hostType(self):
        """Host type of VMware hypervisor."""
        return self._hostType

    def listRunning(self):
        """Return list of paths of .vmx files of all running virtual machines."""
        vmrun = CommandCapture(["vmrun", "-T", self._hostType, "list"],
                               copyToStdio=False)
        # (?m) effects MULTILINE, skip leading whitespace, capture until including final .vmx
        paths = re.findall(r"(?m)\s*(.*\.vmx)", vmrun.stdout)
        # here an opportunity to see in debugger
        return paths

    def start(self, vmxFilePath, gui=False, extraSleepSeconds=30.0):
        """Start virtual machine.
        
        extraSleepSeconds
            extra time for this process to sleep while virtual machine is starting up,
            unless None."""
        CommandCapture(["vmrun", "-T", self._hostType, "start", vmxFilePath] + 
                       (["gui"] if gui else ["nogui"]))
        if extraSleepSeconds:
            time.sleep(extraSleepSeconds)

    def stop(self, vmxFilePath, hard=False, tolerateNotRunning=True, extraSleepSeconds=10.0):
        """Stop virtual machine.
        
        Ideally virtual machines would stop from shutting down from within the virtual machine
        to ensure proper shutdown.
        If VMware Tools are installed then a soft stop should effect such shutting down from within.
        
        If VMware Tools isn't installed then other mechanisms, e.g. issuing a command over ssh
        would seem appropriate.
        
        After some tasks, e.g. after a properly configured operating system install with kickstart,
        a machine should shut down by itself.
        
        A hard stop appears to be the least desirable option, even though it has the highest
        probability of succeeding at stopping the virtual machine it also has the highest
        probability of leaving behind virtual disk content as if after a crash.
        
        extraSleepSeconds
            extra time for this process to sleep before stopping virtual machine,
            unless None."""
        if extraSleepSeconds:
            time.sleep(extraSleepSeconds)
        try:
            CommandCapture(["vmrun", "-T", self._hostType, "stop", vmxFilePath] +
                           (["hard"] if hard else ["soft"]))
        except:
            if tolerateNotRunning:
                if not self.isRunning(vmxFilePath=vmxFilePath): # apparently .vmx file not listed as running
                    pass # avoid exception due to "Error: The virtual machine is not powered on"
                else: # apparently still running
                    raise # don't tolerate still running
            else: # behavior of stop command
                raise # don't tolerate anything

    def isRunning(self, vmxFilePath):
        """Return whether .vmx file listed as running."""
        # really want abspath and expanduser
        os.path.abspath(os.path.expanduser(vmxFilePath))
        running = self.listRunning()
        return vmxFilePath in running

    def sleepUntilNotRunning(self, vmxFilePath, checkIntervalSeconds=5.0, ticker=False):
        """If not running return, else loop sleeping for checkIntervalSeconds."""
        printed = False
        ticked = False
        # check the essential condition, initially and then repeatedly
        while self.isRunning(vmxFilePath):
            if not printed:
                # first time only printing
                print "waiting for " + vmxFilePath + " to stop"
                printed = True
            if ticker:
                if not ticked:
                    # first time only printing
                    sys.stdout.write("[")
                sys.stdout.write(".")
                sys.stdout.flush()
                ticked = True
            time.sleep(checkIntervalSeconds)
        if ticked:
            # final printing
            sys.stdout.write("]\n")

    def notRunningRequired(self, vmxFilePath):
        """Raises exception if .vmx file listed as running."""
        if self.isRunning(vmxFilePath):
            raise Exception("won't do while still running {0}".format(vmxFilePath))

    @classmethod
    def localNotRunningRequired(cls, vmxFilePath):
        """May raise exception if .vmx file locally listed as running.
        
        Only checks::
        
            VMwareHypervisor.local.notRunningRequired(vmxFilePath)
        
        Not perfect.  Nevertheless can help avoid trouble."""
        if VMwareHypervisor.local:
            VMwareHypervisor.local.notRunningRequired(vmxFilePath)
        else:
            # nothing known to test
            pass

    @property
    def suggestedDirectory(self):
        """Suggest a parent directory for virtual machine directories.
        
        For those who don't want to decide themselves."""
        suggestedDirectory = os.path.abspath(ScriptUser.loggedIn.userHomeRelative("vmware"))
        if not os.path.exists(suggestedDirectory):
            # was os.makedirs, but that could allow unintended wild creations to go undetected
            os.mkdir(suggestedDirectory, 0755)
        return suggestedDirectory

    def listSnapshots(self, vmxFilePath):
        """Return list of snapshots of virtual machine.
        
        As implemented omits leading and trailing whitespace if any."""
        vmrun = CommandCapture(["vmrun", "-T", self._hostType, "listSnapshots", vmxFilePath],
                               copyToStdio=False)
        listWithHeading = vmrun.stdout
        # first line tells number of snapshots, names are in subsequent lines
        snapshots = []
        numberMatch = re.search(r"^.*\:\s*([0-9]+)", listWithHeading)
        if numberMatch:
            numberOfSnapshots = int(numberMatch.group(1))
            # (?m) effects MULTILINE, omit leading and trailing whitespace if any
            snapshots = re.findall(r"(?m)^\s*(.*?)\s*$", listWithHeading)
            # omit first line, i.e. line with number of snapshots
            snapshots.pop(0)
            # omit empty lines, if any, e.g. after trailing newline
            snapshots = filter(None, snapshots)
        # here an opportunity to see in debugger
        return snapshots

    def createSnapshot(self, vmxFilePath, snapshot, tolerateRunning=False, tolerateDuplicate=False):
        """Create new snapshot of virtual machine.
        
        As implemented raises exception if running or if duplicate name,
        unless asked to tolerate.
        
        As implemented omits leading and trailing whitespace if any."""
        snapshot = snapshot.strip()
        # TODO reject forward slash "/" in snapshot name
        if not tolerateRunning:
            if self.isRunning(vmxFilePath):
                raise Exception("won't snapshot ({0}) while still running {1} because of default tolerateRunning=False".format(snapshot, vmxFilePath))
        if not tolerateDuplicate:
            snapshots = self.listSnapshots(vmxFilePath)
            if snapshot in snapshots:
                raise Exception("won't snapshot with duplicate name ({0}) for {1}".format(snapshot, vmxFilePath))
        vmrun = CommandCapture(["vmrun", "-T", self._hostType, "snapshot", vmxFilePath, snapshot])

    def revertToSnapshot(self, vmxFilePath, snapshot, tolerateRunning=False):
        """Revert to snapshot of virtual machine.
        
        As implemented raises exception if running, unless asked to tolerate."""
        if not tolerateRunning:
            if self.isRunning(vmxFilePath):
                raise Exception("won't revert to snapshot ({0}) while still running {1} because of default tolerateRunning=False".format(snapshot, vmxFilePath))
        vmrun = CommandCapture(["vmrun", "-T", self._hostType, "revertToSnapshot", vmxFilePath, snapshot])

    def deleteSnapshot(self, vmxFilePath, snapshot, andDeleteChildren=False, tolerateRunning=False):
        """Delete snapshot of virtual machine.
        
        As implemented raises exception if running, unless asked to tolerate."""
        if not tolerateRunning:
            if self.isRunning(vmxFilePath):
                raise Exception("won't delete snapshot while still running {0} because of default tolerateRunning=False".format(vmxFilePath))
        vmrun = CommandCapture(["vmrun", "-T", self._hostType, "deleteSnapshot", vmxFilePath, snapshot] +
                               (["andDeleteChildren"] if andDeleteChildren else []))

    def deleteDescendantsOfSnapshot(self, vmxFilePath, snapshot):
        """Delete descendants of snapshot of virtual machine.
        
        Keeps snapshot.
        
        As implemented raises exception if running."""
        vmrun = CommandCapture(["vmrun", "-T", self._hostType, "listSnapshots", vmxFilePath, "showtree"],
                               copyToStdio=False)
        listWithHeading = vmrun.stdout
        # first line tells number of snapshots, names are in subsequent lines,
        # indented because of option showtree
        snapshotLines = listWithHeading.splitlines()
        # omit first line, i.e. line with number of snapshots
        snapshotLines.pop(0)
        # omit empty lines, if any, e.g. after trailing newline
        snapshotLines = filter(None, snapshotLines)
        snapshotLines = "\n".join(snapshotLines)
        # first group is indentation string, second group is snapshot name
        snapshotLines = re.findall(r"(?m)^(\s*)(\S.*?)\s*$", snapshotLines)
        keeperIndentationLength = None
        deleteIndentationLength = None
        for i in range(0, len(snapshotLines)):
            snapshotLine = snapshotLines[i]
            indentationLength = len(snapshotLine[0])
            name = snapshotLine[1]
            if keeperIndentationLength is None:
                if name == snapshot: # found snapshot
                    keeperIndentationLength = indentationLength
                    snapshotPath = [name]
                    previousIndentationLengthForPath = indentationLength
                    for j in range(i-1, -1, -1):
                        snapshotLineForPath = snapshotLines[j]
                        indentationLengthForPath = len(snapshotLineForPath[0])
                        if indentationLengthForPath < previousIndentationLengthForPath:
                            snapshotPath.append(snapshotLineForPath[1])
                            previousIndentationLengthForPath = indentationLengthForPath
                    snapshotPath.reverse()
                    snapshotPath = "/".join(snapshotPath)
                    continue
                else: # above snapshot
                    continue
            else: # below snapshot
                if indentationLength == keeperIndentationLength: # next sibling of snapshot
                    break # done
                if deleteIndentationLength is None: # first child of snapshot
                    deleteIndentationLength = indentationLength
                if indentationLength == deleteIndentationLength: # any child of snapshot
                    snapshotToDelete = snapshotPath + "/" + name
                    # more efficient here to delete children too, and too complex to tolerate running
                    self.deleteSnapshot(vmxFilePath, snapshotToDelete, andDeleteChildren=True, tolerateRunning=False)

    def revertToSnapshotAndDeleteDescendants(self, vmxFilePath, snapshot):
        """Revert to snapshot of virtual machine and delete any and all descendants of snapshot.
        
        As implemented raises exception if running."""
        self.revertToSnapshot(vmxFilePath, snapshot, tolerateRunning=False)
        self.deleteDescendantsOfSnapshot(vmxFilePath, snapshot)

    def cloneSnapshot(self, vmxFilePath, snapshot, clonedVmxFilePath, linked=True, tolerateRunning=False):
        """Create clone of virtual machine at snapshot.
        
        As implemented raises exception if running, unless asked to tolerate.
        
        linked
            whether to create a linked clone or a full clone."""
        if not tolerateRunning:
            if self.isRunning(vmxFilePath):
                raise Exception("won't clone virtual machine while still running {0} because of default tolerateRunning=False".format(vmxFilePath))
        vmrun = CommandCapture(["vmrun", "-T", self._hostType, "clone", vmxFilePath, clonedVmxFilePath] +
                               (["linked"] if linked else ["full"]) +
                               [snapshot])

    _localHostOnlyNetworkInterfaceName = "vmnet1"
    _localHostOnlyIPAddress = None

    @classproperty
    def localHostOnlyIPAddress(cls):
        """IP address of network interface to hostonly network of VMware hypervisor available locally.
        
        May return None."""
        if not VMwareHypervisor.local:
            return None
        if VMwareHypervisor._localHostOnlyIPAddress is None:
            # determine
            VMwareHypervisor._localHostOnlyIPAddress = \
                NetworkInterface.ipAddressOf(VMwareHypervisor._localHostOnlyNetworkInterfaceName)
            if VMwareHypervisor._localHostOnlyIPAddress is None:
                # look closer
                if sys.platform == "darwin": # Mac OS X
                    # no vmnet if VMware Fusion is not running,
                    # opening a virtual machine apparently reliably starts VMware Fusion
                    tempDummyDir = os.path.join(tempfile.gettempdir(), Timestamp.microsecondTimestamp())
                    os.mkdir(tempDummyDir, 0755)
                    try:
                        tempDummyVm = VMwareMachine(os.path.join(tempDummyDir, "dummy.vmx"))
                        # a minimal .vmx file
                        with open(tempDummyVm.vmxFilePath, "w") as vmxFile:
                            vmxFile.write("""
config.version = "8"
virtualHW.version = "7"
guestOS = "linux"
memsize = "32" # megabytes, must be multiple of 4
sound.present = "FALSE"
floppy0.present = "FALSE"
serial0.present = "FALSE"
vmci0.present = "FALSE"
tools.upgrade.policy = "manual"
tools.remindInstall = "FALSE"
msg.autoAnswer = "TRUE"
""")
                        tempDummyVm.vmxFile.setEthernetAdapter(0, change="remove")
                        VMwareHypervisor.local.start(tempDummyVm.vmxFilePath, gui=False, extraSleepSeconds=0.0)
                        # now there should be a vmnet,
                        # try determining now
                        VMwareHypervisor._localHostOnlyIPAddress = \
                            NetworkInterface.ipAddressOf(VMwareHypervisor._localHostOnlyNetworkInterfaceName)
                        VMwareHypervisor.local.stop(tempDummyVm.vmxFilePath, hard=True, extraSleepSeconds=0.0)
                    finally:
                        shutil.rmtree(tempDummyDir)
        return VMwareHypervisor._localHostOnlyIPAddress

if __name__ == "__main__":
    SystemRequirements.commandsRequiredByImplementations([VMwareHypervisor], verbose=True)
    #
    if VMwareHypervisor.local:
        print VMwareHypervisor.local.hostType
        print "VMs:\n" + str(VMwareHypervisor.local.listRunning())
        someVms = VMwareHypervisor.local.listRunning()
        if someVms:
            print "Snapshots:\n" + str(VMwareHypervisor.local.listSnapshots(someVms[0]))
    else:
        print "no supported VMware hypervisor available locally"


class VMwareMachine(object):
    """A VMware virtual machine."""

    def __init__(self, vmxFilePath):
        """Create new VMware virtual machine descriptor.
        
        A descriptor can describe a VMware virtual machine that does or doesn't yet exist on the host disk."""
        self._vmxFile = VmxFile(vmxFilePath)
        self._portsFile = PortsFile(os.path.join(self._vmxFile.directory,
                                                 self._vmxFile.basenameStem + ".ports"))

    @property
    def vmxFilePath(self):
        """Path of the .vmx file."""
        return self._vmxFile.vmxFilePath

    @property
    def directory(self):
        """Directory .vmx file is in."""
        return self._vmxFile.directory

    def mkdir(self, mode=0755):
        """Create directory .vmx file will be in.
        
        Useful to have directory to put other files into early."""
        os.mkdir(self.directory, mode)

    @property
    def basenameStem(self):
        """Stem of basename of .vmx file.
        
        Used as default for displayName.
        Useful for making names of related files."""
        return self._vmxFile.basenameStem

    @property
    def vmxFile(self):
        """A VmxFile instance.
        
        If needed."""
        return self._vmxFile

    @property
    def portsFile(self):
        """A PortsFile instance.
        
        If needed."""
        return self._portsFile

    def create(self,
               memsizeMegabytes=512,
               guestOS="centos",
               ideDrives=None,
               template=VMwareTemplates.usableVMwareVmxTemplate001):
        """Create a VMware virtual machine.
        
        For some parameters see documentation of class VmxFile method create.
        
        As implemented only supports a limited number of features.
        Nevertheless essential.  To be improved as needed."""
        if not os.path.exists(self.directory):
            # was os.makedirs, but that could allow unintended wild creations to go undetected
            os.mkdir(self.directory, 0755)
        # displayName default to avoid too many parameters, for now
        self._vmxFile.create(memsizeMegabytes=memsizeMegabytes,
                             guestOS=guestOS,
                             ideDrives=ideDrives)
        self._portsFile.create()

    def remove(self):
        """Remove (delete) VMware virtual machine from the host disk.
        
        As implemented completely deletes the directory containing the .vmx file,
        which often is correct but not necessarily always."""
        if self._vmxFile.exists(): # sanity check
            shutil.rmtree(self.directory)

    def acceptKnownHostKey(self):
        """Accept host's key.
        
        Will wait until completed.
        
        Assumes .ports file to exist and to have an entry for ssh.
        
        Needs virtual machine to be running already, ready to accept ssh connections, duh."""
        ports = self.portsFile.getPorts(protocol="ssh")
        if ports is None:
            # .ports file does not exist
            raise Exception("not known how to ssh connect to machine {0}".format
                            (self.basenameStem))
        ipaddresses = map(lambda port: port["ipaddress"], ports)
        ipaddresses = set(ipaddresses)
        for ipaddress in ipaddresses:
            SshCommand.acceptKnownHostKey(ipaddress)

    def _sshPortIpaddressPwd(self, user="root"):
        """Return tuple port, ipaddress, pwd.
        
        Assumes .ports file to exist and to have an entry for ssh for the user.
        
        Auxiliary."""
        ports = self.portsFile.getPorts(protocol="ssh", user=user)
        if ports == []:
            # .ports file has no entry for user
            raise Exception("not known how to ssh connect to machine {0} for user {1}".format
                            (self.basenameStem, user))
        if ports is None:
            # .ports file does not exist
            raise Exception("not known how to ssh connect to machine {0}".format
                            (self.basenameStem))
        port = ports[0]
        ipaddress = port["ipaddress"] if "ipaddress" in port else None
        pwd = port["pwd"] if "pwd" in port else None
        if ipaddress is None:
            raise Exception("incomplete information to ssh connect to machine {0} for user {1}".format
                            (self.basenameStem, user))
        return port, ipaddress, pwd

    def sshParameters(self, user="root"):
        """Return SshParameters instance for user.
        
        user
            a string.
        
        Assumes .ports file to exist and to have an entry for ssh for the user."""
        port, ipaddress, pwd = self._sshPortIpaddressPwd(user)
        sshParameters = SshParameters(ipaddress=ipaddress, user=user, pwd=pwd)
        return sshParameters

    def sshCommand(self, argv, user="root", exceptionIfNotZero=True):
        """Return an SshCommand instance.
        
        Will wait until completed.
        
        Assumes .ports file to exist and to have an entry for ssh for the user.
        
        Needs virtual machine to be running already, ready to accept ssh connections, duh.
        
        argv
            list of command and arguments passed to ssh.
            
            Can accept a string instead of a list.
        
        user
            a string.
        
        Output may contain extraneous leading or trailing newlines and whitespace.
        
        Example use::
        
            sshCommand1 = vmwareMachine.sshCommand(["ls", "-al"])
            print "output=" + sshCommand1.output"""
        sshParameters = self.sshParameters(user=user)
        sshCommand = SshCommand(sshParameters, argv, exceptionIfNotZero=exceptionIfNotZero)
        return sshCommand

    def shutdownCommand(self, extraSleepSeconds=10.0, ignoreException=False):
        """Send shutdown command.
        
        Assumes .ports file to exist and to have an entry for shutdown.
        
        Needs virtual machine to be running already, ready to accept ssh connections, duh.
        
        Example use::
        
            vmwareMachine1.shutdownCommand()
            VMwareHypervisor.local.sleepUntilNotRunning(vmwareMachine1.vmxFilePath, ticker=True)
        
        extraSleepSeconds
            extra time for this process to sleep before shutting down virtual machine,
            unless None."""
        ports = self.portsFile.getPorts(protocol="shutdown", user=None)
        if ports == [] or ports is None:
            # .ports file has no entry for shutdown or .ports file does not exist
            raise Exception("not known how to send shutdown command to machine {0}".format
                            (self.basenameStem))
        port = ports[0]
        command = port["command"] if "command" in port else None
        user = port["user"] if "user" in port else None
        protocol = port["protocol"] if "protocol" in port else "ssh"
        if protocol != "ssh":
            raise Exception("as implemented cannot use {0} protocol to send shutdown command to machine {1}, could use ssh".format
                            (protocol, self.basenameStem))
        if command is None or user is None:
            raise Exception("incomplete information to send shutdown command to machine {0}".format
                            (self.basenameStem))
        if extraSleepSeconds:
            time.sleep(extraSleepSeconds)
        self.sshCommand([command], user, exceptionIfNotZero = not ignoreException)

    def scpPutCommand(self, fromHostPath, toGuestPath, guestUser="root"):
        """Return an ScpCommand instance.
        
        Will wait until completed.
        
        Assumes .ports file to exist and to have an entry for ssh for the user.
        
        Needs virtual machine to be running already, ready to accept ssh connections, duh."""
        toSshParameters = self.sshParameters(user=guestUser)
        scpCommand = ScpCommand.put(fromLocalPath=fromHostPath,
                                    toSshParameters=toSshParameters, toRemotePath=toGuestPath)
        return scpCommand

    def scpGetCommand(self, fromGuestPath, toHostPath, guestUser="root"):
        """Return an ScpCommand instance.
        
        Will wait until completed.
        
        Assumes .ports file to exist and to have an entry for ssh for the user.
        
        Needs virtual machine to be running already, ready to accept ssh connections, duh."""
        fromSshParameters = self.sshParameters(user=guestUser)
        scpCommand = ScpCommand.get(fromSshParameters=fromSshParameters, fromRemotePath=fromGuestPath,
                                    toLocalPath=toHostPath)
        return scpCommand

    def sshIsAvailable(self, user="root", probingCommand="hostname"):
        """Return whether probingCommand succeeds.
        
        Will wait until completed.
        
        Assumes .ports file to exist and to have an entry for ssh for the user."""
        sshParameters = self.sshParameters(user=user)
        isAvailable = SshCommand.isAvailable(sshParameters,
                                             probingCommand=probingCommand)
        return isAvailable

    def sleepUntilSshIsAvailable(self, checkIntervalSeconds=5.0, ticker=False, user="root", probingCommand="hostname", extraSleepSeconds=10.0):
        """If available return, else loop sleeping for checkIntervalSeconds.
        
        Assumes .ports file to exist and to have an entry for ssh for the user."""
        sshParameters = self.sshParameters(user=user)
        SshCommand.sleepUntilIsAvailable(sshParameters,
                                         checkIntervalSeconds=checkIntervalSeconds,
                                         ticker=ticker,
                                         probingCommand=probingCommand)
        if extraSleepSeconds:
            time.sleep(extraSleepSeconds)

    def hasAcceptedKnownHostKey(self):
        """Return whether acceptKnownHostKey succeeds.
        
        Will wait until completed.
        
        Assumes .ports file to exist and to have an entry for ssh."""
        ports = self.portsFile.getPorts(protocol="ssh")
        if ports is None:
            # .ports file does not exist
            raise Exception("not known how to ssh connect to machine {0}".format
                            (self.basenameStem))
        ipaddresses = map(lambda port: port["ipaddress"], ports)
        ipaddresses = set(ipaddresses)
        for ipaddress in ipaddresses:
            hasAcceptedKnownHostKey = SshCommand.hasAcceptedKnownHostKey(ipaddress=ipaddress)
            if not hasAcceptedKnownHostKey:
                return False
        return True

    def sleepUntilHasAcceptedKnownHostKey(self, checkIntervalSeconds=5.0, ticker=False, extraSleepSeconds=10.0):
        """If available return, else loop sleeping for checkIntervalSeconds.
        
        Assumes .ports file to exist and to have an entry for ssh."""
        ports = self.portsFile.getPorts(protocol="ssh")
        if ports is None:
            # .ports file does not exist
            raise Exception("not known how to ssh connect to machine {0}".format
                            (self.basenameStem))
        ipaddresses = map(lambda port: port["ipaddress"], ports)
        ipaddresses = set(ipaddresses)
        for ipaddress in ipaddresses:
            SshCommand.sleepUntilHasAcceptedKnownHostKey(ipaddress=ipaddress,
                                                         checkIntervalSeconds=checkIntervalSeconds,
                                                         ticker=ticker,
                                                         extraSleepSeconds=0)
        if extraSleepSeconds:
            time.sleep(extraSleepSeconds)

    @property
    def regularUser(self):
        """A regular user.
        Often the main user.
        
        Can be None."""
        return self.portsFile.getRegularUser()

if __name__ == "__main__":
    _testDir = os.path.join(tempfile.gettempdir(), Timestamp.microsecondTimestamp())
    os.mkdir(_testDir, 0755)
    try:
        _vmwareMachine1 = VMwareMachine(os.path.join(_testDir, "test1/test1.vmx"))
        _vmwareMachine1.create(memsizeMegabytes=640, ideDrives=[20000, 300])
        VMwareHypervisor.local.createSnapshot(_vmwareMachine1.vmxFilePath, "VM created")
        _vmwareMachine1.vmxFile.setEthernetAdapter(1, "nat")
        VMwareHypervisor.local.createSnapshot(_vmwareMachine1.vmxFilePath, "set NAT")
        VMwareHypervisor.local.start(_vmwareMachine1.vmxFilePath, gui=True)
        time.sleep(5)
        VMwareHypervisor.local.stop(_vmwareMachine1.vmxFilePath, hard=True)
        VMwareHypervisor.local.createSnapshot(_vmwareMachine1.vmxFilePath, "VM ran")
        _vmwareMachine1.vmxFile.removeAllIdeCdromImages()
        _vmwareMachine1.vmxFile.setEthernetAdapter(2, "bridged")
        VMwareHypervisor.local.createSnapshot(_vmwareMachine1.vmxFilePath, "set bridged too")
        VMwareHypervisor.local.revertToSnapshot(_vmwareMachine1.vmxFilePath, "VM created")
        _vmwareMachine1.vmxFile.setEthernetAdapter(1, "bridged")
        VMwareHypervisor.local.createSnapshot(_vmwareMachine1.vmxFilePath, "set bridged")
        # expect listSnapshots ['VM created', 'set NAT', 'VM ran', 'set bridged too', 'set bridged']
        print VMwareHypervisor.local.listSnapshots(_vmwareMachine1.vmxFilePath)
        VMwareHypervisor.local.revertToSnapshotAndDeleteDescendants(_vmwareMachine1.vmxFilePath, "set NAT")
        # expect listSnapshots ['VM created', 'set NAT', 'set bridged']
        print VMwareHypervisor.local.listSnapshots(_vmwareMachine1.vmxFilePath)
        _vmwareMachine1.portsFile.setRegularUser("joe")
        print _vmwareMachine1.regularUser
    finally:
        shutil.rmtree(_testDir)

if __name__ == "__main__":
    # couldn't run further above after VMwareHypervisor because of dependency on VMwareMachine
    print VMwareHypervisor.localHostOnlyIPAddress
