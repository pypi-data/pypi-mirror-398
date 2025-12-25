"""
Documentation for setup.py files is at https://setuptools.readthedocs.io/en/latest/setuptools.html
"""

import setuptools

# Import the README.md file contents
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(name='heaserver-folders-aws-s3',
                 version='1.20.0',
                 description='The HEA AWS S3 bucket folder service.',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 url='https://risr.hci.utah.edu',
                 author='Research Informatics Shared Resource, Huntsman Cancer Institute, Salt Lake City, UT',
                 author_email='Andrew.Post@hci.utah.edu',
                 python_requires='>=3.10',
                 package_dir={'': 'src'},
                 packages=['heaserver.folderawss3'],
                 package_data={'heaserver.folderawss3': ['wstl/*.json']},
                 install_requires=[
                     'heaserver~=1.48.0'
                 ],
                 license='Apache License 2.0',
                 classifiers=[
                     'Development Status :: 5 - Production/Stable',
                     'Intended Audience :: Developers',
                     'Intended Audience :: Science/Research',
                     'Framework :: AsyncIO',
                     'Environment :: Web Environment',
                     'Natural Language :: English',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python :: 3',
                     'Programming Language :: Python :: 3.10',
                     'Programming Language :: Python :: 3.11',
                     'Programming Language :: Python :: 3.12',
                     'Topic :: Software Development',
                     'Topic :: Scientific/Engineering',
                     'Topic :: Scientific/Engineering :: Bio-Informatics',
                     'Topic :: Scientific/Engineering :: Information Analysis',
                     'Topic :: Scientific/Engineering :: Medical Science Apps.'
                 ],
                 entry_points={
                     'console_scripts': [
                         'heaserver-folders-aws-s3 = heaserver.folderawss3.startup:main'
                     ]
                 }
                 )
