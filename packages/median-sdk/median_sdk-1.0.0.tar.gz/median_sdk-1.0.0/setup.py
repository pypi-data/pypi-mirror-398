"""
Setup script for median-sdk package.

This package provides Python bindings for the Median blockchain.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read version from __init__.py
def get_version():
    """Extract version from median_sdk.py"""
    with open('median_sdk.py', 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return '1.0.0'

setup(
    name='median-sdk',
    version=get_version(),
    author='Median Team',
    author_email='contact@median.network',
    description='Python SDK for the Median blockchain',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/your-org/median',
    project_urls={
        'Bug Reports': 'https://github.com/your-org/median/issues',
        'Source': 'https://github.com/your-org/median',
        'Documentation': 'https://github.com/your-org/median/blob/main/sdk/python/README.md',
    },
    py_modules=['median_sdk'],
    classifiers=[
        # Development status
        'Development Status :: 4 - Beta',

        # Intended audience
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',

        # Topic
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Office/Business :: Financial',
        'Topic :: System :: Distributed Computing',

        # License
        'License :: OSI Approved :: Apache Software License',

        # Python versions
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',

        # Operating systems
        'Operating System :: OS Independent',
    ],
    keywords='blockchain cosmos sdk median cryptocurrency crypto web3',
    python_requires='>=3.7',
    install_requires=[
        'requests>=2.25.0',
    ],
    extras_require={
        'dev': [
            'twine>=4.0.0',
            'wheel>=0.37.0',
            'build>=0.10.0',
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'mypy>=0.950',
        ],
        'test': [
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
            'pytest-mock>=3.6.0',
            'responses>=0.20.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'median-sdk=median_sdk:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
