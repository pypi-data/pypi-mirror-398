#!/usr/bin/env python3
"""
CLI for NuPlan Development Kit - shows required packages
"""

import sys
from .core import check_python_version


def show_required_packages():
    """
    Display all required packages for installation
    """
    packages = [
        "aioboto3",
        "aiofiles",
        "bokeh==2.4.3",
        "boto3==1.24.59",
        "cachetools",
        "casadi",
        "control==0.9.1",
        "coverage",
        "docker",
        "Fiona",
        "geopandas>=0.12.1",
        "grpcio==1.43.0",
        "grpcio-tools==1.43.0",
        "guppy3==3.1.2",
        "hydra-core==1.1.0rc1",
        "hypothesis",
        "joblib",
        "jupyter",
        "jupyterlab",
        "matplotlib",
        "mock",
        "moto",
        "nest_asyncio",
        "numpy==1.23.4",
        "pandas",
        "Pillow",
        "pre-commit",
        "psutil",
        "pyarrow",
        "pyinstrument",
        "pyogrio",
        "pyquaternion>=0.9.5",
        "pytest",
        "rasterio",
        "ray",
        "requests",
        "retry",
        "rtree",
        "s3fs",
        "scipy",
        "selenium",
        "setuptools==59.5.0",
        "Shapely>=2.0.0",
        "SQLAlchemy==1.4.27",
        "sympy",
        "testbook",
        "tornado",
        "tqdm",
        "typer",
        "ujson",
        "urllib3",
    ]

    print("Required packages for NuPlan Development Kit:")
    print("=" * 50)

    for package in packages:
        print(f"• {package}")

    print("\nInstall this packages:")
    print("pip install " + " ".join(packages))

    print(" -> Check https://github.com/motional/nuplan-devkit/blob/master/requirements.txt")
    # python --version
    check_python_version()
    return 0


def main():
    """
    Main entry point - handles command line arguments
    """
    # Check if any argument is provided
    if len(sys.argv) > 1:
        # Check for install_info command
        if sys.argv[1] in ["install_info", "--install_info", "--install-info"]:
            return show_required_packages()
        # Check for help
        elif sys.argv[1] in ["--help", "-h", "help"]:
            print("Usage: nuplan [command]")
            print("\nCommands:")
            print("  install_info  - Show required packages for installation")
            print("  help          - Show this help message")
            return 0
        else:
            print(f"Error: Unknown command '{sys.argv[1]}'")
            print("Use 'nuplan help' for available commands")
            return 1

    # No arguments - default to showing required packages
    return show_required_packages()


if __name__ == "__main__":
    sys.exit(main())
