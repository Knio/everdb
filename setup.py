__license__ = '''
This file is part of everdb.

everdb is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

everdb is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General
Public License along with everdb.  If not, see
<http://www.gnu.org/licenses/>.
'''
# pylint: disable=bad-whitespace

# http://guide.python-distribute.org/creation.html

from setuptools import setup

import imp
_version = imp.load_source("everdb._version", "everdb/_version.py")

long_description = open('README.md').read()

# PyPI only supports (an old version of?) ReST.
# Doesn't seem to be compatable with Pandoc. Shame on you.

# try:
#   import pypandoc
#   long_description = pypandoc.convert(
#     long_description, 'rst', format='markdown_github')
# except:
#   import traceback
#   traceback.print_exc()

setup(
  name    = 'everdb',
  version = _version.__version__,
  author  = 'Tom Flanagan and knivey',
  author_email = 'tom@zkpq.ca',
  license = 'LICENSE.txt',
  url     = 'http://github.com/Knio/everdb/',

  description      = 'everdb is a fast embedded database for python',
  long_description = long_description,
  keywords         = 'python database emedded',

  classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: Implementation :: PyPy',
    'Topic :: Database',
    'Topic :: Database :: Database Engines/Servers',
  ],

  packages = ['everdb'],
  include_package_data = True,
  install_requires=['msgpack-python',]
)
