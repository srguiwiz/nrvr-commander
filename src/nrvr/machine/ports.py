#!/usr/bin/python

"""nrvr.machine.ports - Create and modify a .ports file

The main class provided by this module is PortsFile.

To be expanded as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import codecs
import os.path
from xml.etree.ElementTree import ElementTree, Element, SubElement

from nrvr.util.ipaddress import IPAddress
from nrvr.xml.etree import ElementTreeUtil

class PortsFile(object):
    """A .ports file for a machine.
    
    Example content::
    
        <?xml version="1.0" encoding="utf-8"?>
        <ports>
          <ssh>
            <ipaddress>10.123.45.67</ipaddress>
            <user>root</user>
            <pwd>redwood</pwd>
          </ssh>
          <shutdown>
            <command>shutdown -h now</command>
            <user>root</user>
            <protocol>ssh</protocol>
          </shutdown>
        </ports>"""

    def __init__(self, portsFilePath):
        """Create new .ports file descriptor.
        
        A descriptor can describe a .ports file that does or doesn't yet exist on the host disk."""
        # really want abspath and expanduser
        self._portsFilePath = os.path.abspath(os.path.expanduser(portsFilePath))
        # sanity check filename extension
        extension = os.path.splitext(os.path.basename(self._portsFilePath))[1]
        if extension != ".ports":
            raise Exception("won't accept .ports filename not ending in .ports: {0}".format(self._portsFilePath))
        self._portsFileContent = None
        # keep up-to-date
        self._load()

    @property
    def portsFilePath(self):
        """Path of the .ports file."""
        return self._portsFilePath

    def exists(self):
        """Return True if file exists on the host disk."""
        return os.path.exists(self._portsFilePath)

    def _load(self):
        """Load content from file into an xml.etree.ElementTree instance.
        
        If not self.exists() then does nothing.
        
        Auxiliary."""
        if self.exists():
            # read existing file
            with codecs.open(self._portsFilePath, "r", encoding="utf-8") as inputFile:
                self._portsFileContent = ElementTree().parse(inputFile)

    @property
    def portsFileContent(self):
        """An xml.etree.ElementTree instance.
        
        If not self.exists() may be None."""
        return self._portsFileContent

    def create(self):
        """Create a .ports file.
        
        As implemented creates an empty container.
        
        Does nothing in case file already exist on the host disk."""
        if self.exists():
            # intentionally not raise Exception("won't overwrite already existing {0}".format(self._portsFilePath))
            return
        # just an empty container
        ports = Element("ports")
        portsFileContent = ElementTree(ports)
        #
        # write
        with codecs.open(self._portsFilePath, "w", encoding="utf-8") as outputFile:
            # from Python 2.7 and ElementTree 1.3 on with xml_declaration=True
            #portsFileContent.write(outputFile, encoding="utf-8")
            outputFile.write(ElementTreeUtil.tostring \
                             (portsFileContent, indent="  ", xml_declaration=True, encoding="utf-8"))
        # keep up-to-date
        self._load()

    def modify(self, portsFileContentModifyingMethod):
        """Recommended safe wrapper to modify .ports file.
        
        Does nothing in case file doesn't exist on the host disk.
        Intentionally does nothing to support installation policies where .ports files
        are not to be stored.
        
        To make sure file exists, call create()."""
        # help avoid trouble
        if not self.exists():
            # intentionally not self.create()
            return
        # read existing file
        with codecs.open(self._portsFilePath, "r", encoding="utf-8") as inputFile:
            portsFileContent = ElementTree(file=inputFile)
        # modify
        portsFileContentModifyingMethod(portsFileContent)
        # overwrite
        with codecs.open(self._portsFilePath, "w", encoding="utf-8") as outputFile:
            # from Python 2.7 and ElementTree 1.3 on with xml_declaration=True
            #portsFileContent.write(outputFile, encoding="utf-8")
            outputFile.write(ElementTreeUtil.tostring \
                             (portsFileContent, indent="  ", xml_declaration=True, encoding="utf-8"))
        # keep up-to-date
        self._load()

    @classmethod
    def _setSsh(cls, portsFileContent, ipaddress, user, pwd):
        """Set .ports file entry for ssh access for a user."""
        # method made to be portsFileContentModifyingMethod parameter for method modify()
        ipaddress = IPAddress.asString(ipaddress)
        # feel the misery of not yet having better XPath from Python 2.7 and ElementTree 1.3
        sshElements = portsFileContent.findall("ssh")
        for sshElement in sshElements:
            if user == sshElement.findtext("user") and ipaddress == sshElement.findtext("ipaddress"):
                # found user at ipaddress
                pwdElement = sshElement.find("pwd")
                if pwdElement is None: # odd case
                    pwdElement = SubElement(sshElement, "pwd")
                pwdElement.text = pwd
                return # done
        # no entry yet for user at ipaddress
        sshElement = SubElement(portsFileContent.getroot(), "ssh")
        ipaddressElement = SubElement(sshElement, "ipaddress")
        ipaddressElement.text = ipaddress
        userElement = SubElement(sshElement, "user")
        userElement.text = user
        pwdElement = SubElement(sshElement, "pwd")
        pwdElement.text = pwd

    def setSsh(self, ipaddress, user, pwd):
        """Set .ports file entry for ssh access for a user."""
        # recommended safe  wrapper
        self.modify(lambda portsFileContent: self._setSsh(portsFileContent,
                                                          ipaddress=ipaddress, user=user, pwd=pwd))

    @classmethod
    def _removeSsh(cls, portsFileContent, ipaddress, user):
        """Remove .ports file entry for ssh access for a user."""
        # method made to be portsFileContentModifyingMethod parameter for method modify()
        ipaddress = IPAddress.asString(ipaddress)
        # feel the misery of not yet having better XPath from Python 2.7 and ElementTree 1.3
        ports = portsFileContent.getroot()
        sshElements = portsFileContent.findall("ssh")
        for sshElement in sshElements:
            if user == sshElement.findtext("user") and ipaddress == sshElement.findtext("ipaddress"):
                # found user at ipaddress
                ports.remove(sshElement)

    def removeSsh(self, ipaddress, user):
        """Remove .ports file entry for ssh access for a user."""
        # recommended safe  wrapper
        self.modify(lambda portsFileContent: self._removeSsh(portsFileContent,
                                                             ipaddress=ipaddress, user=user))

    @classmethod
    def _setShutdown(cls, portsFileContent, command="shutdown -h now", user="root", protocol="ssh"):
        """Set .ports file entry for shutdown command for machine."""
        # method made to be portsFileContentModifyingMethod parameter for method modify()
        # feel the misery of not yet having better XPath from Python 2.7 and ElementTree 1.3
        shutdownElements = portsFileContent.findall("shutdown")
        for shutdownElement in shutdownElements:
            if user == shutdownElement.findtext("user") and protocol == shutdownElement.findtext("protocol"):
                # found user and protocol
                commandElement = shutdownElement.find("command")
                if commandElement is None: # odd case
                    commandElement = SubElement(shutdownElement, "command")
                commandElement.text = command
                return # done
        # no entry yet for user at protocol
        shutdownElement = SubElement(portsFileContent.getroot(), "shutdown")
        commandElement = SubElement(shutdownElement, "command")
        commandElement.text = command
        userElement = SubElement(shutdownElement, "user")
        userElement.text = user
        protocolElement = SubElement(shutdownElement, "protocol")
        protocolElement.text = protocol

    def setShutdown(self, command="shutdown -h now", user="root", protocol="ssh"):
        """Set .ports file entry for shutdown command for machine."""
        # recommended safe  wrapper
        self.modify(lambda portsFileContent: self._setShutdown(portsFileContent,
                                                               command=command, user=user, protocol=protocol))

    def getPorts(self, protocol=None, user=None):
        """Return a list of dictionaries of .ports file entries for a user.
        
        If self.portsFileContent is None then return None.
        
        If no match then return empty list [].
        
        protocol
            e.g. "ssh".
            
            If None then all.
        
        user
            e.g. "joe".
            
            If None then all."""
        if self._portsFileContent is None:
            # a good way to signal back to caller
            return None
        # feel the misery of not yet having better XPath from Python 2.7 and ElementTree 1.3
        if protocol is not None:
            portElements = self._portsFileContent.findall(protocol)
        else:
            portElements = self._portsFileContent.findall("*")
        ports = []
        for portElement in portElements:
            if user is not None:
                if user == portElement.findtext("user"):
                    ports.append(ElementTreeUtil.simpledict(portElement))
            else:
                ports.append(ElementTreeUtil.simpledict(portElement))
        return ports

    @classmethod
    def _changeIPAddress(cls, portsFileContent, oldIpAddress, newIpAddress):
        """Change all occurences of a specific IP address."""
        # method made to be portsFileContentModifyingMethod parameter for method modify()
        oldIpAddress = IPAddress.asString(oldIpAddress)
        newIpAddress = IPAddress.asString(newIpAddress)
        # feel the misery of not yet having better XPath from Python 2.7 and ElementTree 1.3
        sshElements = portsFileContent.findall("ssh")
        for sshElement in sshElements:
            if oldIpAddress == sshElement.findtext("ipaddress"):
                # found oldIpAddress
                ipaddressElement = sshElement.find("ipaddress")
                ipaddressElement.text = newIpAddress

    def changeIPAddress(self, oldIpAddress, newIpAddress):
        """Set .ports file entry for shutdown command for machine."""
        # recommended safe  wrapper
        self.modify(lambda portsFileContent: self._changeIPAddress(portsFileContent,
                                                                   oldIpAddress=oldIpAddress, newIpAddress=newIpAddress))

if __name__ == "__main__":
    import shutil
    import tempfile
    from nrvr.util.times import Timestamp
    _testDir = os.path.join(tempfile.gettempdir(), Timestamp.microsecondTimestamp())
    os.mkdir(_testDir, 0755)
    try:
        _portsFile1 = PortsFile(os.path.join(_testDir, "test1.ports"))
        _portsFile1.create()
        _portsFile1.setSsh("10.123.45.67", "root", "redwood")
        _portsFile1.setSsh("10.123.45.67", "joe", "dummy")
        _portsFile1.setSsh("10.123.45.67", "jane", "funny")
        print _portsFile1.getPorts(protocol="ssh")
        _portsFile1.removeSsh("10.123.45.67", "joe")
        print _portsFile1.getPorts(protocol="ssh", user="root")
        _portsFile1.changeIPAddress("10.123.45.67", "10.123.45.68")
        print _portsFile1.getPorts(protocol="ssh")
    finally:
        shutil.rmtree(_testDir)
