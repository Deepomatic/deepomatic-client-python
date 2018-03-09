#!/bin/bash

if [ `which pip | wc -l` = "0" ]; then
    echo "N" | apt-get --no-install-recommends -y install openssh-client
    apt-get --no-install-recommends -y install python-setuptools python-dev libffi-dev libssl-dev curl g++
    curl https://bootstrap.pypa.io/get-pip.py | python
    pip install --upgrade pip
fi
