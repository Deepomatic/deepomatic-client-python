#!/bin/bash

set -e

apt-get update && apt-get install -y build-essential
pip install -r requirements.txt
pip install pytest==4.0.2 # for testing
