#!/usr/bin/python

"""nrvr.distros.el.kickstart - Create and manipulate Enterprise Linux kickstart files

Classes provided by this module include
* ElIsoImage
* ElKickstartFileContent

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Contributor - Nora Baschy

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import re

import nrvr.distros.common.kickstart

class ElIsoImage(nrvr.distros.common.kickstart.DistroIsoImage):
    """An Enterprise Linux .iso ISO CD-ROM or DVD-ROM disk image."""

    def __init__(self, isoImagePath):
        """Create new Enterprise Linux ElIsoImage descriptor.
        
        A descriptor can describe an .iso image that does or doesn't yet exist on the host disk."""
        nrvr.distros.common.kickstart.DistroIsoImage.__init__(self, isoImagePath)

    def modificationsIncludingKickstartFile(self, _kickstartFileContent):
        """Construct and return a list of modifications to be passed to method cloneWithModifications.
        
        This method is called by method cloneWithAutoBootingKickstart, which takes the returned list
        and passes it to method cloneWithModifications.
        
        As implemented known to support Scientific Linux 6.1 and 6.4.
        As implemented tested for i386 and x86_64.
        Good chance it will work with other brand Enterprise Linux distributions.
        Good chance it will work with newer versions distributions.
        
        _kickstartFileContent
            An ElKickstartFileContent object.
        
        Return a list of modifications which will be passed to method cloneWithModifications."""
        if not isinstance(_kickstartFileContent, nrvr.distros.el.kickstart.ElKickstartFileContent):
            # defense against more hidden problems
            raise Exception("not given but in need of an instance of nrvr.distros.el.kickstart.ElKickstartFileContent")
        # a distinct path
        kickstartCustomConfigurationPathOnIso = "isolinux/ks-custom.cfg"
        # modifications
        modifications = \
        [
            # the kickstart file
            nrvr.diskimage.isoimage.IsoImageModificationFromString
            (kickstartCustomConfigurationPathOnIso,
             _kickstartFileContent.string),
            # in isolinux/isolinux.cfg
            # delete any pre-existing "menu default"
            nrvr.diskimage.isoimage.IsoImageModificationByReplacement
            ("isolinux/isolinux.cfg",
             re.compile(r"(\r?\n)([ \t]+menu[ \t]+default)(\s)"),
             r"\3"),
            # in isolinux/isolinux.cfg
            # insert section with label "ks-custom", first, before "label linux",
            # documentation says "ks=cdrom:/directory/filename.cfg" with a single "/" slash, NOT double,
            # e.g. see http://fedoraproject.org/wiki/Anaconda/Kickstart,
            # must set "ksdevice=eth0" or "ksdevice=link" or else asks which network interface to use,
            # e.g. see http://wiki.centos.org/TipsAndTricks/KickStart,
            # hope you don't need to read http://fedoraproject.org/wiki/Anaconda/NetworkIssues
            nrvr.diskimage.isoimage.IsoImageModificationByReplacement
            ("isolinux/isolinux.cfg",
             re.compile(r"(\r?\n)(label[ \t]+linux\s)"),
             r"\1label ks-custom\1"
             r"  menu label Custom ^Kickstart\1"
             r"  menu default\1"
             r"  kernel vmlinuz\1"
             r"  append initrd=initrd.img ks=cdrom:/" + kickstartCustomConfigurationPathOnIso + r" ksdevice=eth0 \1\2"),
            # in isolinux/isolinux.cfg
            # change to "timeout 50" measured in 1/10th seconds
            nrvr.diskimage.isoimage.IsoImageModificationByReplacement
            ("isolinux/isolinux.cfg",
             re.compile(r"(\r?\n)(timeout[ \t]+\d+)(\s)"),
             r"\1timeout 50\3")
        ]
        return modifications


