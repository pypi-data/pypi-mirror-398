# Installation

This guide covers how to install gedi2py on different platforms.

## Prerequisites

gedi2py requires:

- **Python** >= 3.10
- **C++ compiler** with C++14 support
- **Eigen3** >= 3.3 (linear algebra library)
- **CMake** >= 3.15

## pip (recommended)

The simplest way to install gedi2py:

```bash
pip install gedi2py
```

This will automatically build the C++ extension if pre-built wheels are not available for your platform.

## conda

Using conda to manage dependencies (recommended for complex environments):

```bash
# Create environment with system dependencies
conda create -n gedi2py python=3.11 cmake eigen compilers -c conda-forge
conda activate gedi2py

# Install gedi2py
pip install gedi2py
```

Or use the provided environment file:

```bash
conda env create -f environment.yml
conda activate gedi2py
pip install -e .
```

## From source

For development or to get the latest features:

```bash
# Clone the repository
git clone https://github.com/csglab/gedi2py.git
cd gedi2py

# Install in development mode
pip install -e ".[dev,test]"
```

### Building from source requirements

#### macOS

```bash
# Install Xcode command line tools (provides C++ compiler)
xcode-select --install

# Install Eigen via Homebrew
brew install eigen cmake
```

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake libeigen3-dev
```

#### Fedora/RHEL

```bash
sudo dnf install gcc-c++ cmake eigen3-devel
```

#### Windows

We recommend using Windows Subsystem for Linux (WSL2) with Ubuntu. Native Windows builds are possible but require:

1. Visual Studio 2019 or later with C++ tools
2. vcpkg or manual Eigen3 installation
3. CMake for Windows

## Verify installation

After installation, verify gedi2py is working:

```python
import gedi2py as gd
print(gd.__version__)

# Check that the C++ backend loads
from gedi2py._gedi_cpp import GEDI
print("C++ backend loaded successfully")
```

## Optional dependencies

### scanpy integration

For full scverse integration, install scanpy:

```bash
pip install scanpy
```

### Visualization

For advanced plotting features:

```bash
pip install seaborn
```

## Troubleshooting

### ImportError: Cannot load C++ extension

This usually means the C++ extension failed to build. Check that:

1. You have a C++ compiler installed
2. Eigen3 is installed and findable by CMake
3. CMake >= 3.15 is available

Try reinstalling with verbose output:

```bash
pip install gedi2py -v
```

### Permission errors

Never use `sudo pip`. Instead:

```bash
# Use --user flag
pip install --user gedi2py

# Or better, use a virtual environment
python -m venv gedi2py-env
source gedi2py-env/bin/activate  # Linux/macOS
pip install gedi2py
```

### Eigen3 not found

If CMake cannot find Eigen3, you can specify the path:

```bash
CMAKE_PREFIX_PATH=/path/to/eigen3 pip install gedi2py
```

Or on conda:

```bash
conda install eigen -c conda-forge
```

### OpenMP issues on macOS

macOS's default compiler (Apple Clang) doesn't include OpenMP. For parallel support:

```bash
# Install libomp via Homebrew
brew install libomp

# Or use GCC
brew install gcc
export CC=gcc-13
export CXX=g++-13
pip install gedi2py
```

## Development installation

For contributing to gedi2py:

```bash
git clone https://github.com/csglab/gedi2py.git
cd gedi2py

# Install with all development dependencies
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```
