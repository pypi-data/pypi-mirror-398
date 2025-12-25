# =============================================================================
# Copyright (C) 2025 Commissariat a l'energie atomique et aux energies alternatives (CEA)
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the names of CEA, nor the names of the contributors may be used to
#   endorse or promote products derived from this software without specific
#   prior written  permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# =============================================================================

from setuptools import setup, find_namespace_packages


def read_version():
    ns = {}
    with open("src/deisa/core/__version__.py") as f:
        exec(f.read(), ns)
    return ns["__version__"]


def readme():
    with open('README.md', 'r') as f:
        return f.read()


setup(name='deisa-core',
      version=read_version(),
      description='Core Deisa tools and utilities.',
      long_description=readme(),
      long_description_content_type='text/markdown',
      license='MIT',
      url='https://github.com/deisa-project/deisa-core',
      project_urls={
          'Bug Reports': 'https://github.com/deisa-project/deisa-core/issues',
          'Source': 'https://github.com/deisa-project/deisa-core',
      },
      author='Benoît Martin',
      author_email='bmartin@cea.fr',
      python_requires='>=3.8',
      keywords='deisa',
      package_dir={'': 'src'},
      packages=find_namespace_packages(where='src', include=['deisa.core']),
      install_requires=["dask", "numpy"],
      extras_require={
          "test": [
              "pytest",
              "dask",
              "distributed",
              "numpy",
          ],
      },
      classifiers=[
          "Programming Language :: Python :: 3.8",
          "Operating System :: OS Independent",
          "Development Status :: 3 - Alpha"
      ]
      )
