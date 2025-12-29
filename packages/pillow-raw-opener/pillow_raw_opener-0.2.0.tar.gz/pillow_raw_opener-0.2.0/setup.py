#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup
import os
try:
    # pip >=20
    from pip._internal.network.session import PipSession
    from pip._internal.req import parse_requirements
except ImportError:
    try:
        # 10.0.0 <= pip <= 19.3.1
        from pip._internal.download import PipSession
        from pip._internal.req import parse_requirements
    except ImportError:
        # pip <= 9.0.3
        from pip.download import PipSession
        from pip.req import parse_requirements

__version__ = '0.2.0'

github_url = 'https://github.com/chitkiu'
github_name = 'raw-pillow-opener'
package_name = 'pillow-raw-opener'
package_path = os.path.abspath(os.path.dirname(__file__))
long_description_file_path = os.path.join(package_path, 'README.md')
long_description = ''
try:
    install_requirements = [str(ir.req) for ir in parse_requirements('requirements.txt', session=PipSession())]
except AttributeError:
    install_requirements = [str(ir.requirement) for ir in parse_requirements('requirements.txt', session=PipSession())]
try:
    with open(long_description_file_path) as f:
        long_description = f.read()
except IOError:
    pass

setup(
    name=package_name,
    packages=find_packages(exclude=['docs', 'tests*']),
    include_package_data=True,
    version=__version__,
    description='raw-pillow-opener is a simple raw image opener for Pillow base on rawpy.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Samuel Duann',
    author_email='adamgic@gmail.com',
    url='%s/%s' % (github_url, github_name, ),
    download_url='%s/%s/archive/v%s.tar.gz' % (github_url, github_name, __version__, ),
    keywords=['nef', 'raw', 'Pillow'],
    install_requires=install_requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Software Development :: Libraries',        
    ],
    license='MIT',
    test_suite='tests'
)
