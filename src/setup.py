#!/usr/bin/python

from distutils.core import setup

setup(name="NrvrCommander",
      version="1.3.2",
      description="Tools for automation.",
      long_description="""Tools for automation.
      
      Modules provides by this package are
      * nrvr.diskimage.isoimage
      * nrvr.distros.el.clone
      * nrvr.distros.el.gnome
      * nrvr.distros.el.kickstart
      * nrvr.distros.el.kickstarttemplates
      * nrvr.distros.el.ssh
      * nrvr.distros.el.util
      * nrvr.distros.ub.kickstarttemplates
      * nrvr.machine.ports
      * nrvr.process.commandcapture
      * nrvr.remote.ssh
      * nrvr.script.util
      * nrvr.util.classproperty
      * nrvr.util.download
      * nrvr.util.ipaddress
      * nrvr.util.nameserver
      * nrvr.util.networkinterface
      * nrvr.util.requirements
      * nrvr.util.times
      * nrvr.util.user
      * nrvr.vm.vmware
      * nrvr.vm.vmwaretemplates
      * nrvr.xml.etree""",
      packages=["nrvr",
                "nrvr.diskimage",
                "nrvr.distros",
                "nrvr.distros.el",
                "nrvr.distros.ub",
                "nrvr.machine",
                "nrvr.process",
                "nrvr.remote",
                "nrvr.util",
                "nrvr.vm",
                "nrvr.xml"],
      maintainer='Nirvana Research',
      maintainer_email='nrvr.commander.python@nrvr.com',
      license="Copyright (c) Nirvana Research 2006-2013, Modified BSD License",
      )
