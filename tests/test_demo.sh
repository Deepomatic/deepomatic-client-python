#!/bin/bash

set -e

# Copy the demo outside of the package
cp demo.py /tmp/demo.py
echo "Testing with $(python --version)"
python /tmp/demo.py
