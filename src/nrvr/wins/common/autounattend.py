#!/usr/bin/python

"""nrvr.wins.common.autounattend - Create and manipulate Windows installer autounattend.xml files

Classes provided by this module include
* WinUdfImage
* InstallerAutounattendFileContent

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

from collections import namedtuple
import re

import nrvr.diskimage.isoimage
from nrvr.process.commandcapture import CommandCapture
from nrvr.util.ipaddress import IPAddress
from nrvr.util.networkinterface import NetworkConfigurationStaticParameters

class WinUdfImage(nrvr.diskimage.isoimage.IsoImage):
    """A Windows installer UDF DVD-ROM disk image."""

    @classmethod
    def commandsUsedInImplementation(cls):
        """Return a list to be passed to SystemRequirements.commandsRequired().
        
        This class can be passed to SystemRequirements.commandsRequiredByImplementations()."""
        return nrvr.diskimage.isoimage.IsoImage.commandsUsedInImplementation() + ["isoinfo"]

    def __init__(self, isoImagePath):
        """Create new Windows installer WinUdfImage descriptor.
        
        A descriptor can describe an .iso image that does or doesn't yet exist on the host disk."""
        nrvr.diskimage.isoimage.IsoImage.__init__(self, isoImagePath)

    def genisoimageOptions(self,
                           bootImage="boot.bin",
                           label=None,
                           udf=True, ignoreJoliet=False):
        """Auxiliary method, called by cloneWithModifications.
        
        Can be overridden by subclass methods genisoimageOptions,
        which may want to extend the returned list.
        
        Could be improved in the future.
        Could recognize content of .iso image.
        Could select different options depending on content of .iso image.
        Maybe could use iso-info -d 9 -i self.isoImagePath.
        Could be overridden for a subclass."""
        # this implementation has been made to work for Windows
        if not label:
            label = Timestamp.microsecondTimestamp()
        genisoimageOptions = []
        if udf: # udf
            genisoimageOptions.append("-udf")
        if not ignoreJoliet:
            # broader compatibility of filenames and metadata
            genisoimageOptions.extend([
                # broader compatibility of filenames and metadata
                "-J",
                "-joliet-long"
            ])
        genisoimageOptions.extend([
            # directories and filenames
            "-relaxed-filenames",
            #
            # boot related
            "-no-emul-boot",
            "-b", bootImage,
            #
            # possibly needed labeling,
            # volume id, volume name or label, max 32 characters
            "-V", label[-32:]
        ])
        return genisoimageOptions

    def cloneWithModifications(self, modifications=[], cloneIsoImagePath=None, udf=True, ignoreJoliet=False,
                               pause=False):
        """Clone with any number of instances of IsoImageModification applied.
        
        A temporary assembly directory in the same directory as cloneIsoImagePath needs disk space,
        but it is removed automatically upon completion of cloning.
        
        modifications
            a list of IsoImageModification instances.
        
        cloneIsoImagePath
            if not given then in same directory with a timestamp in the filename.
        
        return
            WinUdfImage(cloneIsoImagePath)."""
        clone = super(WinUdfImage, self).cloneWithModifications(modifications=modifications,
                                                                cloneIsoImagePath=cloneIsoImagePath,
                                                                udf=udf,
                                                                ignoreJoliet=ignoreJoliet,
                                                                pause=pause)
        return WinUdfImage(clone.isoImagePath)

    def modificationsIncludingAutounattendFile(self, _autounattendFileContent):
        """Construct and return a list of modifications to be passed to method cloneWithModifications.
        
        This method is called by method cloneWithAutounattend, which takes the returned list
        and passes it to method cloneWithModifications.
        
        Subclasses may provide further implementations of this method.
        Possibly different per Windows version specific subclass.
        This class implementation does return an essential list.
        
        _autounattendFileContent
            An InstallerAutounattendFileContent object.
            
            If None then proceed nevertheless.
        
        Return a list of modifications which will be passed to method cloneWithModifications."""
        # modifications
        modifications = []
        modifications.extend([
            # a boot image is a necessity
            self.modificationForElToritoBootImage()
            ])
        if _autounattendFileContent:
            modifications.extend([
                # the autounattend.xml file
                nrvr.diskimage.isoimage.IsoImageModificationFromString
                ("autounattend.xml",
                 _autounattendFileContent.string)
                ])
        return modifications

    def cloneWithAutounattend(self, _autounattendFileContent, modifications=[], cloneIsoImagePath=None):
        """Clone with autounattend.xml file added and modified to automatically boot with it.
        
        For more on behavior see documentation of class IsoImage method cloneWithModifications.
        
        For details of modifications see method modificationsIncludingAutounattendFile,
        which might be different per Windows version specific subclass.
        
        _autounattendFileContent
            An InstallerAutounattendFileContent object.
            
            If None then proceed nevertheless.
        
        modifications
            a list of additional IsoImageModification instances.
        
        cloneIsoImagePath
            if not given then in same directory with a timestamp in the filename.
        
        return
            IsoImage(cloneIsoImagePath)."""
        # modifications, possibly different per Windows version specific subclass
        modifications.extend(self.modificationsIncludingAutounattendFile(_autounattendFileContent))
        # clone with modifications
        clone = self.cloneWithModifications(modifications=modifications,
                                            cloneIsoImagePath=cloneIsoImagePath)
        return clone

    def modificationForElToritoBootImage(self):
        """Construct and return an instance of IsoImageModification, to be processed
        by method cloneWithModifications.
        
        As implemented copies El Torito boot image from sectors into a file."""
        # as implemented assumes this is the kind of disk with this kind of info
        isoinfo = CommandCapture([
            "isoinfo",
            "-d",
            "-j", "UTF-8", # avoid stderr "Setting input-charset to 'UTF-8' from locale."
            "-i", self._isoImagePath],
            copyToStdio=False)
        info = isoinfo.stdout
        numberOfSectors = re.search(r"(?mi)^[ \t]*Nsect[ \t]+([0-9]+).*$", info).group(1)
        numberOfSectors = int(numberOfSectors, base=16)
        firstSector = re.search(r"(?mi)^[ \t]*Bootoff[ \t]+([0-9a-f]+).*$", info).group(1)
        firstSector = int(firstSector, base=16)
        start = firstSector * 2048
        stop = start + numberOfSectors * 2048
        modification = \
            nrvr.diskimage.isoimage.IsoImageModificationFromByteRange(
                "boot.bin",
                self.isoImagePath,
                start, stop)
        return modification

    def modificationMakeEiCfg(self, editionId, oem=False, volumeLicense=False):
        """Construct and return an instance of IsoImageModification, to be processed
        by method cloneWithModifications.
        
        As implemented writes a new sources/ei.cfg file from scratch.
        
        editionId
            a string.
            For Windows 7 one of "Starter", "HomeBasic", "HomePremium", "Professional", "Ultimate", "Enterprise".
            For Windows 8 one of "Core", "Professional", "ProfessionalWMC", "Enterprise"."""
        eiCfgContent = "".join(
            "[EditionID]\n"
            + editionId + "\n"
            "[Channel]\n"
            + ("Retail" if not oem else "OEM") + "\n"
            "[VL]\n"
            + ("0" if not volumeLicense else "1") + "\n"
            )
        modification = \
            nrvr.diskimage.isoimage.IsoImageModificationFromString(
                "sources/ei.cfg",
                eiCfgContent)
        return modification


