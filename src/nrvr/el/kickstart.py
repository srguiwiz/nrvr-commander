#!/usr/bin/python

"""nrvr.el.kickstart - Create and manipulate Enterprise Linux kickstart files

Classes provided by this module include
* ElIsoImage
* KickstartFileSection
* KickstartFileContent

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import re

import nrvr.diskimage.isoimage
from nrvr.el.kickstarttemplates import KickstartTemplates
from nrvr.process.commandcapture import CommandCapture
from nrvr.util.ipaddress import IPAddress

class ElIsoImage(nrvr.diskimage.isoimage.IsoImage):
    """An Enterprise Linux .iso ISO CD-ROM or DVD-ROM disk image."""

    def __init__(self, isoImagePath):
        """Create new Enterprise Linux IsoImage descriptor.
        
        A descriptor can describe an .iso image that does or doesn't yet exist on the host disk."""
        nrvr.diskimage.isoimage.IsoImage.__init__(self, isoImagePath)

    def cloneWithAutoBootingKickstart(self, _kickstartFileContent, cloneIsoImagePath=None):
        """Clone with kickstart file added and modified to automatically boot with it.
        
        For more on behavior see documentation of class IsoImage method cloneWithModifications.
        
        _kickstartFileContent
            A KickstartFileContent object.

        As implemented known to support Scientific Linux 6.1 and 6.4.
        As implemented tested for i386 and x86_64.
        Good chance it will work with other brand Enterprise Linux distributions.
        Good chance it will work with newer versions distributions."""
        # a distinct path
        kickstartCustomConfigurationPathOnIso = "isolinux/ks-custom.cfg"
        # modifications
        modifications = \
        [nrvr.diskimage.isoimage.IsoImageModificationFromString
         (kickstartCustomConfigurationPathOnIso,
          _kickstartFileContent.string),
         # in isolinux.cfg
         # delete any pre-existing "menu default"
         nrvr.diskimage.isoimage.IsoImageModificationByReplacement
         ("isolinux/isolinux.cfg",
          re.compile(r"(\r?\n)([ \t]+menu[ \t]+default)(\s)"),
          r"\3"),
         # in isolinux.cfg
         # insert section with label "ks-custom", first, before "label linux",
         # documentation says "ks=cdrom:/directory/filename.cfg" with a single "/" slash, NOT double,
         # e.g. see http://fedoraproject.org/wiki/Anaconda/Kickstart,
         # must set "ksdevice=eth0" or "ksdevice=link" or else asks which network interface to use,
         # e.g. see http://wiki.centos.org/TipsAndTricks/KickStart,
         # hope you don't need to read http://fedoraproject.org/wiki/Anaconda/NetworkIssues
         nrvr.diskimage.isoimage.IsoImageModificationByReplacement
         ("isolinux/isolinux.cfg",
          re.compile(r"(\r?\n)(label[ \t]+linux)(\s)"),
          r"\1label ks-custom\1"
          r"  menu label Custom ^Kickstart\1"
          r"  menu default\1"
          r"  kernel vmlinuz\1"
          r"  append initrd=initrd.img ks=cdrom:/" + kickstartCustomConfigurationPathOnIso + r" ksdevice=eth0 \1\2\3"),
         # in isolinux.cfg
         # change to "timeout 50" measured in 1/10th seconds
         nrvr.diskimage.isoimage.IsoImageModificationByReplacement
         ("isolinux/isolinux.cfg",
          re.compile(r"(\r?\n)(timeout[ \t]+\d+)(\s)"),
          r"\1timeout 50\3")]
        # clone with modifications
        clone = self.cloneWithModifications(cloneIsoImagePath=cloneIsoImagePath,
                                            modifications=modifications)
        return clone


class KickstartFileSection(object):
    """The name and text content of a section of an Anaconda kickstart file for Enterprise Linux."""

    def __init__(self, name, string):
        """Create new kickstart file content section container."""
        self.name = name
        self.string = string
    @property
    def string(self):
        """Getter."""
        return self._string
    @string.setter
    def string(self, newString):
        """Setter.
        
        If not already ends with a newline then appends a newline to make sure it
        ends with a newline."""
        # make sure section content string ends with a newline
        if newString[-1] != "\n":
            newString = newString + "\n"
        self._string = newString


