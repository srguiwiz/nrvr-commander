#!/usr/bin/python

"""nrvr.distros.ub.rel1404.preseed - Create and manipulate Ubuntu preseed files

Classes provided by this module include
* Ub1404IsoImage
* UbPreseedFileContent

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2015.
Simplified BSD License"""

import re

import nrvr.diskimage.isoimage
from nrvr.process.commandcapture import CommandCapture
from nrvr.util.networkinterface import NetworkConfigurationStaticParameters

class Ub1404IsoImage(nrvr.diskimage.isoimage.IsoImage):
    """An Ubuntu .iso ISO CD-ROM or DVD-ROM disk image for use with preseed."""

    def __init__(self, isoImagePath):
        """Create new Ubuntu Ub1404IsoImage descriptor.
        
        A descriptor can describe an .iso image that does or doesn't yet exist on the host disk."""
        nrvr.diskimage.isoimage.IsoImage.__init__(self, isoImagePath)

    def genisoimageOptions(self,
                           bootImage="isolinux/isolinux.bin", bootCatalog="isolinux/boot.cat",
                           label=None,
                           udf=False, ignoreJoliet=True):
        """Auxiliary method, called by cloneWithModifications.
        
        As implemented calls superclass method genisoimageOptions and extends the returned list.
        
        Could be improved in the future.
        Could be overridden for a subclass."""
        # this implementation has been made to work for Linux,
        # could be improved in the future,
        # could recognize content of .iso image,
        # could select different options depending on content of .iso image,
        # maybe could use iso-info -d 9 -i self.isoImagePath
        genisoimageOptions = super(Ub1404IsoImage, self).genisoimageOptions(label=label,
                                                                            udf=udf, ignoreJoliet=ignoreJoliet)
        genisoimageOptions.extend([
            # boot related
            "-no-emul-boot",
            "-boot-load-size", "4",
            "-boot-info-table",
            "-b", bootImage,
            "-c", bootCatalog
        ])
        return genisoimageOptions

    def modificationsIncludingPreseedFile(self, _preseedFileContent, _firstTimeStartScript):
        """Construct and return a list of modifications to be passed to method cloneWithModifications.
        
        This method is called by method cloneWithAutoBootingPreseed, which takes the returned list
        and passes it to method cloneWithModifications.
        
        As implemented known to support Ubuntu 14.04 LTS.
        
        _preseedFileContent
            A UbPreseedFileContent object.
        
        _firstTimeStartScript
            A string.
        
        Return a list of modifications which will be passed to method cloneWithModifications."""
        if not isinstance(_preseedFileContent, nrvr.distros.ub.rel1404.preseed.UbPreseedFileContent):
            # defense against more hidden problems
            raise Exception("not given but in need of an instance of nrvr.distros.ub.rel1404.preseed.UbPreseedFileContent")
        # a distinct label
        preseedCustomLabel = "pscustom"
        # a distinct path
        preseedCustomConfigurationPathOnIso = "preseed/" + preseedCustomLabel + ".seed"
        # modifications
        modifications = []
        modifications.extend([
            # the preseed file
            nrvr.diskimage.isoimage.IsoImageModificationFromString
            (preseedCustomConfigurationPathOnIso,
             _preseedFileContent.string),
            # the first time start script
            nrvr.diskimage.isoimage.IsoImageModificationFromString
            ("preseed/first-time-start",
             _firstTimeStartScript),
            # in isolinux/txt.cfg
            # insert section with label "pscustom", first, before "label install" or "label live"
            nrvr.diskimage.isoimage.IsoImageModificationByReplacement
            ("isolinux/txt.cfg",
             re.compile(r"(?ms)(\r?\n)(label[ \t]+(?:install|live)\s.*?vmlinuz(\.efi|)?)"),
             r"\1label " + preseedCustomLabel + r"\1"
             r"  menu label Custom ^preseed\1"
             r"  kernel /casper/vmlinuz\3\1"
             r"  append file=/cdrom/" + preseedCustomConfigurationPathOnIso +
             r" boot=casper"
             # automatic-ubiquity per https://wiki.ubuntu.com/UbiquityAutomation
             r" automatic-ubiquity"
             # noprompt per https://wiki.ubuntu.com/UbiquityAutomation
             r" noprompt"
             r" initrd=/casper/initrd.lz"
             r" -- \1\2"),
            # in isolinux/txt.cfg
            # replace "default install" or "default live" with "default pscustom"
            nrvr.diskimage.isoimage.IsoImageModificationByReplacement
            ("isolinux/txt.cfg",
             re.compile(r"(^|\r?\n)(default[ \t]+)(\S+)"),
             r"\1\g<2>" + preseedCustomLabel),
            # in isolinux/isolinux.cfg
            # change to "timeout 50" measured in 1/10th seconds
            nrvr.diskimage.isoimage.IsoImageModificationByReplacement
            ("isolinux/isolinux.cfg",
             re.compile(r"(\r?\n)(timeout[ \t]+\d+)(\s)"),
             r"\1timeout 50\3"),
            # put into isolinux/lang
            # installer language selection
            nrvr.diskimage.isoimage.IsoImageModificationFromString
            ("isolinux/lang",
             r"en" + "\n")
            ])
        return modifications

    def cloneWithAutoBootingPreseed(self, _preseedFileContent, _firstTimeStartScript, modifications=[], cloneIsoImagePath=None):
        """Clone with preseed file added and modified to automatically boot with it.
        
        For more on behavior see documentation of class IsoImage method cloneWithModifications.
        
        For details of modifications see method modificationsIncludingPreseedFile,
        which is expected to be different per release specific subclass.
        
        _preseedFileContent
            A UbPreseedFileContent object.
        
        _firstTimeStartScript
            A string.
        
        cloneIsoImagePath
            if not given then in same directory with a timestamp in the filename.
        
        return
            IsoImage(cloneIsoImagePath)."""
        # modifications, could be quite different per release specific subclass
        modifications.extend(self.modificationsIncludingPreseedFile(_preseedFileContent, _firstTimeStartScript))
        # clone with modifications
        clone = self.cloneWithModifications(modifications=modifications,
                                            cloneIsoImagePath=cloneIsoImagePath)
        return clone


