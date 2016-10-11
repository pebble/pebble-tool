__author__ = 'katharine'

import sys
from setuptools import setup, find_packages

requires = [
    'libpebble2==0.0.26',
    'httplib2==0.9.1',
    'oauth2client==1.4.12',
    'progressbar2==2.7.3',
    'pyasn1==0.1.8',
    'pyasn1-modules==0.0.6',
    'pypng==0.0.17',
    'pyqrcode==1.1',
    'requests==2.7.0',
    'rsa==3.1.4',
    'pyserial==2.7',
    'six==1.9.0',
    'websocket-client==0.32.0',
    'wheel==0.24.0',
    'colorama==0.3.3',
    'packaging==16.7',
]

if sys.version_info < (3, 4, 0):
    requires.append('enum34==1.0.4')

__version__ = None  # Overwritten by executing version.py.
with open('pebble_tool/version.py') as f:
    exec(f.read())

setup(name='pebble-tool',
      version=__version__,
      description='Tool for interacting with pebbles.',
      url='https://github.com/pebble/pebble-tool',
      author='Pebble Technology Corporation',
      author_email='katharine@pebble.com',
      license='MIT',
      packages=find_packages(),
      package_data={
          'pebble_tool.commands.sdk': ['python'],
          'pebble_tool.sdk': ['templates/*'],
          'pebble_tool.util': ['static/**/*', 'static/*.*'],
      },
      install_requires=requires,
      entry_points={
          'console_scripts': ['pebble=pebble_tool:run_tool'],
      },
      zip_safe=False)
