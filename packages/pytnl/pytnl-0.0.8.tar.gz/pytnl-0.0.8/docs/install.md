# Installation

## Dependencies

Before we begin, there are several dependencies that [PyTNL] requires.

**Required:**

- **Python 3.12 or later**, including the _development headers_ for building
  C/C++ Python modules
- **Compiler for the C++17 standard**, e.g. [GCC] or [Clang]
- **[Git]**
- **An MPI library** such as [OpenMPI]

**Optional:**

- **[CUDA toolkit]** for building and using CUDA-enabled PyTNL
  submodules

### Installation

You can install all dependencies with one of the following commands, depending
on your Linux distro:

**Arch Linux**

```shell
pacman -S base-devel git python openmpi
```

**Ubuntu**

```shell
apt install build-essential git python3-dev libopenmpi-dev
```

Additional dependencies will be pulled in automatically either as Python
packages (e.g. [cmake]) or using the [FetchContent cmake module][FetchContent].

---

## PyPi

PyTNL can be installed [PyPi] using any
Python package manager, e.g. `pip`:

```shell
pip install pytnl
```

!!! warning

    PyTNL currently publishes only a [source distribution (sdist)][sdist]
    so this step involves building the binary modules on your own system.
    For this to work, several [dependencies](#dependencies) must be installed.

## Git

The latest development version can be installed directly from
the git repository instead of the stable release from [PyPI](#pypi).

```shell
pip install git+https://gitlab.com/tnl-project/pytnl.git
```

Alternatively, if you need to make changes to the sources, see [Development](#development).

!!! warning

    This step involves building PyTNL from source, you need to have installed all [dependencies](#dependencies)

## Other

There are other ways to install PyTNL in specific environments, including
running plain `cmake` commands or using a different Python build frontend
such as [build]. See the [.gitlab-ci.yml] file
for examples and do not hesitate to get in touch in case of questions!

## Development

This section covers the suggested setup for PyTNL developers.
First make sure to install all [dependencies](#dependencies).

Clone the [PyTNL] repository and create a Python **virtual environment** (venv) for the
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

The `[docs]` _extra_ installs optional packages for serving and building documentation website.

```shell
mkdocs serve # Hosts documentation website locally
mkdocs build # Builds the documentation and outputs static website to /public
```

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

<!--- LINKS --->

[GCC]: https://gcc.gnu.org/
[FetchContent]: https://cmake.org/cmake/help/latest/module/FetchContent.html
[Clang]: https://clang.llvm.org/
[Git]: https://git-scm.com/
[OpenMPI]: https://www.open-mpi.org/
[CUDA toolkit]: https://developer.nvidia.com/cuda-toolkit
[cmake]: https://pypi.org/project/cmake/)
[PyTNL]: https://gitlab.com/tnl-project/pytnl
[build]: https://pypi.org/project/build/
[.gitlab-ci.yml]: https://gitlab.com/tnl-project/pytnl/-/blob/main/.gitlab-ci.yml?ref_type=heads
[PyPi]: https://pypi.org/project/pytnl/
[sdist]: https://packaging.python.org/en/latest/discussions/package-formats/
