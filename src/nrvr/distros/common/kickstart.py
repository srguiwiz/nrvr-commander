#!/usr/bin/python

"""nrvr.distros.common.kickstart - Create and manipulate Linux distribution kickstart files

Classes provided by this module include
* DistroIsoImage
* KickstartFileSection
* DistroKickstartFileContent

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

from collections import namedtuple
import re

import nrvr.diskimage.isoimage
from nrvr.process.commandcapture import CommandCapture
from nrvr.util.ipaddress import IPAddress

class DistroIsoImage(nrvr.diskimage.isoimage.IsoImage):
    """A Linux distribution .iso ISO CD-ROM or DVD-ROM disk image."""

    def __init__(self, isoImagePath):
        """Create new Linux distribution IsoImage descriptor.
        
        A descriptor can describe an .iso image that does or doesn't yet exist on the host disk."""
        nrvr.diskimage.isoimage.IsoImage.__init__(self, isoImagePath)

    def genisoimageOptions(self,
                           bootImage="isolinux/isolinux.bin", bootCatalog="isolinux/boot.cat",
                           label=None):
        """Auxiliary method, called by cloneWithModifications.
        
        As implemented calls superclass method genisoimageOptions and extends the returned list.
        
        Could be improved in the future.
        Could recognize content of .iso image.
        Could select different options depending on content of .iso image.
        Could be overridden for a subclass."""
        # this implementation has been made to work for Linux
        genisoimageOptions = super(DistroIsoImage, self).genisoimageOptions(label=label)
        genisoimageOptions.extend([
            # boot related
            "-no-emul-boot",
            "-boot-load-size", "4",
            "-boot-info-table",
            "-b", bootImage,
            "-c", bootCatalog
        ])
        return genisoimageOptions

    def modificationsIncludingKickstartFile(self, _kickstartFileContent):
        """Construct and return a list of modifications to be passed to method cloneWithModifications.
        
        This method is called by method cloneWithAutoBootingKickstart, which takes the returned list
        and passes it to method cloneWithModifications.
        
        Subclasses should provide substantial implementations of this method.
        Expected to be different per distro specific subclass.
        This class implementation only returns an empty list [].
        
        _kickstartFileContent
            A DistroKickstartFileContent object.
        
        Return a list of modifications which will be passed to method cloneWithModifications."""
        modifications = []
        return modifications

    def cloneWithAutoBootingKickstart(self, _kickstartFileContent, cloneIsoImagePath=None):
        """Clone with kickstart file added and modified to automatically boot with it.
        
        For more on behavior see documentation of class IsoImage method cloneWithModifications.
        
        For details of modifications see method modificationsIncludingKickstartFile,
        which is expected to be different per distro specific subclass.
        
        _kickstartFileContent
            A DistroKickstartFileContent object."""
        # modifications, could be quite different per distro specific subclass
        modifications = self.modificationsIncludingKickstartFile(_kickstartFileContent)
        # clone with modifications
        clone = self.cloneWithModifications(modifications=modifications,
                                            cloneIsoImagePath=cloneIsoImagePath)
        return clone


class KickstartFileSection(object):
    """The name and text content of a section of an Anaconda kickstart file for use with a Linux distribution."""

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


NetworkConfigurationStaticParameters = namedtuple("NetworkConfigurationStaticParameters",
                                                  ["ipaddress", "netmask", "gateway", "nameservers"])


