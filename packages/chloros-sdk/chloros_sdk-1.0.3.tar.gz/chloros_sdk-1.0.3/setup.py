"""
Chloros SDK - Setup Configuration
==================================

Official Python SDK for MAPIR Chloros image processing software.

Copyright (c) 2025 MAPIR Inc. All rights reserved.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read version from __version__.py
version_dict = {}
with open('chloros_sdk/__version__.py') as f:
    exec(f.read(), version_dict)

# Read long description from README
this_directory = Path(__file__).parent
long_description = (this_directory / "SDK_README.md").read_text(encoding='utf-8')

setup(
    name='chloros-sdk',
    version=version_dict['__version__'],
    description='Official Python SDK for MAPIR Chloros image processing',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='MAPIR Inc.',
    author_email='info@mapir.camera',
    url='https://www.mapir.camera',
    project_urls={
        'Documentation': 'https://docs.chloros.com',
        'Source': 'https://github.com/mapircamera/chloros-sdk',
        'Tracker': 'https://github.com/mapircamera/chloros-sdk/issues',
        'Support': 'https://www.mapir.camera/community/contact',
    },
    packages=find_packages(exclude=['tests', 'examples']),
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Image Processing',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: Microsoft :: Windows :: Windows 11',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='chloros mapir multispectral ndvi image-processing agriculture remote-sensing',
    license='Proprietary',
    platforms=['Windows'],
    include_package_data=True,
    zip_safe=False,
)














