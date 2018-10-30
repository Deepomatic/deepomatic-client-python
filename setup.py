import os
from setuptools import find_packages, setup
try: # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
    from pip.req import parse_requirements

from deepomatic import __version__

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

# Read requirements
install_reqs = parse_requirements('requirements.txt', session='hack')

setup(
    name='deepomatic',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    description='Deepomatic API client',
    long_description=README,
    url='https://www.deepomatic.com',
    author='deepomatic',
    author_email='support@deepomatic.com',
    install_requires=[str(ir.req) for ir in install_reqs],
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ]
)
