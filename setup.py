"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='scipion-em-defmap',  # Required
    version='3.0.1',  # Required
    description='Scipion defmap plugin.',  # Required
    long_description=long_description,  # Optional
    url='https://github.com/Sofia-GMT/scipion-em-defmap',  # Optional
    author='Sofía González Matatoros',  # Optional
    author_email='sofia.gonzalez.10147@gmail.com',  # Optional
    keywords='scipion cryoem imageprocessing scipion-3.0 molecular-dynamics',  # Optional
    packages=find_packages(),
    install_requires=[requirements],
    entry_points={'pyworkflow.plugin': 'defmap = defmap'},
    package_data={  # Optional
       'defmap': ['defmap_logo.png', 'protocols.conf'],
    }
)