class ElKickstartFileContent(nrvr.distros.common.kickstart.DistroKickstartFileContent):
    """The text content of an Anaconda kickstart file for Enterprise Linux."""

    def __init__(self, string):
        """Create new kickstart file content container."""
        nrvr.distros.common.kickstart.DistroKickstartFileContent.__init__(self, string)

    def elReplaceHostname(self, hostname):
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

    def elReplaceStaticIP(self, ipaddress, netmask="255.255.255.0", gateway=None, nameservers=None):
        """Replace static IP options in network option.
        
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
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        # sanity check
        normalizedStaticIp = self.normalizeStaticIp(ipaddress, netmask, gateway, nameservers)
        commandSection = self.sectionByName("command")
        # several set
        commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*--ip[ \t]*(?:=|[ \t])[ \t]*)[^\s]+(.*)$",
                                       r"\g<1>" + normalizedStaticIp.ipaddress + r"\g<2>",
                                       commandSection.string)
        commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*--netmask[ \t]*(?:=|[ \t])[ \t]*)[^\s]+(.*)$",
                                       r"\g<1>" + normalizedStaticIp.netmask + r"\g<2>",
                                       commandSection.string)
        commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*--gateway[ \t]*(?:=|[ \t])[ \t]*)[^\s]+(.*)$",
                                       r"\g<1>" + normalizedStaticIp.gateway + r"\g<2>",
                                       commandSection.string)
        if normalizedStaticIp.nameservers:
            commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*--nameserver[ \t]*(?:=|[ \t])[ \t]*)[^\s]+(.*)$",
                                           r"\g<1>" + ",".join(normalizedStaticIp.nameservers) + r"\g<2>",
                                           commandSection.string)
        else:
            # remove option --nameserver
            commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*)--nameserver[ \t]*(?:=|[ \t])[ \t]*[^\s]+(.*)$",
                                           r"\g<1>" + r"\g<2>",
                                           commandSection.string)
        return self

    def elAddNetworkConfigurationWithDhcp(self, device):
        """Add an additional network device with DHCP.
        
        device
            a string, e.g. "eth1".
            
            Should be increased past "eth1" if adding more than one additional configuration.
            
            Pre-existing network configurations are moved up by one device each, if there would be a conflict.
            E.g. adding for "eth0" when for "eth0" already exists causes the pre-existing for "eth0" to become for "eth1".
        
        return
            self, for daisychaining."""
        commandSection = self.sectionByName("command")
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        deviceMatch = re.match(r"([^0-9]+)([0-9])", device)
        if deviceMatch:
            # e.g. "eth0"
            devicePrefix = deviceMatch.group(1)
            deviceNumber = deviceMatch.group(2)
            deviceNumber = int(deviceNumber)
            for i in range(8, deviceNumber - 1, -1):
                deviceI = devicePrefix + str(i)
                deviceIPlus1 = devicePrefix + str(i + 1)
                # move up by one device each network configuration
                commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*--device[ \t]*(?:=|[ \t])[ \t]*)" + re.escape(deviceI) + r"(.*)$",
                                               r"\g<1>" + deviceIPlus1 + r"\g<2>",
                                               commandSection.string)
        # not --noipv6
        networkConfiguration = "network --device=" + device + " --bootproto=dhcp --onboot=yes --activate"
        if deviceMatch and deviceNumber == 0:
            # having configuration of eth0 first appears to be more conducive to overall success,
            # and also, per http://fedoraproject.org/wiki/Anaconda/Kickstart#network, supposedly
            # "... in installer environment. Device of the first network command is activated if network is required,
            # e.g. in case of network installation ...",
            commandSection.string = networkConfiguration + "\n" \
                                    + "#\n" \
                                    + commandSection.string
        else:
            commandSection.string = commandSection.string \
                                    + "#\n" \
                                    + networkConfiguration + "\n"

    def elActivateGraphicalLogin(self):
        """Boot into graphical login on the installed system.
        
        Do not use in a kickstart that does not install the X Window System.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        commandSection = self.sectionByName("command")
        commandSection.string = commandSection.string + """
#
# XWindows configuration information.
xconfig --startxonboot --defaultdesktop=GNOME
"""
        return self

    def elAddUser(self, username, pwd=None):
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
                pwd = self.cryptedPwd(pwd)
                isCrypted = True
        else:
            isCrypted = False
        commandSection = self.sectionByName("command")
        commandSection.string = commandSection.string \
                                + "#\n" \
                                + "user --name=" + username \
                                + (" --password=" + pwd if pwd else "") \
                                + (" --iscrypted" if isCrypted else "") \
                                + "\n"

if __name__ == "__main__":
    from nrvr.distros.el.kickstarttemplates import ElKickstartTemplates
    _kickstartFileContent = ElKickstartFileContent(ElKickstartTemplates.usableElKickstartTemplate001)
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
