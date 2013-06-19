#!/usr/bin/python

import os

scriptDirectory = os.path.dirname(os.path.abspath(__file__))
setupDirectory = os.path.join(scriptDirectory, "src")
setupScript = os.path.join(setupDirectory, "setup.py")

os.chdir(setupDirectory)
os.system(setupScript + " install")
