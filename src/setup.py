#!/usr/bin/python

from distutils.core import setup

setup(name="NrvrCommander",
      version="1.4.9",
      description="Tools for automation.",
      long_description="""Tools for automation.
      
      Modules provides by this package are
      * nrvr.diskimage.isoimage
      * nrvr.distros.common.gnome
      * nrvr.distros.common.kickstart
      * nrvr.distros.common.ssh
      * nrvr.distros.el.clone
      * nrvr.distros.el.gnome
      * nrvr.distros.el.kickstart
      * nrvr.distros.el.kickstarttemplates
      * nrvr.distros.el.util
      * nrvr.distros.ub.gnome
      * nrvr.distros.ub.kickstart
      * nrvr.distros.ub.kickstarttemplates
      * nrvr.machine.ports
      * nrvr.process.commandcapture
      * nrvr.remote.ssh
      * nrvr.util.classproperty
      * nrvr.util.download
      * nrvr.util.ipaddress
      * nrvr.util.nameserver
      * nrvr.util.networkinterface
      * nrvr.util.registering
      * nrvr.util.requirements
      * nrvr.util.times
      * nrvr.util.user
      * nrvr.vm.vmware
      * nrvr.vm.vmwaretemplates
      * nrvr.wins.common.autounattend
      * nrvr.wins.common.cygwin
      * nrvr.wins.common.javaw
      * nrvr.wins.common.ssh
      * nrvr.wins.win7.autounattend
      * nrvr.wins.win7.autounattendtemplates
      * nrvr.xml.etree""",
      packages=["nrvr",
                "nrvr.diskimage",
                "nrvr.distros",
                "nrvr.distros.common",
                "nrvr.distros.el",
                "nrvr.distros.ub",
                "nrvr.machine",
                "nrvr.process",
                "nrvr.remote",
                "nrvr.util",
                "nrvr.vm",
                "nrvr.wins",
                "nrvr.wins.common",
                "nrvr.wins.win7",
                "nrvr.xml"],
      maintainer='Nirvana Research',
      maintainer_email='nrvr.commander.python@nrvr.com',
      license="Copyright (c) Nirvana Research 2006-2014, Modified BSD License",
      )
