#!/usr/bin/python

import os
import sys

scriptDirectory = os.path.dirname(os.path.abspath(__file__))
setupDirectory = os.path.join(scriptDirectory, "src")
setupScript = os.path.join(setupDirectory, "setup.py")

os.chdir(setupDirectory)
# do actual install
status = os.system(setupScript + " install")
status = status >> 8 # because os.system returns an os.wait kind of exit status
# exit code to alert
# e.g. in case permission denied
# so make-docs-api.py can know
sys.exit(status)
