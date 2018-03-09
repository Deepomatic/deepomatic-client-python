#!/bin/bash

echo "N" | apt-get --no-install-recommends -y install openssh-client
apt-get --no-install-recommends -y install python3-setuptools python3-dev libffi-dev libssl-dev curl g++
curl https://bootstrap.pypa.io/get-pip.py | python3
pip3 install --upgrade pip

# Sets python3 as a python alternative with a low priority
update-alternatives --install /usr/bin/python python /usr/bin/python3 0

# Install requirements
pip3 install -r requirements.txt