class DistroKickstartFileContent(object):
    """The text content of an Anaconda kickstart file for use with a Linux distribution."""

    def __init__(self, string):
        """Create new kickstart file content container.
        
        Documentation is at http://fedoraproject.org/wiki/Anaconda/Kickstart .
        
        Documentation apparently says a kickstart file is an ASCII file.
        
        Nevertheless, this constructor does unicode(string), as befits the 21st century.
        Just don't put anything into it that is not in the ASCII range."""
        self._sections = self.parseIntoSections(unicode(string))

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
        
        Setting a returned KickstartFileSection's string modifies the DistroKickstartFileContent.
        
        If more than one section with same name returns first."""
        for section in self._sections:
            if name == section.name:
                return section
        return None

    def sectionsByName(self, name):
        """Return sections by name.
        
        Return a list of KickstartFileSection, or empty list [].
        
        Setting a returned KickstartFileSection's string modifies the DistroKickstartFileContent."""
        sections = []
        for section in self._sections:
            if name == section.name:
                sections.append(section)
        return sections

    def replaceLang(self, lang):
        """Replace lang option.
        
        lang
            e.g. "de_DE.UTF-8" to replace "en_US.UTF-8".
            
            As implemented does not do any sanity checking.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        commandSection = self.sectionByName("command")
        commandSection.string = re.sub(r"(?m)^([ \t]*lang[ \t]+).*$",
                                       r"\g<1>" + lang,
                                       commandSection.string)
        return self

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
            pwd = self.cryptedPwd(pwd)
            isCrypted = True
        commandSection = self.sectionByName("command")
        # change to known root pwd
        commandSection.string = re.sub(r"(?m)^([ \t]*rootpw[ \t]+).*$",
                                       r"\g<1>" + ("--iscrypted " if isCrypted else "") + pwd,
                                       commandSection.string)
        return self

    def normalizeStaticIp(self, ipaddress, netmask="255.255.255.0", gateway=None, nameservers=None):
        """Normalize static IP options for network configuration.
        
        For use in methods in this class DistroKickstartFileContent and in its subclasses.
        
        As implemented only supports IPv4.
        
        ipaddress
            IP address.
        
        netmask
            netmask.
            Defaults to 255.255.255.0.
        
        gateway
            gateway.
            If None then default to ip.1.
        
        nameservers
            one nameserver or a list of nameservers.
            If None then default to gateway.
            If empty list then remove option.
        
        return
            a NetworkConfigurationStaticParameters instance."""
        # also see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        # sanity check
        ipaddress = IPAddress.asString(ipaddress)
        if not re.match(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$", ipaddress):
            raise Exception("won't accept apparently impossible IP address {0}".format(ipaddress))
        netmask = IPAddress.asString(netmask)
        if gateway is None:
            # default to ip.1
            gateway = IPAddress.bitOr(IPAddress.bitAnd(ipaddress, netmask), "0.0.0.1")
        gateway = IPAddress.asString(gateway)
        if nameservers is None:
            # default to gateway
            nameservers = [gateway]
        elif not isinstance(nameservers, list):
            # process one as a list of one
            nameservers = [nameservers]
        else:
            # given a list already
            nameservers = nameservers
        nameserversStrings = [IPAddress.asString(oneNameserver) for oneNameserver in nameservers]
        normalized = NetworkConfigurationStaticParameters(ipaddress=ipaddress,
                                                          netmask=netmask,
                                                          gateway=gateway,
                                                          nameservers=nameserversStrings)
        return normalized

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
            firstWordOfLine = DistroKickstartFileContent.firstWordOfLineRegex.search(line).group(1)
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
            firstWordOfLine = DistroKickstartFileContent.firstWordOfLineRegex.search(line).group(1)
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
            firstWordOfLine = DistroKickstartFileContent.firstWordOfLineRegex.search(line).group(1)
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
            firstWordOfLine = DistroKickstartFileContent.firstWordOfLineRegex.search(line).group(1)
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

    def setSwappiness(self, swappiness):
        """Set swappiness.
        
        swappiness
            an int between 0 and 100.
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/12.04/installation-guide/example-preseed.txt
        postSection = self.sectionByName("%post")
        swappiness = int(swappiness) # precaution
        if not 0 <= swappiness <= 100:
            raise Exception("swappiness must be between 0 and 100, cannot be {0}".format(swappiness))
        swappiness = str(swappiness)
        # will have effect from next booting onwards,
        # then verifiable by looking at cat /proc/sys/vm/swappiness
        settingSwappiness = "".join(
            "\n#"
            "\n# Set swappiness"
            "\nif ( grep -q '^vm.swappiness=' /etc/sysctl.conf ) ; then"
            "\n  # replace"
            "\n  sed -i -e 's/^vm.swappiness=.*/vm.swappiness=" + swappiness + "/' /etc/sysctl.conf"
            "\nelse"
            "\n  # append"
            "\n  echo '' >> /etc/sysctl.conf"
            "\n  echo '#' >> /etc/sysctl.conf"
            "\n  echo 'vm.swappiness=" + swappiness + "' >> /etc/sysctl.conf"
            "\nfi"
            )
        # simply append
        # in case of multiple invocations last one would be effective
        postSection.string = postSection.string + settingSwappiness + "\n"

if __name__ == "__main__":
    from nrvr.distros.el.kickstart import ElKickstartFileContent
    from nrvr.distros.el.kickstarttemplates import ElKickstartTemplates
    _kickstartFileContent = ElKickstartFileContent(ElKickstartTemplates.usableElKickstartTemplate001)
    _kickstartFileContent.replaceLang("de_DE.UTF-8")
    _kickstartFileContent.replaceRootpw("redwood")
    _kickstartFileContent.elReplaceHostname("test-hostname-101")
    _kickstartFileContent.elReplaceStaticIP("10.123.45.67")
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
    _kickstartFileContent.elAddNetworkConfigurationWithDhcp("eth1")
    _kickstartFileContent.elAddNetworkConfigurationWithDhcp("eth0")
    _kickstartFileContent.elActivateGraphicalLogin()
    _kickstartFileContent.elAddUser("jack", pwd="rainbow")
    _kickstartFileContent.elAddUser("jill", "sunshine")
    _kickstartFileContent.elAddUser("pat")
    _kickstartFileContent.sectionByName("%post").string = "\n#\n%post\n# replaced all of %post this time, just for testing\n"
    _kickstartFileContent.setSwappiness(30)
    print _kickstartFileContent.string
