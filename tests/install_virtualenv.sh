#!/bin/bash

echo "N" | apt-get --no-install-recommends -y install openssh-client
apt-get install python-virtualenv
