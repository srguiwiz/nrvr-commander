#!/usr/bin/python

# demoing some control of virtual machines

from nrvr.util.ipaddress import IPAddress
from nrvr.util.user import ScriptUser
from nrvr.vm.vmware import VMwareMachine, VMwareHypervisor

ipaddress = "192.168.4.171"
name = IPAddress.nameWithNumber("example", ipaddress)
exampleVm = VMwareMachine(ScriptUser.loggedIn.userHomeRelative("vmware/examples/%s/%s.vmx" % (name, name)))
VMwareHypervisor.local.start(exampleVm.vmxFilePath, gui=True)
print exampleVm.sshCommand(["ls nonexistent ; echo `hostname`"]).output

import shutil
import tempfile
from nrvr.util.time import Timestamp

_exampleDir = os.path.join(tempfile.gettempdir(), Timestamp.microsecondTimestamp())
os.mkdir(_exampleDir, 0755)
try:
    _sendDir = os.path.join(_exampleDir, "send")
    os.mkdir(_sendDir, 0755)
    _exampleFile1 = os.path.join(_sendDir, "example1.txt")
    with open(_exampleFile1, "w") as outputFile:
        outputFile.write("this is an example\n" * 1000000)
    _scpExample1 = exampleVm.scpPutCommand(fromHostPath=_exampleFile1, toGuestPath="~/example1.txt")
    print "returncode=" + str(_scpExample1.returncode)
    print "output=" + _scpExample1.output
    _scpExample2 = exampleVm.scpGetCommand(fromGuestPath="/etc/hosts", toHostPath=_exampleFile1)
    print "returncode=" + str(_scpExample2.returncode)
    print "output=" + _scpExample2.output
    with open(_exampleFile1, "r") as inputFile:
        _exampleFile1Content = inputFile.read()
    print "content=\n" + _exampleFile1Content
finally:
    shutil.rmtree(_exampleDir)

print exampleVm.sshCommand(["ls nonexistent"]).output

