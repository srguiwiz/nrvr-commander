#!/bin/bash
#
THIS_SCRIPT_DIR=$( cd "$( dirname "$0" )" && pwd )
mkdir -p $THIS_SCRIPT_DIR/docs/api
cd $THIS_SCRIPT_DIR/docs/api
#
find ../../src -wholename '*nrvr*' | cut -c 11- | grep -v '__' | grep -v '^build/' | grep -v '.pyc$' | cut -f1 -d'.' | sed 's/\//./g' | xargs pydoc -w
