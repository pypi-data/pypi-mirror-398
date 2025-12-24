# Nuplan

### pip install nuplan-devkit or u can get nuplan this page -> https://github.com/motional/nuplan-devkit

Prerequisites
Before using this package, ensure you have the correct Python version or be prepared to resolve dependency conflicts with your specific Python version.

Important: The nuPlan Development Kit officially requires Python 3.9. If you're using a different Python version, you'll need to manage dependency compatibility yourself.

For example, if your current Python version is different:

```text
Current Python version: 3.11.2 (main, Apr 28 2025, 14:11:48) [GCC 12.2.0]
Python 3.9 required, but found 3.11.2
```

## Dependencies
The nuPlan Development Kit requires the following packages:

```text
aioboto3
aiofiles
bokeh==2.4.3
boto3==1.24.59
cachetools
casadi
control==0.9.1
coverage
docker
Fiona
geopandas>=0.12.1
grpcio==1.43.0
grpcio-tools==1.43.0
guppy3==3.1.2
hydra-core==1.1.0rc1
hypothesis
joblib
jupyter
jupyterlab
matplotlib
mock
moto
nest_asyncio
numpy==1.23.4
pandas
Pillow
pre-commit
psutil
pyarrow
pyinstrument
pyogrio
pyquaternion>=0.9.5
pytest
rasterio
ray
requests
retry
rtree
s3fs
scipy
selenium
setuptools==59.5.0
Shapely>=2.0.0
SQLAlchemy==1.4.27
sympy
testbook
tornado
tqdm
typer
ujson
urllib3
```

## Usage
```text
nuplan --help
Usage: nuplan [command]

Commands:
  install_info  - Show required packages for installation
  help          - Show this help message

...

nuplan_cli --help
nuplan_cli COMMAND --help
```

## Package Structure

```text
nuplan_devkit
├── nuplan_devkit        # Git-based installer and helper utilities
├── nuplan               # Main nuPlan source folder (vendored from GitHub)
│   ├── common           # Code shared by database and planning modules
│   ├── database         # Core devkit for loading and rendering datasets and maps
│   ├── planning         # Planning framework for simulation, training, and evaluation
│   ├── submission       # Submission engine for the nuPlan planning challenge
│   └── cli              # Command-line interface tools
```


## nuplan-devkit installer

from nuplan_installer import install_and_verify_nuplan

success = install_and_verify_nuplan("nuplan_devkit")



## Support & Feedback

If you encounter any issues, have questions, or would like to suggest improvements, feel free to contact me directly:

**Email:** genry777mill777er@gmail.com

I’m always open to feedback and contributions that help improve this project.