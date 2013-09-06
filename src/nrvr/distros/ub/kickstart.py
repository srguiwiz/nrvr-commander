#!/usr/bin/python

"""nrvr.distros.ub.kickstart - Create and manipulate Ubuntu kickstart files

Classes provided by this module include
* UbIsoImage
* UbKickstartFileContent

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import re

import nrvr.distros.common.kickstart

class UbIsoImage(nrvr.distros.common.kickstart.DistroIsoImage):
    """An Ubuntu .iso ISO CD-ROM or DVD-ROM disk image."""

    def __init__(self, isoImagePath):
        """Create new Ubuntu IsoImage descriptor.
        
        A descriptor can describe an .iso image that does or doesn't yet exist on the host disk."""
        nrvr.distros.common.kickstart.DistroIsoImage.__init__(self, isoImagePath)

    def modificationsIncludingKickstartFile(self, _kickstartFileContent):
        """Construct and return a list of modifications to be passed to method cloneWithModifications.
        
        This method is called by method cloneWithAutoBootingKickstart, which takes the returned list
        and passes it to method cloneWithModifications.
        
        As implemented known to support Ubuntu 12.04 LTS.
        Good chance it will work with newer versions distributions.
        
        _kickstartFileContent
            A UbKickstartFileContent object.
        
        Return a list of modifications which will be passed to method cloneWithModifications."""
        if not isinstance(_kickstartFileContent, nrvr.distros.ub.kickstart.UbKickstartFileContent):
            # defense against more hidden problems
            raise Exception("not given but in need of an instance of nrvr.distros.ub.kickstart.UbKickstartFileContent")
        # a distinct label
        kickstartCustomLabel = "kscustom"
        # a distinct path
        kickstartCustomConfigurationPathOnIso = "isolinux/" + kickstartCustomLabel + ".cfg"
        # modifications
        modifications = \
        [
            # the kickstart file
            nrvr.diskimage.isoimage.IsoImageModificationFromString
            (kickstartCustomConfigurationPathOnIso,
             _kickstartFileContent.string),
            # in isolinux/txt.cfg
            # insert section with label "kscustom", first, before "label install",
            # documentation says "ks=cdrom:/directory/filename.cfg" with a single "/" slash, NOT double
            nrvr.diskimage.isoimage.IsoImageModificationByReplacement
            ("isolinux/txt.cfg",
             re.compile(r"(\r?\n)(label[ \t]+install\s)"),
             r"\1label " + kickstartCustomLabel + r"\1"
             r"  menu label Custom ^kickstart\1"
             r"  kernel /install/vmlinuz\1"
             r"  append file=/cdrom/preseed/" + kickstartCustomLabel + r".seed"
             r" initrd=/install/initrd.gz"
             r" ks=cdrom:/" + kickstartCustomConfigurationPathOnIso +
             r" --\1\2"),
            # in isolinux/txt.cfg
            # replace "default install" with "default kscustom"
            nrvr.diskimage.isoimage.IsoImageModificationByReplacement
            ("isolinux/txt.cfg",
             re.compile(r"(^|\r?\n)(default[ \t]+)(\S+)"),
             r"\1\g<2>" + kickstartCustomLabel),
            # in isolinux/isolinux.cfg
            # change to "timeout 50" measured in 1/10th seconds
            nrvr.diskimage.isoimage.IsoImageModificationByReplacement
            ("isolinux/isolinux.cfg",
             re.compile(r"(\r?\n)(timeout[ \t]+\d+)(\s)"),
             r"\1timeout 50\3"),
            # a custom preseed file preseed/kscustom.seed
            # with essentials that appear to be necessary before the kickstart file,
            # some or much of this gleaned from parts of /preseed/cli.seed,
            # possibly also from *.cfg files in /isolinux
            nrvr.diskimage.isoimage.IsoImageModificationFromString
            ("preseed/" + kickstartCustomLabel + ".seed",
             r"# essentials, more than a placeholder file for now," "\n"
             r"# some of this has been copied manually and selectively from a /preseed/cli.seed" "\n"
             r"d-i preseed/early_command string . /usr/share/debconf/confmodule; db_get debconf/priority; case $RET in low|medium) db_fset tasksel/first seen false; echo 'tasksel tasksel/first seen false' >>/var/lib/preseed/log ;; esac" "\n"
             r"d-i base-installer/kernel/altmeta string lts-quantal" "\n"
             r"# tell netcfg a specific interface to use instead of looking or asking" "\n"
             r"d-i netcfg/choose_interface select eth0" "\n"
             ),
            # put into isolinux/lang
            # installer language selection
            nrvr.diskimage.isoimage.IsoImageModificationFromString
            ("isolinux/lang",
             r"en" + "\n"
             ),
        ]
        return modifications


