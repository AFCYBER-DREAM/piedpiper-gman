#! /usr/bin/env python
import setuptools

import os

from setuptools import find_packages, setup

setup(name='picli-gman-faas',
      use_scm_version=True,
      setup_requires=['setuptools-scm'],
      description='A sinister inter-dimensional bureaucrat that monitors the state of each FaaS.',
      classifiers=['Development Status :: 2 - Pre-Alpha',
                   'Environment :: Console',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python'],
      author='Nick Shobe',
      author_email='nickshobe@gmail.com',
      license='MIT License',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      requires=['flask-restful',
                'attrdict',
                'pyyaml',
                'peewee']
)
