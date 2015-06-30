#!/usr/bin/env python

from setuptools import setup
from Cython.Build import cythonize

setup(name='WebStress',
      version='1.0',
      description='Python Distribution Utilities',
      author='Bob Farrell',
      author_email='robertanthonyfarrell@gmail.com',
      packages=['webstress',
                'webstress.client',
                'webstress.config',
                'webstress.interfaces',
                'webstress.common',
                'twisted.plugins'],
      ext_modules=cythonize('webstress/util/cstats.pyx'),
      scripts=['scripts/webstress'],
      install_requires=[
        'twisted==15.0.0',
        'pyyaml==3.11',
        'pyopenssl==0.14',
        'service_identity==14.0.0',
        'fake-factory==0.4.2',
        'nevow==0.11.1',
        'mock==1.0.1',
        'numpy==1.9.2',
        'ampoule==0.2',
       ],
     )