ElementAttributeNameValue = namedtuple("ElementAttributeNameValue", ["elementName", "attributeName", "attributeValue"])


class InstallerAutounattendFileContent(object):
    """The text content of a Windows installer autounattend.xml file for use with a Windows installer."""
    # this current implementation is more awkward than we would have known how to code, specifically
    # we would have preferred using XPath (or at least DOM) instead of regular expressions,
    # mostly we did because of a self-imposed requirement to use only libraries that come
    # with Python 2.6 (are available in Enterprise Linux 6.4 without additional installs);
    # so with xml.etree.ElementTree we couldn't (maybe gave up too quickly trying to) figure
    # how to write out the XML with namespaces so it would work when running setup;
    # allowing Python 2.7 would give better XPath support in ElementTree, and
    # maybe writing out would work better or we could code something that writes out better;
    # this is what it is now, and could be implemented in a more XML way in the future

    def __init__(self, string):
        """Create new autounattend file content container.
        
        This constructor does unicode(string)."""
        self._string = unicode(string)

    @property
    def string(self):
        """The whole content."""
        return self._string

    def _replaceElementText(self, name, text):
        """Very simple replacement of element text.
        
        As implemented replaces all elements that match.
        
        name
            tag name of element to match.
        
        text
            text to insert.
            If empty string then simply make it empty.
            If None then delete the element instead.
            
            As implemented does not escape.
        
        return
            self, for daisychaining."""
        patternString = r"(?s)(<" + name + r"(?:\s*|\s+.*?)>)(.*?)(</" + name + r"\s*>)"
        if text is not None:
            replacementString = r"\g<1>" + text + r"\g<3>"
        else:
            replacementString = r""
        self._string = re.sub(patternString, replacementString, self._string)
        return self

    def _replaceNestedElementText(self, names, text):
        """Very simple replacement of element text.
        
        As implemented replaces all elements that match.
        
        names
            a list of tag names of nested element to match.
        
        text
            text to insert.
            If empty string then simply make it empty.
            If None then delete the element instead.
            
            As implemented does not escape.
        
        return
            self, for daisychaining."""
        openingTagsPattern = r""
        closingTagsPattern = r""
        firstLevel = True
        while names:
            nextName = names.pop(0)
            if not firstLevel:
                openingTagsPattern = openingTagsPattern + r".*?"
                closingTagsPattern = r".*?" + closingTagsPattern
            openingTagsPattern = openingTagsPattern + r"<" + nextName + r"(?:\s*|\s+.*?)>"
            closingTagsPattern = r"</" + nextName + r"\s*>" + closingTagsPattern
            firstLevel = False
        patternString = r"(?s)(" + openingTagsPattern + r")(.*?)(" + closingTagsPattern + r")"
        if text is not None:
            replacementString = r"\g<1>" + text + r"\g<3>"
        else:
            replacementString = r""
        self._string = re.sub(patternString, replacementString, self._string)
        return self

    def _appendToChildren(self, elementName, attributeName, attributeValue, additionalContent, prepend=False):
        """Simple appending of content to the children of element.
        
        As implemented replaces all elements that match.
        
        elementName
            tag name of element to match.
        
        attributeName
            name of an attribute of element to match.
            If None or empty string then no attribute match required.
        
        attributeValue
            value for the attribute to match.
        
        additionalContent
            a string of additionalContent to insert.
            
            As implemented does not escape.
        
        prepend
            whether to prepend instead of to append.
        
        return
            self, for daisychaining."""
        if attributeName:
            attributePartOfPatternString = r'\s+(?:[^>]*?\s+)?_ATTRIBUTENAME_\s*=\s*"_ATTRIBUTEVALUE_"'
        else:
            attributePartOfPatternString = r''
        patternString = r'(?s)(<_ELEMENTNAME_' + attributePartOfPatternString + r'[^>]*>)(.*?)(</_ELEMENTNAME_\s*>)'
        # make pattern match actual names and values,
        # tolerate regular expression metacharacters
        patternString = re.sub(r"_ELEMENTNAME_", re.escape(elementName), patternString)
        if attributeName:
            patternString = re.sub(r"_ATTRIBUTENAME_", re.escape(attributeName), patternString)
            patternString = re.sub(r"_ATTRIBUTEVALUE_", re.escape(attributeValue), patternString)
        if not prepend:
            replacementString = r"\g<1>\g<2>" + additionalContent + r"\g<3>"
        else:
            replacementString = r"\g<1>" + additionalContent + r"\g<2>\g<3>"
        self._string = re.sub(patternString, replacementString, self._string)
        return self

    def _appendToNestedChildren(self, elementAttributeNameValues, additionalContent, prepend=False):
        """Simple appending of content to the children of element.
        
        As implemented replaces all elements that match.
        
        elementAttributeNameValues
            a list of ElementAttributeNameValue instances for nested element to match.
            
            Wherein elementName is a tag name of element to match.
            
            Wherein attributeName is a name of an attribute of element to match.
            If None or empty string then no attribute match required.
            
            Wherein attributeValue is a value for the attribute to match.
        
        additionalContent
            a string of additionalContent to insert.
            
            As implemented does not escape.
        
        prepend
            whether to prepend instead of to append.
        
        return
            self, for daisychaining."""
        openingTagsPattern = r""
        closingTagsPattern = r""
        firstLevel = True
        while elementAttributeNameValues:
            elementAttributeNameValue = elementAttributeNameValues.pop(0)
            elementName = elementAttributeNameValue.elementName
            attributeName = elementAttributeNameValue.attributeName
            attributeValue = elementAttributeNameValue.attributeValue
            if attributeName:
                attributePartOfPatternString = r'\s+(?:[^>]*?\s+)?' + attributeName + r'\s*=\s*"' + attributeValue + r'"'
            else:
                attributePartOfPatternString = r''
            if not firstLevel:
                openingTagsPattern = openingTagsPattern + r".*?"
                closingTagsPattern = r".*?" + closingTagsPattern
            openingTagsPattern = openingTagsPattern + r"<" + elementName + attributePartOfPatternString + r"[^>]*>"
            closingTagsPattern = r"</" + elementName + r"\s*>" + closingTagsPattern
            firstLevel = False
        patternString = r"(?s)(" + openingTagsPattern + r")(.*?)(" + closingTagsPattern + r")"
        if not prepend:
            replacementString = r"\g<1>\g<2>" + additionalContent + r"\g<3>"
        else:
            replacementString = r"\g<1>" + additionalContent + r"\g<2>\g<3>"
        self._string = re.sub(patternString, replacementString, self._string)
        return self

    def replaceLanguageAndLocale(self, languageAndLocale):
        """Replace language and locale.
        
        languageAndLocale
            e.g. "de-DE" to replace "en-US".
            
            As implemented does not do any sanity checking.
        
        return
            self, for daisychaining."""
        # see http://technet.microsoft.com/en-us/library/ff715986.aspx
        # see http://technet.microsoft.com/en-us/library/ff715564.aspx
        langSpecs = ["UILanguage", "SystemLocale", "InputLocale", "UserLocale"]
        for langSpec in langSpecs:
            self._replaceElementText(langSpec, languageAndLocale)
        return self

    def replaceAdminPw(self, pwd):
        """Replace administrator password.
        
        return
            self, for daisychaining."""
        self._replaceNestedElementText(["AdministratorPassword", "Value"], pwd)
        return self

    def replaceComputerName(self, computerName):
        """Replace computer name.
        
        return
            self, for daisychaining."""
        self._replaceElementText("ComputerName", computerName)
        return self

    def addNetworkConfigurationStatic(self, mac,
                                      ipaddress, netmask="255.255.255.0", gateway=None, nameservers=None,
                                      limitRoutingToLocalByNetmask=False):
        """Add an additional network device with static IP.
        
        As implemented only supports IPv4.
        
        mac
            the MAC, e.g. "01:23:45:67:89:ab" or "01-23-45-67-89-AB".
        
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
            If empty list then do not add any.
        
        return
            self, for daisychaining."""
        # sanity check
        normalizedStaticIp = NetworkConfigurationStaticParameters.normalizeStaticIp(ipaddress, netmask, gateway, nameservers)
        # see http://technet.microsoft.com/en-us/library/ff716288.aspx
        mac = mac.replace(":","-").upper()
        ipaddressSlashRoutingPrefixLength = normalizedStaticIp.ipaddress + "/" + str(normalizedStaticIp.routingprefixlength)
        gatewaySlashRoutingPrefixLength = normalizedStaticIp.gateway + "/" + str(normalizedStaticIp.routingprefixlength)
        if not limitRoutingToLocalByNetmask:
            routePrefix = "0.0.0.0/0"
        else:
            routePrefix = IPAddress.asString(normalizedStaticIp.localprefix) + "/" + str(normalizedStaticIp.routingprefixlength)
        nameservers = normalizedStaticIp.nameservers
        additionalContent = r"""
<component name="Microsoft-Windows-TCPIP" processorArchitecture="x86" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Interfaces>
    <Interface wcm:action="add">
      <Identifier>""" + mac + r"""</Identifier>
      <Ipv4Settings>
        <DhcpEnabled>false</DhcpEnabled>
        <RouterDiscoveryEnabled>false</RouterDiscoveryEnabled>
      </Ipv4Settings>
      <UnicastIpAddresses>
        <IpAddress wcm:action="add" wcm:keyValue="1">""" + ipaddressSlashRoutingPrefixLength + r"""</IpAddress>
      </UnicastIpAddresses>
      <Routes>
        <Route wcm:action="add">
          <Identifier>1</Identifier>
          <NextHopAddress>""" + gatewaySlashRoutingPrefixLength + r"""</NextHopAddress>
          <Prefix>""" + routePrefix + r"""</Prefix>
        </Route>
      </Routes>
    </Interface>
  </Interfaces>
</component>"""
        if nameservers:
            additionalContent += r"""
<component name="Microsoft-Windows-DNS-Client" processorArchitecture="x86" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Interfaces>
    <Interface wcm:action="add">
      <Identifier>""" + mac + r"""</Identifier>
      <DNSServerSearchOrder>
""" + "\n".join(map(lambda nameserver, i:
                    r"""<IpAddress wcm:action="add" wcm:keyValue=""" r'"' + str(i+1) + r'"' r""">""" + nameserver + r"""</IpAddress>""",
                    nameservers, range(0,len(nameservers)))) + r"""
      </DNSServerSearchOrder>
      <EnableAdapterDomainNameRegistration>false</EnableAdapterDomainNameRegistration>
      <DisableDynamicUpdate>true</DisableDynamicUpdate>
    </Interface>
  </Interfaces>
<DNSDomain>example.com</DNSDomain>
</component>"""
        self._appendToChildren("settings", "pass", "specialize", additionalContent, prepend=True)
        return self

    def acceptEula(self, fullname, organization=None, productkey=None):
        """Accept software license terms.
        
        fullname
            according to documentation should be name of the end user.
        
        organization
            according to documentation should be name of the organization that owns the computer.
            
            Some value has to be provided.
            
            If None then default to fullname.
        
        productkey
            according to documentation should be a product key.
            
            If None then do not change value.
            
            A product key contains settings that specify which edition to install.
            
            This probably is a legal matter and you may have to figure this out between yourself,
            the supplier of the operating system which you are installing, and counsel you may employ.
            
            Warnings aside, this could be quite simple.  Enterprises apparently have license agreements
            in place with the supplier of the operating system which you are installing.
            And, many computers are sold bundled with valid licenses already.
            And, licenses can be bought.
        
        return
            self, for daisychaining."""
        # see http://technet.microsoft.com/en-us/library/ff716077.aspx
        self._replaceNestedElementText(["UserData", "FullName"], fullname)
        if organization is None:
            organization = fullname
        self._replaceNestedElementText(["UserData", "Organization"], organization)
        if productkey is not None:
            self._replaceNestedElementText(["UserData", "ProductKey", "Key"], productkey)
        # see http://technet.microsoft.com/en-us/library/ff715801.aspx
        self._replaceElementText("RegisteredOwner", fullname)
        return self

    def addLocalAccount(self, username, pwd, fullname, groups):
        """Add a local account.
        
        username
            username.
        
        pwd
            password.
            May be empty string.
        
        fullname
            full name.
        
        groups
            a list of groups, e.g. ["Administrators"].
        
        return
            self, for daisychaining."""
        # see http://technet.microsoft.com/en-us/library/ff716114.aspx
        additionalContent = r"""<LocalAccount wcm:action="add">
  <Description>""" + fullname + r"""</Description>
  <DisplayName>""" + fullname + r"""</DisplayName>
  <Name>""" + username + r"""</Name>
  <Password>
    <Value>""" + pwd + r"""</Value>
    <PlainText>true</PlainText>
  </Password>
  <Group>""" + ";".join(groups) + r"""</Group>
</LocalAccount>
"""
        self._appendToChildren("LocalAccounts", None, None, additionalContent)
        return self

    def enableAutoLogon(self, username, pwd):
        """Enable automatic logon.
        
        username
            username.
        
        pwd
            password.
            May be empty string.
        
        return
            self, for daisychaining."""
        # see http://technet.microsoft.com/en-us/library/ff715801.aspx
        additionalContent = r"""<AutoLogon>
  <Enabled>true</Enabled>
  <Username>""" + username + r"""</Username>
  <Password>
    <Value>""" + pwd + r"""</Value>
    <PlainText>true</PlainText>
  </Password>
</AutoLogon>
"""
        self._appendToNestedChildren([ElementAttributeNameValue("settings", "pass", "oobeSystem"),
                                      ElementAttributeNameValue("component", "name", "Microsoft-Windows-Shell-Setup")],
            additionalContent)
        return self

    def adjustFor32Bit(self):
        """Adjust for 32-bit.
        
        return
            self, for daisychaining."""
        self._string = re.sub(r'(\s+processorArchitecture\s*=\s*")(amd64)(")',
                              r"\g<1>x86\g<3>",
                              self._string)
        return self

    def adjustFor64Bit(self):
        """Adjust for 32-bit.
        
        return
            self, for daisychaining."""
        self._string = re.sub(r'(\s+processorArchitecture\s*=\s*")(x86)(")',
                              r"\g<1>amd64\g<3>",
                              self._string)
        return self
