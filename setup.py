#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='rwisimulation',
      version='1.2.1',
      description='Run simulations in Remcom Wireless InSite',
      author='LASSE',
      author_email='pedosb@gmail.com',
      url='https://github.com/lasseufpa/5gm-rwi-simulation',
      packages=['rwisimulation', 'rwisimulation.datamodel', 'sumo'],
      entry_points={
          'console_scripts': [
              'rwi-simulation = rwisimulation.simulation:main',
              'rwi-save-tfrecord = rwisimulation.tfrecord:main [tf,shapely]'
          ]
      },
      install_requires=['numpy(>=1.14)', 'rwiparsing', 'rwimodeling', 'pyreadline'],
      extras_require={
          'tf': 'tensorflow(>=1.4)',
          'shapely': 'Shapely(>=1.6.3)',
      },
      dependency_links=[
          'git+https://github.com/lasseufpa/5gm-rwi-parsing.git@master#egg=rwiparsing',
          'git+https://github.com/lasseufpa/5gm-rwi-3d-modeling.git@master#egg=rwimodeling',
      ])