class UbKickstartFileContent(nrvr.distros.common.kickstart.DistroKickstartFileContent):
    """The text content of an Anaconda kickstart file for Ubuntu."""

    def __init__(self, string):
        """Create new kickstart file content container."""
        nrvr.distros.common.kickstart.DistroKickstartFileContent.__init__(self, string)

    def ubReplaceHostname(self, hostname):
        """Replace hostname value in preseed variable.
        
        hostname
            new hostname.
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        hostname = re.escape(hostname) # precaution
        commandSection = self.sectionByName("command")
        # change to hostname
        commandSection.string = re.sub(r"(?m)^([ \t]*preseed[ \t]+netcfg/get_hostname[ \t]+string[ \t]+)\S+(.*)$",
                                       r"\g<1>" + hostname + r"\g<2>",
                                       commandSection.string)
        # possibly two ways of setting hostname
        commandSection.string = re.sub(r"(?m)^([ \t]*preseed[ \t]+netcfg/hostname[ \t]+string[ \t]+)\S+(.*)$",
                                       r"\g<1>" + hostname + r"\g<2>",
                                       commandSection.string)
        return self

    _endOfNetworkInterfacesRegex = re.compile(r"(?s)(.*>[ \t]+/etc/network/interfaces[ \t]*)(\n|$)(.*)")

    def ubCreateNetworkConfigurationSection(self):
        """Create the necessary network configuration section.
        
        As implemented there is no protection against a conflict in case there would be a
        pre-existing network configuration section.
        
        return
            self, for daisychaining."""
        # no luck with preseed, hence write into /etc/network/interfaces
        postSection = self.sectionByName("%post")
        networkConfigurationToAdd = "".join(
            "\n#"
            "\n# Set network configuration"
            "\necho \"# This file describes the network interfaces available on your system\" > /etc/network/interfaces"
            "\necho \"# and how to activate them. For more information, see interfaces(5).\" >> /etc/network/interfaces"
            "\necho \"\" >> /etc/network/interfaces"
            "\necho \"# The loopback network interface\" >> /etc/network/interfaces"
            "\necho \"auto lo\" >> /etc/network/interfaces"
            "\necho \"iface lo inet loopback\" >> /etc/network/interfaces"
            "\necho \"\" >> /etc/network/interfaces"
            )
        if re.search(self._endOfNetworkInterfacesRegex, postSection.string): # pre-existing network configuration
            # insert
            postSection.string = re.sub(self._endOfNetworkInterfacesRegex,
                                        r"\g<1>" + networkConfigurationToAdd + r"\2\3",
                                        postSection.string)
        else: # no pre-existing network configuration
            # append
            postSection.string = postSection.string + networkConfigurationToAdd + "\n"

    def ubAddNetworkConfigurationStatic(self, device,
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
        normalizedStaticIp = self.normalizeStaticIp(ipaddress, netmask, gateway, nameservers)
        postSection = self.sectionByName("%post")
        networkConfigurationToAdd = "".join(
            "\necho \"#\" >> /etc/network/interfaces"
            "\necho \"# Network interface " + device + "\" >> /etc/network/interfaces"
            "\necho \"auto " + device + "\" >> /etc/network/interfaces"
            "\necho \"iface " + device + " inet static\" >> /etc/network/interfaces"
            "\necho \"  address " + normalizedStaticIp.ipaddress + "\" >> /etc/network/interfaces"
            "\necho \"  netmask " + normalizedStaticIp.netmask + "\" >> /etc/network/interfaces"
            "\necho \"  gateway " + normalizedStaticIp.gateway + "\" >> /etc/network/interfaces"
            "\necho \"  dns-nameservers " + " ".join(normalizedStaticIp.nameservers) + "\" >> /etc/network/interfaces"
            )
        if re.search(self._endOfNetworkInterfacesRegex, postSection.string): # pre-existing network configuration
            # insert
            postSection.string = re.sub(self._endOfNetworkInterfacesRegex,
                                        r"\g<1>" + networkConfigurationToAdd + r"\2\3",
                                        postSection.string)
        else: # no pre-existing network configuration
            # append
            postSection.string = postSection.string + networkConfigurationToAdd + "\n"

    def ubAddNetworkConfigurationDhcp(self, device):
        """Add an additional network device with DHCP.
        
        device
            a string, e.g. "eth0".
            
            Should be increased past "eth0" if adding more than one additional configuration.
            
            As implemented there is no protection against a conflict in case there would be a
            pre-existing network configuration for the device.
        
        return
            self, for daisychaining."""
        # no luck with preseed, hence write into /etc/network/interfaces
        postSection = self.sectionByName("%post")
        networkConfigurationToAdd = "".join(
            "\necho \"#\" >> /etc/network/interfaces"
            "\necho \"# Network interface " + device + "\" >> /etc/network/interfaces"
            "\necho \"auto " + device + "\" >> /etc/network/interfaces"
            "\necho \"iface " + device + " inet dhcp\" >> /etc/network/interfaces"
            )
        if re.search(self._endOfNetworkInterfacesRegex, postSection.string): # pre-existing network configuration
            # insert
            postSection.string = re.sub(self._endOfNetworkInterfacesRegex,
                                        r"\g<1>" + networkConfigurationToAdd + r"\2\3",
                                        postSection.string)
        else: # no pre-existing network configuration
            # append
            postSection.string = postSection.string + networkConfigurationToAdd + "\n"

    def ubActivateGraphicalLogin(self):
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
        # for each user set resolution to a reasonable size, less than maximum
        # see https://wiki.ubuntu.com/X/Config/Resolution
        postSection = self.sectionByName("%post")
        postSection.string = postSection.string + r"""
