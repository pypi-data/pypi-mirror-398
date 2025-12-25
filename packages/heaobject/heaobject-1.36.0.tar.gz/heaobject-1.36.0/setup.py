"""
Documentation for setup.py files is at https://setuptools.readthedocs.io/en/latest/setuptools.html
"""

import setuptools

# Import the README.md file contents
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(name='heaobject',
                 version='1.36.0',
                 description='Data and other classes that are passed into and out of HEA REST APIs.',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 url='https://risr.hci.utah.edu',
                 author='Research Informatics Shared Resource, Huntsman Cancer Institute, Salt Lake City, UT',
                 author_email='Andrew.Post@hci.utah.edu',
                 python_requires='>=3.10',
                 package_dir={'': 'src'},
                 packages=['heaobject'],
                 package_data={'heaobject': ['py.typed']},
                 license='Apache License 2.0',
                 install_requires=[
                     'multidict~=6.1.0',
                     'yarl~=1.18.3',  # Sync version with aiohttp's dependencies.
                     'humanize~=4.11.0',
                     'email-validator~=2.3.0',
                     'uritemplate~=4.1.1',
                     'python-dateutil~=2.9.0.post0',  # Remove when we remove support for python 3.10.
                     'tzlocal~=5.2',
                     'orjson~=3.10.12',
                     'babel~=2.16.0',
                     'pyxdg~=0.28',
                     'types-pyxdg~=0.28.0.20250622',
                     'wrapt~=1.17.2',  # Sync version with whatever depends on it in heaserver's dependencies.
                     'cryptography~=44.0.0'  # Sync version with whatever depends on it in heaserver's dependencies.
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