class KickstartFileContent(object):
    """The text content of an Anaconda kickstart file for Enterprise Linux."""

    def __init__(self, string):
        """Create new kickstart file content container.
        
        Documentation is at http://fedoraproject.org/wiki/Anaconda/Kickstart.
        
        Documentation apparently says a kickstart file is an ASCII file.
        
        Nevertheless, this constructor does unicode(string), as befits the 21st century.
        Just don't put anything into it that is not in the ASCII range."""
        self._sections = KickstartFileContent.parseIntoSections(unicode(string))

    @classmethod
    def parseIntoSections(cls, whole):
        """Return sections as list of KickstartFileSection objects."""
        sectionsSplit = re.split(r"(?:\r?\n[ \t]*)%", whole)
        sectionNameRegex = re.compile(r"^([^\s]*)")
        sections = []
        # make tuples (sectionName, sectionContent)
        for sectionIndex in range(0, len(sectionsSplit)):
            if sectionIndex == 0:
                # for the initial command section, which doesn't start with a %
                sectionContent = sectionsSplit[sectionIndex]
                sectionName = "command"
            else:
                # for all except the initial command section, those start with a %,
                # also put back the "%" that was lost in split
                sectionContent = "%" + sectionsSplit[sectionIndex]
                sectionName = sectionNameRegex.match(sectionContent).group(1)
            sections.append(KickstartFileSection(sectionName, sectionContent))
        # now mostly for readability of comments in resulting file,
        # try a little bit of smarts in recognizing what comments or empty lines go with what section,
        # this is isn't an exact algorithm, possibly cannot be exact,
        # hence for all sections except last
        whitespaceOnlyRegex = re.compile(r"^[ \t]*$")
        anyCommentRegex = re.compile(r"^[ \t]*#.*$")
        emptyCommentRegex = re.compile(r"^[ \t]*#[ \t]*$")
        for sectionIndex in range(0, len(sections) - 1):
            # this section as lines
            linesSplit = sections[sectionIndex].string.splitlines()
            # start looking after first line
            lastSubstantialLine = 0
            for lineIndex in range (1, len(linesSplit)):
                line = linesSplit[lineIndex]
                if whitespaceOnlyRegex.match(line):
                    continue
                if anyCommentRegex.match(line):
                    continue
                lastSubstantialLine = lineIndex
            # now look after last substantial line
            firstWhitespaceOnlyLine = None
            for lineIndex in range (lastSubstantialLine + 1, len(linesSplit)):
                if whitespaceOnlyRegex.match(linesSplit[lineIndex]):
                    firstWhitespaceOnlyLine = lineIndex
                    break
            firstEmtpyCommentLine = None
            for lineIndex in range (lastSubstantialLine + 1, len(linesSplit)):
                if emptyCommentRegex.match(linesSplit[lineIndex]):
                    firstEmtpyCommentLine = lineIndex
                    break
            if firstWhitespaceOnlyLine is not None:
                firstLineToMove = firstWhitespaceOnlyLine
            elif firstEmtpyCommentLine is not None:
                firstLineToMove = firstEmtpyCommentLine
            else:
                firstLineToMove = None
            if firstLineToMove is not None:
                # put into next section
                linesToMove = "\n".join(linesSplit[firstLineToMove:]) + "\n"
                sections[sectionIndex + 1].string = linesToMove + sections[sectionIndex + 1].string
                # remove from this section
                linesSplit = linesSplit[:firstLineToMove]
            # put back into this section
            if linesSplit:
                lines = "\n".join(linesSplit) + "\n"
            else:
                # not any line left, maybe possible
                lines = ""
            sections[sectionIndex].string = lines
        return sections

    @property
    def string(self):
        """The whole content.
        
        As implemented this is dynamically built, but it is
        for the sake of correctness and maintainability."""
        return "".join(section.string for section in self._sections)

    @property
    def sections(self):
        return self._sections

    def sectionByName(self, name):
        """Return section by name.
        
        Return a KickstartFileSection, or None.
        
        Setting a returned KickstartFileSection's string modifies the KickstartFileContent.
        
        If more than one section with same name returns first."""
        for section in self._sections:
            if name == section.name:
                return section
        return None

    def sectionsByName(self, name):
        """Return sections by name.
        
        Return a list of KickstartFileSection, or empty list [].
        
        Setting a returned KickstartFileSection's string modifies the KickstartFileContent."""
        sections = []
        for section in self._sections:
            if name == section.name:
                sections.append(section)
        return sections

    @classmethod
    def cryptedPwd(cls, plainPwd):
        """Encrypt in a format acceptable for kickstart."""
        # as implemented MD5 hash it, e.g. $1$sodiumch$UqZCYecJ/y5M5pp1x.7C4/
        # TODO explore allowing and defaulting to newer SHA-512 (aka sha512), starting with $6
        cryptedPwd = CommandCapture(["openssl",
                                     "passwd",
                                     "-1", # use the MD5 based BSD pwd algorithm 1
                                     "-salt", "sodiumchloride",
                                     plainPwd],
                                    copyToStdio=False).stdout
        # get rid of extraneous newline or any extraneous whitespace
        cryptedPwd = re.search(r"^\s*([^\s]+)", cryptedPwd).group(1)
        # here cryptedPwd should start with $
        return cryptedPwd

    def replaceRootpw(self, pwd):
        """Replace rootpw option.
        
        pwd
            pwd will be encrypted.  If starting with $ it is assumed to be encrypted already.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        # if starts with $ then assume encrypted
        isCrypted = re.match(r"\$", pwd)
        if not isCrypted:
            pwd = KickstartFileContent.cryptedPwd(pwd)
            isCrypted = True
        commandSection = self.sectionByName("command")
        # change to known root pwd
        commandSection.string = re.sub(r"(?m)^([ \t]*rootpw[ \t]+).*$",
                                       r"\g<1>" + ("--iscrypted " if isCrypted else "") + pwd,
                                       commandSection.string)
        return self

    def replaceHostname(self, hostname):
        """Replace hostname option in network option.
        
        hostname
            new hostname.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        hostname = re.escape(hostname) # precaution
        commandSection = self.sectionByName("command")
        # change to hostname
        commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*--hostname[ \t]*(?:=|[ \t])[ \t]*)[^\s]+(.*)$",
                                       r"\g<1>" + hostname + r"\g<2>",
                                       commandSection.string)
        return self

    def replaceStaticIP(self, ip, netmask="255.255.255.0", gateway=None, nameserver=None):
        """Replace static IP options in network option.
        
        As implemented only supports IPv4.
        
        ip
            IP address.
        
        netmask
            netmask.
            Defaults to 255.255.255.0.
        
        gateway
            gateway.
            If None then default to ip.1.
        
        nameserver
            one nameserver or a list of nameservers.
            If None then default to gateway.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        commandSection = self.sectionByName("command")
        # sanity check
        ip = IPAddress.asString(ip)
        if not re.match(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$", ip):
            raise Exception("won't accept apparently impossible IP address {0}".format(ip))
        netmask = IPAddress.asString(netmask)
        if gateway is None:
            # default to ip.1
            gateway = IPAddress.bitOr(IPAddress.bitAnd(ip, netmask), "0.0.0.1")
        gateway = IPAddress.asString(gateway)
        if nameserver is None:
            # default to gateway
            nameservers = [gateway]
        elif not isinstance(nameserver, list):
            # process one as a list of one
            nameservers = [nameserver]
        else:
            # given a list already
            nameservers = nameserver
        nameserversStrings = [IPAddress.asString(oneNameserver) for oneNameserver in nameservers]
        # several set
        commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*--ip[ \t]*(?:=|[ \t])[ \t]*)[^\s]+(.*)$",
                                       r"\g<1>" + ip + r"\g<2>",
                                       commandSection.string)
        commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*--netmask[ \t]*(?:=|[ \t])[ \t]*)[^\s]+(.*)$",
                                       r"\g<1>" + netmask + r"\g<2>",
                                       commandSection.string)
        commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*--gateway[ \t]*(?:=|[ \t])[ \t]*)[^\s]+(.*)$",
                                       r"\g<1>" + gateway + r"\g<2>",
                                       commandSection.string)
        commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*--nameserver[ \t]*(?:=|[ \t])[ \t]*)[^\s]+(.*)$",
                                       r"\g<1>" + ",".join(nameserversStrings) + r"\g<2>",
                                       commandSection.string)
        return self

    def activateGraphicalLogin(self):
        """Boot into graphical login on the installed system.
        
        Do not use in a kickstart that does not install the X Window System.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        commandSection = self.sectionByName("command")
        commandSection.string = commandSection.string + """#
# XWindows configuration information.
xconfig --startxonboot
"""
        return self

    def addUser(self, username, pwd=None):
        """Add user.
        
        username
            username to add.
        
        pwd
            pwd will be encrypted.  If starting with $ it is assumed to be encrypted already.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        username = re.escape(username) # precaution
        if pwd:
            # if pwd starts with $ then assume encrypted
            isCrypted = re.match(r"\$", pwd)
            if not isCrypted:
                pwd = KickstartFileContent.cryptedPwd(pwd)
                isCrypted = True
        else:
            isCrypted = False
        commandSection = self.sectionByName("command")
        commandSection.string = commandSection.string + "#\n" \
                                                      + "user --name=" + username \
                                                      + (" --password=" + pwd if pwd else "") \
                                                      + (" --iscrypted" if isCrypted else "") \
                                                      + "\n"

    # .group(1) to be first word to whitespace or #
    firstWordOfLineRegex = re.compile(r"^[ \t]*([^\s#]*).*$")

    def addPackage(self, package):
        """Add package or package group to %packages section.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        packagesSection = self.sectionByName("%packages")
        # this section as lines
        linesSplit = packagesSection.string.splitlines()
        # check whether package already listed
        pastSectionName = False
        alreadyListed = False
        for line in linesSplit:
            # check whether first word matches, i.e. to whitespace or #
            firstWordOfLine = KickstartFileContent.firstWordOfLineRegex.search(line).group(1)
            if not pastSectionName:
                if firstWordOfLine.startswith("%"):
                    pastSectionName = True
                # don't look yet until pastSectionName
                continue
            if firstWordOfLine == package:
                # already listed
                alreadyListed = True
                break
        if not alreadyListed:
            # add package
            linesSplit.append(package)
        # put back into this section
        packagesSection.string = "\n".join(linesSplit) + "\n"
        return self

    def removePackage(self, package):
        """Remove package or package group from %packages section.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        packagesSection = self.sectionByName("%packages")
        # this section as lines
        linesSplit = packagesSection.string.splitlines()
        # check whether package listed
        pastSectionName = False
        filteredLines = []
        for line in linesSplit:
            # check whether first word matches, i.e. to whitespace or #
            firstWordOfLine = KickstartFileContent.firstWordOfLineRegex.search(line).group(1)
            if not pastSectionName:
                if firstWordOfLine.startswith("%"):
                    pastSectionName = True
                # don't filter yet until pastSectionName
                filteredLines.append(line)
                continue
            if firstWordOfLine != package:
                # don't filter other packages
                filteredLines.append(line)
        # put back into this section
        packagesSection.string = "\n".join(filteredLines) + "\n"
        return self

    def removeAllPackages(self):
        """Remove all packages and package groups from %packages section.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        packagesSection = self.sectionByName("%packages")
        # this section as lines
        linesSplit = packagesSection.string.splitlines()
        # check whether package already listed
        pastSectionName = False
        filteredLines = []
        for line in linesSplit:
            # check whether first word matches, i.e. to whitespace or #
            firstWordOfLine = KickstartFileContent.firstWordOfLineRegex.search(line).group(1)
            if not pastSectionName:
                if firstWordOfLine.startswith("%"):
                    pastSectionName = True
                # don't filter yet until pastSectionName
                filteredLines.append(line)
                if pastSectionName:
                    # no more
                    break
                else:
                    continue
        # put back into this section
        packagesSection.string = "\n".join(filteredLines) + "\n"
        return self

    def replaceAllPackages(self, packages):
        """Replace all packages and package groups in %packages section.
        
        packages
            a list of packages and package groups.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        packagesSection = self.sectionByName("%packages")
        # this section as lines
        linesSplit = packagesSection.string.splitlines()
        # check whether package already listed
        pastSectionName = False
        filteredLines = []
        for line in linesSplit:
            # check whether first word matches, i.e. to whitespace or #
            firstWordOfLine = KickstartFileContent.firstWordOfLineRegex.search(line).group(1)
            if not pastSectionName:
                if firstWordOfLine.startswith("%"):
                    pastSectionName = True
                # don't filter yet until pastSectionName
                filteredLines.append(line)
                if pastSectionName:
                    # no more
                    break
                else:
                    continue
        # add replacement packages
        filteredLines.extend(packages)
        # put back into this section
        packagesSection.string = "\n".join(filteredLines) + "\n"
        return self

if __name__ == "__main__":
    _kickstartFileContent = KickstartFileContent(KickstartTemplates.usableKickstartTemplate001)
    _kickstartFileContent.replaceRootpw("redwood")
    _kickstartFileContent.replaceHostname("test-hostname-101")
    _kickstartFileContent.replaceStaticIP("10.123.45.67")
    _kickstartFileContent.addPackage("another-package-for-testing")
    _kickstartFileContent.addPackage("@another-package-group-for-testing")
    _kickstartFileContent.addPackage("@base")
    _kickstartFileContent.removePackage("@client-mgmt-tools")
    _kickstartFileContent.removeAllPackages()
    _kickstartFileContent.addPackage("made-something-up-for-testing")
    _kickstartFileContent.replaceAllPackages(["@package-group-1-for-testing",
                                             "@package-group-2-for-testing",
                                             "@package-group-3-for-testing",
                                             "package-a-for-testing",
                                             "package-b-for-testing",
                                             "package-c-for-testing"])
    _kickstartFileContent.activateGraphicalLogin()
    _kickstartFileContent.addUser("jack", pwd="rainbow")
    _kickstartFileContent.addUser("jill", "sunshine")
    _kickstartFileContent.addUser("pat")
    _kickstartFileContent.sectionByName("%post").string = "removed %post this time, weird, just for testing\n"
    print _kickstartFileContent.string
