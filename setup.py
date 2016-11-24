from setuptools import setup

setup(name='android-build-system',
      version='1.0.0',
      description='A script for running and extending android builds',
      url='http://github.com/8w9aG/android-build-system',
      author='Will Sackfield',
      author_email='will.sackfield@gmail.com',
      license='Apache',
      packages=['androidbuildsystem'],
      zip_safe=False,
      entry_points={
          'console_scripts': [
             'androidbuildsystem = androidbuildsystem:_main'
              ]
      })
