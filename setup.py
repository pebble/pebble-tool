__author__ = 'katharine'

from setuptools import setup, find_packages

setup(name='libpebble2',
      version='0.0.0',
      description='Tool for interacting with pebbles.',
      url='https://github.com/pebble/pebble-tool',
      author='Pebble Technology Corporation',
      author_email='katharine@pebble.com',
      license='MIT',
      packages=find_packages(),

      install_requires=[
        'git+ssh://git@github.com/pebble/kb-libpebble2.git@e4323b5',
      ],
      zip_safe=True)