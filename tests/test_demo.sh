#!/bin/bash

set -e

# Copy the demo outside of the package
cp demo.py /tmp/demo.py

for version in '2.7' '3.6'; do
    echo "Testing Python ${version}"
    virtualenv -p python${version} venv_${version}
    bash -c "source venv_${version}/bin/activate && pip install . && python /tmp/demo.py"
done
