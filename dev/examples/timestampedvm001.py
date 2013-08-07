#!/usr/bin/python

"""Example use of NrvrCommander.

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2013.
Modified BSD License"""

import os.path

from nrvr.util.requirements import SystemRequirements
from nrvr.util.times import Timestamp
from nrvr.vm.vmware import VMwareHypervisor

# TODO document this is a good way to preflight check
SystemRequirements.commandsRequiredByImplementations([VMwareHypervisor],
                                                     verbose=True)
# TODO document this is a good way to preflight check
VMwareHypervisor.localRequired()

# BEGIN not really necessary, just showing how to
# TODO document this way of making new VM names and directories
# timestamp to the microsecond should be good enough
exampleName = "example" + Timestamp.microsecondTimestamp()
exampleVmxFilePath = os.path.join(VMwareHypervisor.local.suggestedDirectory, exampleName, exampleName + ".vmx")
print exampleVmxFilePath
# END not really necessary, just showing how to

