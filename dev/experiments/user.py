#!/usr/bin/python

# just some testing of determining user

import getpass
import pwd
import os

print pwd.getpwuid(os.getuid())[0]

print getpass.getuser()

print os.getlogin()

