#!/usr/bin/python
#
# may have to sudo this script, for installlocally.py
#

import glob
import os
import os.path
import sys

scriptDirectory = os.path.dirname(os.path.abspath(__file__))
#
os.chdir(scriptDirectory)
# intentionally run installlocally.py and fail if fails,
# because pydoc documents what is installed
installlocallyScript = os.path.join(scriptDirectory, "installlocally.py")
status = os.system(installlocallyScript)
status = status >> 8 # because os.system returns an os.wait kind of exit status
if status:
    # exit code to alert
    # e.g. in case permission denied
    # so calling script can know
    sys.exit(status)
#
docsApiDirectory = os.path.join(scriptDirectory, "docs/api")
os.chdir(docsApiDirectory)
#
oldDocsApiFilesGlob = glob.glob(os.path.join(docsApiDirectory, "nrvr*.html"))
for oldFilename in oldDocsApiFilesGlob:
    os.remove(oldFilename)
#
srcDirectory = os.path.join(scriptDirectory, "src")
srcDirectoryNameLength = len(srcDirectory)
srcNrvrDirectory = os.path.join(scriptDirectory, "src/nrvr")
for top, dirs, files in os.walk(srcNrvrDirectory):
    packageName = top[srcDirectoryNameLength+1:].replace(os.sep, ".")
    print "documenting package " + packageName
    os.system("pydoc -w " + packageName)
    for nm in files:
        if nm.endswith(".py") and not nm.startswith("__"):
            sourceFile = os.path.join(top, nm)
            packageName = sourceFile[srcDirectoryNameLength+1:-3].replace(os.sep, ".")
            print "documenting package " + packageName
            os.system("pydoc -w " + packageName)
