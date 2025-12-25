#!/usr/bin/env python
import os

from datetime import date

from setuptools import setup, find_packages

from whatap import build
build.release_date = date.today().strftime('%Y%m%d')

readme_file = os.path.join(os.getcwd(), 'whatap', 'README.rst')

setup(name=build.name,
      version=build.version,
      description='Monitoring and Profiling Service',
      long_description=open(readme_file).read(),
      author='whatap',
      author_email='admin@whatap.io',
      license='Whatap License',
      url='https://www.whatap.io',
      packages=find_packages(exclude=('sample','sample.*')),
      package_data={
          'whatap': ['LICENSE', '*.rst', '*.conf', '*.json', 'agent/*/*/whatap_python', 'agent/windows/*.exe']
      },
      entry_points={
          'console_scripts': [
              'whatap-start-agent=whatap.scripts:start_agent',
              'whatap-stop-agent=whatap.scripts:stop_agent',
              'whatap-setting-config=whatap.scripts:setting_config',


              'whatap-start-batch-agent=whatap:start_batch_agent',
          ],
      },
      install_requires=[
          'psutil>=5.0.0; platform_system=="Windows"',  # Required for Windows compatibility (memory/process monitoring)
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Operating System :: POSIX :: Linux',
          'Operating System :: MacOS',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Programming Language :: Python :: 3.12',
          'Programming Language :: Python :: 3.13',
      ],
      zip_safe=False,
      python_requires='>=3.7',
      )

