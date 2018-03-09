#!/bin/bash

set -e

for version in '2.7' '3.6'; do
    echo "Testing Python ${version}"
    virtualenv -p python${version} venv_${version}
    bash -c "source venv_${version}/bin/activate && pip install -r requirements.txt && python demo.py"
done
