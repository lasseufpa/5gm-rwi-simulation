#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='rwisimulation',
      version='1.1.2',
      description='Run simulations in Remcom Wireless InSite',
      author='LASSE',
      author_email='pedosb@gmail.com',
      url='https://gitlab.lasse.ufpa.br/software/python-machine-learning/rwi-simulation',
      packages=['rwisimulation'],
      entry_points={
          'console_scripts': [
              'rwi-simulation = rwisimulation.simulation:main',
              'rwi-save-tfrecord = rwisimulation.tfrecord:main [tf,shapely]'
          ]
      },
      install_requires=['numpy(>=1.14)', 'rwiparsing', 'rwimodeling'],
      extras_require={
          'tf': 'tensorflow(>=1.4)',
          'shapely': 'Shapely(>=1.6.3)',
      },
      dependency_links=[
          'git+https://oauth2:GGh9FfxwbqX4pubGGyLY@gitlab.lasse.ufpa.br/software/python-machine-learning/rwi-parsing@master#egg=rwiparsing',
          'git+https://oauth2:GGh9FfxwbqX4pubGGyLY@gitlab.lasse.ufpa.br/software/python-machine-learning/rwi-3d-modeling@master#egg=rwimodeling',
      ])