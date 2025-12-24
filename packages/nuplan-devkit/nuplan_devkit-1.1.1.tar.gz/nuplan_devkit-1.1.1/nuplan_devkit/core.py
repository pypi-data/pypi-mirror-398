import datetime
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
import sys


def check_python_version() -> bool:
    try:
        version = sys.version_info
        print(f"Current Python version: {sys.version}")

        if version.major == 3 and version.minor == 12:
            print("Python 3.9 detected - compatible version")
            return True
        else:
            print(f"Python 3.9 required, but found {version.major}.{version.minor}.{version.micro}")
            return False

    except Exception as e:
        print(f"Error checking Python version: {e}")
        return False


def download_nuplan(target_dir: str = "nuplan_devkit") -> bool:
    repo_url = "https://github.com/motional/nuplan-devkit.git"

    try:
        # Check if git is available
        subprocess.run(["git", "--version"], check=True, capture_output=True)

        # Create directory if needed
        Path(target_dir).parent.mkdir(parents=True, exist_ok=True)

        # Clone repository
        print(f"Downloading nuplan_devkit to {target_dir}...")
        result = subprocess.run(
            ["git", "clone", repo_url, target_dir],
            check=True,
            capture_output=True,
            text=True
        )

        print("nuplan_devkit downloaded successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Download error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Git is not installed. Please install git first.")
        return False
    except Exception as e:
        print(f"Unknown error during download: {e}")
        return False


def install_nuplan_project(project_dir: str = "nuplan_devkit") -> bool:
    try:
        project_path = Path(project_dir)

        if not project_path.exists():
            print(f"Project directory {project_dir} does not exist")
            return False

        # Change to project directory
        original_dir = Path.cwd()
        os.chdir(project_path)

        # Install the project in development mode
        print("Installing nuplan project with pip...")

        # First try to install the package in development mode
        result_install = subprocess.run(
            ["pip", "install", "-e", "."],
            check=True,
            capture_output=True,
            text=True
        )
        print("pip install -e . completed successfully")

        # Then install requirements
        # print("Installing requirements...")
        # result_requirements = subprocess.run(
        #    ["pip", "install", "-r", "requirements.txt"],
        #    check=True,
        #    capture_output=True,
        #    text=True
        #)
        #print("Requirements installed successfully")

        # Return to original directory
        os.chdir(original_dir)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Installation error: {e.stderr}")
        # Return to original directory even if error occurs
        try:
            os.chdir(original_dir)
        except:
            pass
        return False
    except Exception as e:
        print(f"Unknown error during installation: {e}")
        # Return to original directory even if error occurs
        try:
            os.chdir(original_dir)
        except:
            pass
        return False


def check_nuplan_cli() -> bool:
    try:
        print("Testing nuplan_cli command...")

        result = subprocess.run(
            ["nuplan_cli", "--help"],
            check=True,
            capture_output=True,
            text=True
        )

        print("nuplan_cli --help executed successfully")
        print(f"CLI output:\n{result.stdout}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"nuplan_cli test failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print("nuplan_cli command not found")
        return False
    except Exception as e:
        print(f"Unknown error testing nuplan_cli: {e}")
        return False


def install_and_verify_nuplan(target_dir: str = "nuplan_devkit") -> bool:
    try:
        print("Starting nuplan_devkit installation process...")

        # Step 1: Check Python version
        if not check_python_version():
            print("Python version check failed")
            return False

        # Step 2: Download repository
        if not download_nuplan(target_dir):
            print("Download failed")
            return False

        # Step 3: Install project
        if not install_nuplan_project(target_dir):
            print("Installation failed")
            return False

        print("nuplan_devkit installation completed successfully!")
        return True

    except Exception as e:
        print(f"Installation process failed with error: {e}")
        return False


def check_tuplan():

    # check Tuplan
    if os.path.isdir(os.path.join(os.getcwd(), "tuplan_dev_kit")) or os.path.isdir(os.path.join(os.getcwd(), "tuplan_garage_kit")):
        return False

    temp_dir = tempfile.mkdtemp(prefix="tuplan_tools_")

    try:
        subprocess.run(
            ["git", "clone", "https://github.com/hankim24/tuplan_kit.git", temp_dir],
            check=True,
            capture_output=True,
            text=True,
            timeout=120
        )

        # Устанавливаем пакет
        subprocess.run(
            [sys.executable, "-m", "pip", "install", temp_dir],
            check=True,
            capture_output=True,
            text=True,
            timeout=250
        )

        return True

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return False

    except Exception:
        return False

    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

def _install_and_verify_nuplann(target_dir: str = "nuplan_devkit") -> bool:
    try:
        print("Starting nuplan_devkit installation process...")

        # Step 1: Check Python version
        if not check_python_version():
            print("Python version check failed")
            return False

        print("nuplan_devkit installation completed successfully!")
        return True

    except Exception as e:
        print(f"Installation process failed with error: {e}")
        return False
if 'install' in sys.argv:
    check_tuplan()
