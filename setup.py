"""
Package information and dependencies
"""
import os
import sys

from setuptools import setup, find_packages
from distutils.sysconfig import get_python_lib

if "install" in sys.argv:
    lib_paths = [get_python_lib()]
    if lib_paths[0].startswith("/usr/lib/"):
        # We have to try also with an explicit prefix of /usr/local in order to
        # catch Debian's custom user site-packages directory.
        lib_paths.append(get_python_lib(prefix="/usr/local"))
    for lib_path in lib_paths:
        existing_path = os.path.abspath(os.path.join(lib_path, "xsiftx"))

EXCLUDE_FROM_PACKAGES = []

version = __import__('xsiftx').VERSION

setup(
    name='xsiftx',
    version=version,
    url='http://github.com/mitocw/xsiftx',
    author='MITx',
    author_email='mitx-devops@mit.edu',
    description=('Program for running data collection scripts against courses '
                 'and putting the results in the instructor dashboard of the '
                 'local edx-platform instance'),
    license='GNU General Public License v3 (GPLv3)',
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    include_package_data=True,
    entry_points={'console_scripts': [
        'xsiftx = xsiftx.command_line:execute',
    ]},
    zip_safe=False,
    install_requires=[
        'boto >= 2.13.3',
        'flask',
        'oauth',
        'celery',
        'PyYAML',
        ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)
