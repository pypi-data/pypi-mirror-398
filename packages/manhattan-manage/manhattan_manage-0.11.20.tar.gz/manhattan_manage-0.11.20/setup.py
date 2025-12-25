"""
Setup instuctions for the package.
"""

import os

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Build a list of template files to include in the install
def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename))
    return paths

templates = package_files('manhattan_manage/manhattan/manage/templates')


setup(
    name='manhattan_manage',
    namespace_packages=['manhattan'],

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.11.20',
    description='Classes and views for managing documents in a manhattan '
                'project.',
    long_description=long_description,
    long_description_content_type='text/markdown',

    # The project's main homepage (@@ add github url once public)
    url='https://git.getme.co.uk/manhattan/manhattan_manage',

    # Author details
    author='Anthony Blackshaw',
    author_email='ant@getme.co.uk',

    # Maintainer
    maintainer="The Getme development team",
    maintainer_email="devs@getme.co.uk",

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Operating systems
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.7'
    ],

    # What does your project relate to?
    keywords='flask manhattan',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages('manhattan_manage'),
    package_dir={'': 'manhattan_manage'},

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'Flask>=1.1.1',
        'inflection>=0.3.1',
        'manhattan_chains>=0.0.15',
        'manhattan_formatters>=0.1.6',
        'manhattan_mail>=0.0.13',
        'manhattan_nav>=0.0.18',
        'manhattan_publishing>=0.2.2',
        'manhattan_secure>=0.2.0',
        'mongoframes>=1.3.6',
        'pytz>=2019.3'
    ],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'develop': ['pytest', 'pytest-flask', 'tox'],
        'test': ['pytest', 'pytest-flask', 'tox']
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    include_package_data=True,
    package_data={'templates': templates},

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={}
)
