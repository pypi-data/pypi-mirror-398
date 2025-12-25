'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-12-06 08:06:49 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-12-22 10:08:40 +0100
FilePath     : setup.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

from pathlib import Path
from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Core dependencies required for the tool
REQUIRED_PACKAGES = [
    # 'numpy>=1.24.0',
    # 'pandas>=2.0.0',
    # 'uproot>=5.0.0',
    # 'awkward>=2.0.0',
    # 'matplotlib>=3.7.0',
    # 'scikit-learn>=1.3.0',
    # 'xgboost>=1.0.0',  # You use this heavily
    # 'tqdm>=4.0.0',  # You use this
    # 'rich>=10.0.0',  # You use this for logging
    # 'uncertainties>=3.0.0',  # You use this
    # 'ROOT>=6.24.0',  # For TMVA functionality
]

# Optional dependencies for development
DEV_PACKAGES = [
    # 'pytest>=7.0.0',
    # 'black>=23.0.0',
    # 'isort>=5.12.0',
    # 'mypy>=1.0.0',
    # 'flake8>=6.0.0',
]

setup(
    name='analysis-tool',
    version='1.0.0',
    author='Jie Wu',
    author_email='j.wu@cern.ch',
    description='A generic analysis tool for various data analyses. Mainly for the analysis of the LHCb experiment.',
    long_description=long_description,
    long_description_content_type='text/markdown',  # Specify the format of the long description
    url='https://github.com/JieWu-GitHub/Analysis_tools',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Intended Audience :: Science/Research",
        "Development Status :: 4 - Beta",
    ],
    keywords=['HEP', 'physics', 'lhcb', 'data-analysis', 'root', 'tmva', 'xgboost'],
    packages=find_packages(exclude=['tests*', 'docs*', 'backup*']),
    include_package_data=True,  # Include package data as specified in MANIFEST.in
    python_requires='>=3.10',
    install_requires=REQUIRED_PACKAGES,
    extras_require={
        'dev': DEV_PACKAGES,
    },
    entry_points={
        'console_scripts': [
            'analysis_tool=analysis_tool.cli:main',
        ],
    },
    license='MIT',
)
