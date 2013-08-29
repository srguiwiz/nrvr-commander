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
        """Create new Enterprise Linux IsoImage descriptor.
        
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

    def elReplaceStaticIP(self, ip, netmask="255.255.255.0", gateway=None, nameserver=None):
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
            If empty list then remove option.
        
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
        if nameserversStrings:
            commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*--nameserver[ \t]*(?:=|[ \t])[ \t]*)[^\s]+(.*)$",
                                           r"\g<1>" + ",".join(nameserversStrings) + r"\g<2>",
                                           commandSection.string)
        else:
            # remove option --nameserver
            commandSection.string = re.sub(r"(?m)^([ \t]*network[ \t]+.*)--nameserver[ \t]*(?:=|[ \t])[ \t]*[^\s]+(.*)$",
                                           r"\g<1>" + r"\g<2>",
                                           commandSection.string)
        return self

    def elAddNetworkConfigurationWithDhcp(self, device="eth1"):
        """Add an additional network device with DHCP.
        
        device
            should be increased past "eth1" if adding more than one additional configuration.
            
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
