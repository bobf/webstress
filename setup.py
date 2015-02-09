#!/usr/bin/env python
from setuptools import setup

setup(name='WebStress',
      version='1.0',
      description='Python Distribution Utilities',
      author='Bob Farrell',
      author_email='robertanthonyfarrell@gmail.com',
      packages=['webstress'],
      install_requires=[
        'twisted==15.0.0',
        'pyyaml==3.11'
       ],
     )
