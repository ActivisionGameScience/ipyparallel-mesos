#!/usr/bin/env python

from setuptools import setup, find_packages

from pip.req import parse_requirements
import pip
requirements = [
    str(req.req) for req in parse_requirements('requirements.txt', session=pip.download.PipSession())
]

setup(name='ipyparallel_mesos',
      version='0.0.2',
      description='ipyparallel launchers for mesos using docker and marathon',
      author='John Dennison',
      author_email='john.dennison@activision.com',
      url = 'https://github.com/ActivisionGameScience/ipyparallel-mesos/',
      packages=find_packages(),
      install_requires=requirements
)
