#!/usr/bin/env python3
#
# command to build:
#
#     ./setup.py sdist
#

import base
import setuptools

# when building, we run this in the local directory
# sometime in the last year the install directory changed or such and it breaks at install time?
try:
  with open('PYPI.md', 'r') as readme:
    long_description = readme.read()
except FileNotFoundError:
  long_description  = ''

setuptools.setup(
    name            = 'octobase',
    version         = base.VERSION,
    author          = 'Octoboxy',
    author_email    = 'office@octoboxy.com',
    description     = 'The First Building Block For Any Python Project',
    url             = 'https://bitbucket.org/octoboxy/octobase/',
    python_requires = '>=3.9',
    classifiers     = [
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
    ],
    packages        = setuptools.find_packages(),
    long_description              = long_description,
    long_description_content_type = 'text/markdown',
)

print('Done\nCommand to upload:\n   $ twine upload dist/octobase-{}.tar.gz'.format(base.VERSION))
