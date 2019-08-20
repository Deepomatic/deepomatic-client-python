#!/bin/bash

set -e

apt-get update && apt-get install -y build-essential
pip install -r requirements.txt
pip install pytest==4.0.2 \
            pytest-cov==2.6.1 \
            pytest-voluptuous==1.1.0 \
            httpretty==0.9.6 # for testing
