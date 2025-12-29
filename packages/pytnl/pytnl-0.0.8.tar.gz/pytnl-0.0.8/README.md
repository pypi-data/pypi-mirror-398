# PyTNL

Python bindings for the [Template Numerical Library (TNL)][tnl-project].

## Installation

### From PyPI

PyTNL can be installed [from PyPI](https://pypi.org/project/pytnl/) using any
Python package manager, e.g. `pip`:

```shell
pip install pytnl
```

However, PyTNL currently publishes only a [source distribution (sdist)][sdist]
so this step involves building the binary modules on your own system.
For this to work, several dependencies must be installed:

- __Python 3.12 or later__, including the _development headers_ for building
  C/C++ Python modules
- __Compiler for the C++17 standard__, e.g. [GCC][gcc] or [Clang][clang]
- __[Git][git]__
- __An MPI library__ such as [OpenMPI][openmpi]
- _(Optional):_ [CUDA toolkit][CUDA] for building and using CUDA-enabled PyTNL
  submodules

You can install all dependencies with one of the following commands, depending
on your Linux distribution:

- Arch Linux:

  ```shell
  pacman -S base-devel git python openmpi
  ```

- Ubuntu:

  ```shell
  apt install build-essential git python3-dev libopenmpi-dev
  ```

Additional dependencies will be pulled in automatically either as Python
packages (e.g. [cmake][cmake-pkg]) or using the [FetchContent cmake module][
cmake-fetchcontent].

### From git repository

Alternatively, the latest development version can be installed directly from
the git repository instead of the stable release from PyPI:

```shell
pip install git+https://gitlab.com/tnl-project/pytnl.git
```

This step involves building PyTNL from source as well, see the previous section
for the necessary dependencies.

Alternatively, if you need to make changes to the sources, see the next
section.

### For development

This section covers the suggested setup for PyTNL developers.
First make sure to install all dependencies mentioned in the first section.

Clone the repository and create a Python [virtual environment][venv] for the
project:

```shell
git clone https://gitlab.com/tnl-project/pytnl.git
cd pytnl
python -m venv .venv
source .venv/bin/activate
```

Next we need to install the build system in this environment:

```shell
pip install scikit-build-core
pip install cmake ninja  # only necessary if not present in your system
```

To facilitate repeatable builds, the following command installs PyTNL without
build isolation using the active venv and shared `build` subdirectory for build
artifacts:

```shell
pip install --no-build-isolation -ve .[dev]
```

Run the previous command again after making changes in the code to rebuild the
project.

The `[dev]` _extra_ also installs packages for testing and linting the code
that you can run:

```shell
pytest
ruff check
basedpyright
mypy
```

The `[dev-cuda]` _extra_ additionally contains dependencies necessary for
testing the CUDA support.

### Other

There are other ways to install PyTNL in specific environments, including
running plain `cmake` commands or using a different Python build frontend
such as [build][python-build]. See the [.gitlab-ci.yml](.gitlab-ci.yml) file
for examples and do not hesitate to get in touch in case of questions!

## Usage

After installing PyTNL, run `python` and import some module from the `pytnl`
package, e.g. `pytnl.containers`.

The [examples directory](./examples/) contains some short examples showing how
to use PyTNL.

Note that if you install [pyright][pyright] and integrate its LSP server
(`pyright-langserver`) into your editor, you will get _code completion_
for objects in the `pytnl` package 🤩
There is also an extension [for VSCode][pyright-vscode] and
[for VSCodium][pyright-vscodium].

[tnl-project]: https://tnl-project.gitlab.io/
[sdist]: https://packaging.python.org/en/latest/discussions/package-formats/
[gcc]: https://gcc.gnu.org/
[clang]: https://clang.llvm.org/
[git]: https://git-scm.com/
[openmpi]: https://www.open-mpi.org/
[CUDA]: https://docs.nvidia.com/cuda/index.html
[cmake-pkg]: https://pypi.org/project/cmake/
[cmake-fetchcontent]: https://cmake.org/cmake/help/latest/module/FetchContent.html
[venv]: https://docs.python.org/3/library/venv.html
[python-build]: https://pypi.org/project/build/
[pyright]: https://pypi.org/project/pyright/
[pyright-vscode]: https://marketplace.visualstudio.com/items?itemName=ms-pyright.pyright
[pyright-vscodium]: https://www.open-vsx.org/extension/ms-pyright/pyright