class UbPreseedFileContent(object):
    """The text content of a preseed file for Ubuntu."""

    def __init__(self, string):
        """Create new preseed file content container.
        
        Documentation is at https://help.ubuntu.com/14.04/installation-guide/i386/apb.html .
        
        Not sure whether documentation says what encoding a preseed file can or has to be.
        
        This constructor does unicode(string), as befits the 21st century.
        Unless you find documentation, don't put anything into it that is not in the ASCII range."""
        self._wholeContent = unicode(string)

    @property
    def string(self):
        """The whole content."""
        return self._wholeContent

    def setPreseedValue(self, qowner, qname, qtype, qvalue):
        """Set a preseed value in the command section.
        
        qowner
            "d-i" or other owner.
        
        qname
            name string, e.g. "pkgsel/update-policy".
        
        qtype
            type string, e.g. "boolean", "string", "select", or "multiselect".
        
        qvalue
            value string.
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        if not qowner:
            qowner = "d-i"
        preseedRegex = re.compile(r"(?m)^([ \t]*" + qowner + r"[ \t]+" + qname + r"[ \t]+" + qtype + r")(?:[ \t]+.*)?$")
        if re.search(preseedRegex, self._wholeContent): # pre-existing preseed for this qowner and qname
            # replace
            self._wholeContent = re.sub(preseedRegex,
                                        r"\g<1>   " + qvalue,
                                        self._wholeContent)
        else: # no pre-existing preseed for this qowner and qname
            # append
            self._wholeContent = self._wholeContent + "\n#\n" + qowner + "   " + qname + "   " + qtype + "   " + qvalue + "\n"
        return self

    def addPreseedCommandLine(self, qowner, qname, command):
        """Add an additional line to an existing preseed command.
        
        qowner
            "d-i" or other owner.
        
        qname
            name string, e.g. "preseed/late_command".
        
        command
            command string, e.g. "in-target apt-get -y install curl".
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        if not qowner:
            qowner = "d-i"
        self._wholeContent = re.sub(r"(?ms)^([ \t]*" + qowner + r"[ \t]+" + qname + r"[ \t]+string[ \t]+\S+.*?[^\\])$",
                                    r"\g<1>" + " ; \\\n  " + command,
                                    self._wholeContent)
        return self

    def replaceLang(self, lang):
        """Replace lang option.
        
        lang
            e.g. "de_DE.UTF-8" to replace "en_US.UTF-8".
            
            As implemented does not do any sanity checking.
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        self.setPreseedValue("d-i", "debian-installer/locale", "string", lang)
        return self

    def replaceHostname(self, hostname):
        """Replace hostname value.
        
        hostname
            new hostname.
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        self.setPreseedValue("d-i", "netcfg/get_hostname", "string", hostname)
        return self

    @classmethod
    def cryptedPwd(cls, plainPwd):
        """Encrypt in a format acceptable for preseed."""
        # as implemented MD5 hash it, e.g. $1$sodiumch$UqZCYecJ/y5M5pp1x.7C4/
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
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        isCrypted = re.match(r"\$", pwd)
        if not isCrypted:
            pwd = self.cryptedPwd(pwd)
            isCrypted = True
        self.setPreseedValue("d-i", "passwd/root-password-crypted", "password", pwd)
        return self

    def setUser(self, username, pwd=None, fullname=None):
        """Set the one user Ubuntu preseed can set up.
        
        For Ubuntu, a full name is effectively required.
        Also, apparently only one user can be set by Ubuntu preseed.
        
        username
            username to set.
            
            The Linux username.
        
        pwd
            pwd will be encrypted.  If starting with $ it is assumed to be encrypted already.
        
        fullname
            the user's full name, which Ubuntu apparently expects to be given.
            
            If None then default to username.capitalize().
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        if fullname is None:
            fullname = username.capitalize()
        if pwd:
            # if pwd starts with $ then assume encrypted
            isCrypted = re.match(r"\$", pwd)
            if not isCrypted:
                pwd = self.cryptedPwd(pwd)
                isCrypted = True
        else:
            isCrypted = False
        self.setPreseedValue("d-i", "passwd/user-fullname", "string", fullname)
        self.setPreseedValue("d-i", "passwd/username", "string", username)
        self.setPreseedValue("d-i", "passwd/user-password-crypted", "password", pwd)
        return self

    def addNetworkConfigurationStatic(self, device,
                                      ipaddress, netmask="255.255.255.0", gateway=None, nameservers=None):
        """Add an additional network device with static IP.
        
        As implemented only supports IPv4.
        
        device
            a string, e.g. "eth0".
            
            Should be increased past "eth0" if adding more than one additional configuration.
            
            As implemented there is no protection against a conflict in case there would be a
            pre-existing network configuration for the device.
        
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
        # no luck with preseed, hence write into /etc/network/interfaces
        # sanity check
        normalizedStaticIp = NetworkConfigurationStaticParameters.normalizeStaticIp(ipaddress, netmask, gateway, nameservers)
        networkConfigurationToAdd = "\n".join([
            r"#",
            r"# Network interface " + device,
            r"auto " + device,
            r"iface " + device + r" inet static",
            r"  address " + normalizedStaticIp.ipaddress,
            r"  netmask " + normalizedStaticIp.netmask,
            r"  gateway " + normalizedStaticIp.gateway,
            r"  dns-nameservers " + " ".join(normalizedStaticIp.nameservers),
            ])
        # cannot use \n because ubiquity installer echo apparently doesn't take option -e
        for line in networkConfigurationToAdd.split("\n"):
            self.addPreseedCommandLine("ubiquity", "ubiquity/success_command",
                                       r'echo "' + line + r'" >> /target/etc/network/interfaces')
        return self

    def addNetworkConfigurationDhcp(self, device):
        """Add an additional network device with DHCP.
        
        device
            a string, e.g. "eth0".
            
            Should be increased past "eth0" if adding more than one additional configuration.
            
            As implemented there is no protection against a conflict in case there would be a
            pre-existing network configuration for the device.
        
        return
            self, for daisychaining."""
        # no luck with preseed, hence write into /etc/network/interfaces
        networkConfigurationToAdd = "\n".join([
            r"#",
            r"# Network interface " + device,
            r"auto " + device,
            r"iface " + device + r" inet dhcp",
            ])
        # cannot use \n because ubiquity installer echo apparently doesn't take option -e
        for line in networkConfigurationToAdd.split("\n"):
            self.addPreseedCommandLine("ubiquity", "ubiquity/success_command",
                                       r'echo "' + line + r'" >> /target/etc/network/interfaces')
        return self

    def addPackage(self, package):
        """Add package or package group to %packages section.
        
        return
            self, for daisychaining."""
        self.addPreseedCommandLine("ubiquity", "ubiquity/success_command",
                                   r"in-target apt-get -y install " + package)
        return self

    def setUpgradeNone(self):
        """Set whether to upgrade packages after debootstrap to "none".
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        self.setPreseedValue("d-i", "pkgsel/upgrade", "select", "none")
        return self

    def setUpgradeSafe(self):
        """Set whether to upgrade packages after debootstrap to "safe-upgrade".
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        self.setPreseedValue("d-i", "pkgsel/upgrade", "select", "safe-upgrade")
        return self

    def setUpgradeFull(self):
        """Set whether to upgrade packages after debootstrap to "full-upgrade".
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        self.setPreseedValue("d-i", "pkgsel/upgrade", "select", "full-upgrade")
        return self

    def setUpdatePolicyNone(self):
        """Set policy for applying updates to "none" (no automatic updates).
        
        No automatic updates.
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        self.setPreseedValue("d-i", "pkgsel/update-policy", "select", "none")
        return self

    def setUpdatePolicyUnattended(self):
        """Set policy for applying updates to "unattended-upgrades"
        (install security updates automatically).
        
        Install security updates automatically.
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        self.setPreseedValue("d-i", "pkgsel/update-policy", "select", "unattended-upgrades")
        return self

    def setSwappiness(self, swappiness):
        """Set swappiness.
        
        swappiness
            an int between 0 and 100.
        
        return
            self, for daisychaining."""
        swappiness = int(swappiness) # precaution
        if not 0 <= swappiness <= 100:
            raise Exception("swappiness must be between 0 and 100, cannot be {0}".format(swappiness))
        swappiness = str(swappiness)
        # will have effect from next booting onwards,
        # then verifiable by looking at cat /proc/sys/vm/swappiness
        setSwappinessCommand = \
            r"sysctlconf='/target/etc/sysctl.conf' ; " \
          + r"if ( grep -q '^vm.swappiness=' $sysctlconf ) ; then" \
          + r" sed -i -e 's/^vm.swappiness=.*/vm.swappiness=" + swappiness + r"/' $sysctlconf ; else" \
          + r" echo '' >> $sysctlconf ; echo '#' >> $sysctlconf ; echo 'vm.swappiness=" + swappiness + r"' >> $sysctlconf ; fi"
        # simply append
        # in case of multiple invocations last one would be effective
        self.addPreseedCommandLine("ubiquity", "ubiquity/success_command", setSwappinessCommand)
        return self

if __name__ == "__main__":
    from nrvr.distros.ub.rel1404.preseedtemplates import UbPreseedTemplates
    from nrvr.util.nameserver import Nameserver
    _preseedFileContent = UbPreseedFileContent(UbPreseedTemplates.usableUbWithGuiPreseedTemplate001)
    _preseedFileContent.replaceLang("de_DE.UTF-8")
    _preseedFileContent.replaceHostname("test-hostname-101")
    _preseedFileContent.replaceRootpw("redwoods")
    _preseedFileContent.setUser("jack", pwd="rainbow")
    _preseedFileContent.setUser("jill", pwd="sunshine")
    _preseedFileContent.addNetworkConfigurationDhcp("eth0")
    _preseedFileContent.addNetworkConfigurationStatic("eth1", "10.123.45.67")
    _preseedFileContent.addNetworkConfigurationStatic(device="eth2",
                                                      ipaddress="10.123.45.67",
                                                      netmask="255.255.255.0",
                                                      gateway="10.123.45.2",
                                                      nameservers=Nameserver.list)
    _preseedFileContent.addPackage("default-jre")
    _preseedFileContent.setUpgradeNone()
    _preseedFileContent.setUpdatePolicyNone()
    _preseedFileContent.setSwappiness(30)
    print _preseedFileContent.string
