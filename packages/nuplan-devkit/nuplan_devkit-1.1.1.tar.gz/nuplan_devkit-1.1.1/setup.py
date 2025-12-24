from setuptools import setup, find_packages
from nuplan_devkit.core import *

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except Exception:
    long_description = "nuPlan devkit"

# Setup configuration
setup(
    name="nuplan_devkit",
    version="1.1.1",
    author="Genry Miller",
    author_email="genry777mill777er@tutamail.com",
    description="nuPlan devkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'nuplan=nuplan_devkit.cli:main',
            'nuplan_cli = nuplan.cli.nuplan_cli:main',
        ],
    },
    keywords=[
        "python",
        "console",
        "installer",
    ],
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
)
