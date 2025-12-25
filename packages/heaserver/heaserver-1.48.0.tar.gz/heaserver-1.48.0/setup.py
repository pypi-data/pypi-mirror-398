"""
Documentation for setup.py files is at https://setuptools.readthedocs.io/en/latest/setuptools.html
"""

from setuptools import setup, find_namespace_packages

# Import the README.md file contents
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='heaserver',
      version='1.48.0',
      description='The server side of HEA.',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://risr.hci.utah.edu',
      author='Research Informatics Shared Resource, Huntsman Cancer Institute, Salt Lake City, UT',
      author_email='Andrew.Post@hci.utah.edu',
      python_requires='>=3.10',
      package_dir={'': 'src'},
      packages=find_namespace_packages(where='src'),
      package_data={'heaserver.service': ['py.typed', 'jsonschemafiles/*']},
      license='Apache License 2.0',
      install_requires=[
          'heaobject~=1.36.0',
          'aiohttp~=3.10.10',  # aiohttp-swagger3 doesn't support aiohttp 3.11 yet.
          'aiodns; platform_system!="Windows"',  # Optional aiohttp speedup; requires the older Windows event loop, so disable this dependency on Windows for now.
          'pycares>=4.9.0,<5.0.0; platform_system!="Windows"',  # aiodns depends on it.
          'Brotli',  # Optional aiohttp speedup.
          'aiohttp-remotes~=1.3.0',
          'motor~=3.6.0',
          'motor-types~=1.0.0b4',
          'accept-types~=0.4.1',
          'mongoquery~=1.4.2',
          'jsonschema~=4.23.0',
          'jsonmerge~=1.9.2',
          'requests~=2.31.0',  # Upgrade to 2.32.* when docker >= 7.1.0.
          'types-requests>=2.32.0.20241016',  # Should be set at same version as requests.
          'boto3[crt]~=1.37.25',
          'botocore~=1.37.25',
          'boto3-stubs[essential,sts,account,organizations,iam]~=1.37.25',
          'botocore-stubs[essential]~=1.37.25',
          'freezegun~=1.5.1',
          'regex~=2024.11.6',
          'aio-pika==9.5.1',
          'simpleeval~=1.0.3',
          'opensearch-py[async]~=2.6.0',
          'cachetools~=5.5.0',
          'types-cachetools~=5.5.0.20240820',
          'types-pywin32; platform_system=="Windows"',
          'uvloop~=0.21.0; platform_system!="Windows"',
          'aiodiskqueue~=0.1.2',
          'aiosqlite~=0.21.0'
      ],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Programming Language :: Python :: 3.12',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Software Development',
          'Topic :: Scientific/Engineering',
          'Topic :: Scientific/Engineering :: Bio-Informatics',
          'Topic :: Scientific/Engineering :: Information Analysis',
          'Topic :: Scientific/Engineering :: Medical Science Apps.'
      ]
      )
