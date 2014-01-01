#!/usr/bin/python

"""Send a command to a VM.
A useful utility by itself, try its --help option.

Assumes .ports file to exist and to have an entry for ssh for the user.

Idea and first implementation - Leo Baschy <srguiwiz12 AT nrvr DOT com>

Public repository - https://github.com/srguiwiz/nrvr-commander

Copyright (c) Nirvana Research 2006-2014.
Modified BSD License"""

from optparse import OptionParser

from nrvr.remote.ssh import SshCommand
from nrvr.util.requirements import SystemRequirements
from nrvr.vm.vmware import VMwareMachine

optionsParser = OptionParser(usage="%prog [options] vmxfile command [arguments]",
                             description=
"""Send a command to a VM.

Assumes .ports file to exist and to have an entry for ssh for the user.""",
                             version="%prog 1.0")
optionsParser.add_option("-u", "--user", type="string", dest="user",
                         help="user, default %default", default="root")
(options, args) = optionsParser.parse_args()

# preflight checks
SystemRequirements.commandsRequiredByImplementations([SshCommand],
                                                     verbose=False)

if len(args) < 1:
    optionsParser.error("did not find vmxfile argument")
vmx = args.pop(0)
vm = VMwareMachine(vmx)

if len(args) < 1:
    optionsParser.error("did not find command argument")
commandAndArguments = args[0:]

sshCommand = vm.sshCommand(commandAndArguments, user=options.user)

print sshCommand.output
