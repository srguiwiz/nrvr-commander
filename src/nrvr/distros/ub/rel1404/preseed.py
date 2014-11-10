#!/usr/bin/python

"""nrvr.distros.ub.rel1404.preseed - Create and manipulate Ubuntu preseed files

Classes provided by this module include
* Ub1404IsoImage
* UbPreseedFileContent

To be improved as needed.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

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

    def modificationsIncludingPreseedFile(self, _preseedFileContent):
        """Construct and return a list of modifications to be passed to method cloneWithModifications.
        
        This method is called by method cloneWithAutoBootingPreseed, which takes the returned list
        and passes it to method cloneWithModifications.
        
        As implemented known to support Ubuntu 14.04 LTS.
        
        _preseedFileContent
            A DistroPreseedFileContent object.
        
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
             r" automatic-ubiquity"
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

    def cloneWithAutoBootingPreseed(self, _preseedFileContent, modifications=[], cloneIsoImagePath=None):
        """Clone with preseed file added and modified to automatically boot with it.
        
        For more on behavior see documentation of class IsoImage method cloneWithModifications.
        
        For details of modifications see method modificationsIncludingPreseedFile,
        which is expected to be different per release specific subclass.
        
        _preseedFileContent
            A UbPreseedFileContent object.
        
        cloneIsoImagePath
            if not given then in same directory with a timestamp in the filename.
        
        return
            IsoImage(cloneIsoImagePath)."""
        # modifications, could be quite different per release specific subclass
        modifications.extend(self.modificationsIncludingPreseedFile(_preseedFileContent))
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

    def replaceLang(self, lang):
        """Replace lang option.
        
        lang
            e.g. "de_DE.UTF-8" to replace "en_US.UTF-8".
            
            As implemented does not do any sanity checking.
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        self._wholeContent = re.sub(r"(?m)^([ \t]*d-i[ \t]+debian-installer/locale[ \t]+string[ \t]+)\S+.*$",
                                    r"\g<1>" + lang,
                                    self._wholeContent)
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
        self._wholeContent = re.sub(r"(?m)^([ \t]*d-i[ \t]+passwd/root-password-crypted[ \t]+password[ \t]+)\S+.*$",
                                    r"\g<1>" + pwd,
                                    self._wholeContent)
        return self

    def replaceHostname(self, hostname):
        """Replace hostname value.
        
        hostname
            new hostname.
        
        return
            self, for daisychaining."""
        # see https://help.ubuntu.com/14.04/installation-guide/example-preseed.txt
        self._wholeContent = re.sub(r"(?m)^([ \t]*d-i[ \t]+netcfg/get_hostname[ \t]+string[ \t]+)\S+.*$",
                                    r"\g<1>" + hostname,
                                    self._wholeContent)
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
        self._wholeContent = re.sub(r"(?m)^([ \t]*d-i[ \t]+passwd/user-fullname[ \t]+string[ \t]+)\S+.*$",
                                    r"\g<1>" + fullname,
                                    self._wholeContent)
        self._wholeContent = re.sub(r"(?m)^([ \t]*d-i[ \t]+passwd/username[ \t]+string[ \t]+)\S+.*$",
                                    r"\g<1>" + username,
                                    self._wholeContent)
        self._wholeContent = re.sub(r"(?m)^([ \t]*d-i[ \t]+passwd/user-password-crypted[ \t]+password[ \t]+)\S+.*$",
                                    r"\g<1>" + pwd,
                                    self._wholeContent)
        return self

if __name__ == "__main__":
    from nrvr.distros.ub.rel1404.preseedtemplates import UbPreseedTemplates
    _preseedFileContent = UbPreseedFileContent(UbPreseedTemplates.usableUbPreseedTemplate001)
    _preseedFileContent.replaceLang("de_DE.UTF-8")
    _preseedFileContent.replaceRootpw("redwoods")
    _preseedFileContent.replaceHostname("test-hostname-101")
    _preseedFileContent.setUser("jack", pwd="rainbow")
    _preseedFileContent.setUser("jill", pwd="sunshine")
    print _preseedFileContent.string
