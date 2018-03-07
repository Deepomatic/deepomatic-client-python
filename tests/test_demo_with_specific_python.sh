#!/bin/bash

set -e

if [ $# -lt 1 ]; then
    dmake_fail "$0: Missing arguments"
    echo "exit 1"
    exit 1
fi

VERSION=$1

VENV=venv_${VERSION}
virtualenv -p python${VERSION} ${VENV}
source ${VENV}/bin/activate

python --version
pip install -r requirements.txt
python demo.py