#
# For each user set resolution to a reasonable size
skeldir=/etc/skel
cdir=$skeldir/.config
mxfile=$cdir/monitors.xml
echo "writing $mxfile"
mkdir $cdir
echo '<monitors version="1">
<configuration>
  <clone>no</clone>
      <output name="default">
          <vendor>???</vendor>
          <product>0x0000</product>
          <serial>0x00000000</serial>
          <width>1024</width>
          <height>768</height>
          <rate>0</rate>
          <x>0</x>
          <y>0</y>
          <rotation>normal</rotation>
          <reflect_x>no</reflect_x>
          <reflect_y>no</reflect_y>
          <primary>yes</primary>
      </output>
  </configuration>
</monitors>' > $mxfile
"""
        return self

    def ubSetUser(self, username, pwd=None, fullname=None):
        """Set the one user Ubuntu kickstart can set up.
        
        Ubuntu kickstart differs from Enterprise Linux in syntax.
        Also, a full name is effectively required.
        Also, only one user can be set by Ubuntu kickstart.
        
        username
            username to set.
            
            The Linux username.
        
        pwd
            pwd will be encrypted.  If starting with $ it is assumed to be encrypted already.
        
        fullname
            the user's full name, which Ubuntu apparently expects to be given.
            
            Default to username.capitalize().
        
        return
            self, for daisychaining."""
        # see http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
        # see https://help.ubuntu.com/lts/installation-guide/i386/automatic-install.html
        # see https://help.ubuntu.com/12.04/installation-guide/example-preseed.txt
        if not fullname:
            fullname = username.capitalize()
        username = re.escape(username) # precaution
        fullname = re.escape(fullname) # precaution
        if pwd:
            # if pwd starts with $ then assume encrypted
            isCrypted = re.match(r"\$", pwd)
            if not isCrypted:
                pwd = self.cryptedPwd(pwd)
                isCrypted = True
        else:
            isCrypted = False
        commandSection = self.sectionByName("command")
        commandString = "user " + username \
                        + (" --password=" + pwd if pwd else "") \
                        + (" --iscrypted" if isCrypted else "") \
                        + (" --fullname=" + fullname if fullname else "")
        if re.search(r"(?m)^user\s+.*$", commandSection.string): # pre-existing user command
            # replace
            commandSection.string = re.sub(r"(?m)^user\s+.*$", re.escape(commandString), commandSection.string)
        else: # no pre-existing user command
            # append
            commandSection.string = commandSection.string + "#\n" + commandString + "\n"

    _updatePolicyRegex = re.compile(r"(?m)^[ \t]*preseed[ \t]+pkgsel/update-policy[ \t]+.*$")

    def ubSetUpdatePolicyNone(self):
        """Set policy for applying updates to "none".
        
        No automatic updates.
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/12.04/installation-guide/example-preseed.txt
        commandSection = self.sectionByName("command")
        preseedString = r"preseed pkgsel/update-policy select none"
        if re.search(self._updatePolicyRegex, commandSection.string): # pre-existing pkgsel/update-policy
            # replace
            commandSection.string = re.sub(self._updatePolicyRegex,
                                           preseedString,
                                           commandSection.string)
        else: # no pre-existing pkgsel/update-policy
            # append
            commandSection.string = commandSection.string + "#\n" + preseedString + "\n"

    def ubSetUpdatePolicyUnattended(self):
        """Set policy for applying updates to "unattended-upgrades".
        
        Install security updates automatically.
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/12.04/installation-guide/example-preseed.txt
        commandSection = self.sectionByName("command")
        preseedString = r"preseed pkgsel/update-policy select unattended-upgrades"
        if re.search(self._updatePolicyRegex, commandSection.string): # pre-existing pkgsel/update-policy
            # replace
            commandSection.string = re.sub(self._updatePolicyRegex,
                                           preseedString,
                                           commandSection.string)
        else: # no pre-existing pkgsel/update-policy
            # append
            commandSection.string = commandSection.string + "#\n" + preseedString + "\n"

if __name__ == "__main__":
    from nrvr.distros.ub.kickstarttemplates import UbKickstartTemplates
    from nrvr.util.nameserver import Nameserver
    _kickstartFileContent = UbKickstartFileContent(UbKickstartTemplates.usableKickstartTemplate001)
    _kickstartFileContent.replaceRootpw("redwood")
    _kickstartFileContent.addPackage("another-package-for-testing")
    _kickstartFileContent.removeAllPackages()
    _kickstartFileContent.addPackage("made-something-up-for-testing")
    _kickstartFileContent.replaceAllPackages(["@package-group-for-testing",
                                             "package-a-for-testing",
                                             "package-b-for-testing",
                                             "package-c-for-testing"])
    _kickstartFileContent.ubCreateNetworkConfigurationSection()
    _kickstartFileContent.ubAddNetworkConfigurationDhcp("eth0")
    _kickstartFileContent.ubAddNetworkConfigurationStatic("eth1", "10.123.45.67")
    _kickstartFileContent.ubAddNetworkConfigurationStatic(device="eth2",
                                                          ipaddress="10.123.45.67",
                                                          netmask="255.255.255.0",
                                                          gateway="10.123.45.2",
                                                          nameservers=Nameserver.list)
    _kickstartFileContent.ubActivateGraphicalLogin()
    _kickstartFileContent.ubSetUser("jack", pwd="rainbow")
    _kickstartFileContent.ubSetUser("jill", pwd="sunshine")
    _kickstartFileContent.setSwappiness(30)
    print _kickstartFileContent.string
