#!/usr/bin/python

from distutils.core import setup
import sys

try:
    setup(name="NrvrCommander",
          version="1.7.2",
          description="Tools for automation.",
          long_description="""Tools for automation.
          
          Modules provides by this package are
          * nrvr.diskimage.isoimage
          * nrvr.distros.common.gnome
          * nrvr.distros.common.kickstart
          * nrvr.distros.common.ssh
          * nrvr.distros.common.util
          * nrvr.distros.el.clone
          * nrvr.distros.el.gnome
          * nrvr.distros.el.kickstart
          * nrvr.distros.el.kickstarttemplates
          * nrvr.distros.el.util
          * nrvr.distros.ub.util
          * nrvr.distros.ub.rel1204.gnome
          * nrvr.distros.ub.rel1204.kickstart
          * nrvr.distros.ub.rel1204.kickstarttemplates
          * nrvr.distros.ub.rel1404.gnome
          * nrvr.distros.ub.rel1404.preseed
          * nrvr.distros.ub.rel1404.preseedtemplates
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
                    "nrvr.distros.ub.rel1204",
                    "nrvr.distros.ub.rel1404",
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
except Exception as ex:
    # attempt same output as if no try except
    sys.stderr.write(ex)
    sys.stdout.flush()
    sys.stderr.flush()
    # exit code to alert
    # e.g. in case permission denied
    # so calling script can know
    sys.exit(1)
