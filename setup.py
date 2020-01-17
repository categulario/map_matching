#!/usr/bin/env python3
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()

with open(path.join(here, 'mapmatching', 'version.txt')) as f:
    version = f.read().strip()

setup(
    name='mapmatching',
    description='A map matching library',
    long_description=long_description,
    url='https://github.com/categulairo/map_matching',

    version=version,

    author='Abraham Toriz Cruz',
    author_email='categulario@gmail.com',
    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',

        'Environment :: Console',

        'Intended Audience :: Developers',
        'Intended Audience :: Education',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',

        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    keywords='mapmatching algorithm gps',

    packages=find_packages(exclude=[
        "*.tests", "*.tests.*", "tests.*", "tests",
    ]),

    package_data={
        'mapmatching': ['lua/scripts/*.lua', 'overpass/*.overpassql', 'version.txt'],
    },

    entry_points={
        'console_scripts': [
            'mapmatching = mapmatching.main:main',
        ],
    },

    install_requires=[
        'redis',
        'requests',
    ],

    setup_requires=[
        'pytest-runner',
    ],

    tests_require=[
        'pytest',
        'pytest-mock',
    ],
)
