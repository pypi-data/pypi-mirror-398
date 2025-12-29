#!/usr/bin/env -S just --working-directory . --justfile

# Installs the project using pip. Since this is the first recipe it is run by default.
install:
    just ensure-command pip
    pip install --no-build-isolation -ve .[dev,dev-cuda]

# Runs all checks
check: check-format check-code check-typing check-typos check-recipes

# Builds an sdist tarball of the project using python-build
build-sdist:
    just ensure-command pyproject-build python
    python -m build --sdist --no-isolation

# Builds a wheel of the project using python-build
build-wheel:
    just ensure-command pyproject-build python
    python -m build --wheel --no-isolation

# Builds a wheel and an sdist tarball of the project using python-build
build: build-sdist build-wheel

# Cleans the build directory
clean:
    rm -frv dist build

# Checks the code using ruff
check-code:
    just ensure-command ruff
    ruff check

# Checks the code formatting using ruff
check-format:
    just ensure-command ruff
    ruff format --diff

# Checks for typing issues using mypy
check-typing:
    just ensure-command basedpyright
    basedpyright
    just ensure-command mypy
    mypy

# Checks for common spelling mistakes using typos
check-typos:
    just ensure-command typos
    typos

# Checks justfile recipe for shell issues using shellcheck
check-recipe recipe:
    just ensure-command grep shellcheck
    just -vv -n {{ recipe }} 2>&1 | grep -v '===> Running recipe' | shellcheck -

# Checks all justfile recipes with inline bash for shell issues using shellcheck
check-recipes:
    just check-recipe 'ensure-command command'
    just check-recipe 'create-pypi-release'
    just check-recipe 'release'

# Runs all tests
test:
    just ensure-command pytest
    pytest -vv

# Ensures that one or more required commands are installed
ensure-command +command:
    #!/usr/bin/env bash
    set -euo pipefail

    read -r -a commands <<< "{{ command }}"

    for cmd in "${commands[@]}"; do
        if ! command -v "$cmd" > /dev/null 2>&1 ; then
            printf "Couldn't find required executable '%s'\n" "$cmd" >&2
            exit 1
        fi
    done

# Gets the project name from the pyproject.toml
get-project-name:
    just ensure-command yq
    yq -r '.project.name' pyproject.toml

# Gets the current version of the project from the pyproject.toml
get-current-version:
    just ensure-command yq
    yq -r '.project.version' pyproject.toml

# Builds a sdist tarball of the project and uploads it to PyPI using twine
create-pypi-release:
    #!/usr/bin/env bash
    set -euo pipefail

    project="$(just get-project-name)"
    readonly project="$project"
    if [[ -z "$project" ]]; then
        printf "No project name found!\n" >&2
        exit 1
    fi
    current_version="$(just get-current-version)"
    readonly current_version="$current_version"
    if [[ -z "$current_version" ]]; then
        printf "No current version found!\n" >&2
        exit 1
    fi

    just ensure-command git twine # gpg glab

    if ! git tag --points-at | grep "$current_version" >/dev/null; then
        printf "Current project version is %s, but HEAD is not the tag %s!\n" "$current_version" "$current_version" >&2
        exit 1
    fi

    rm -fv dist/*
    just build-sdist

    #printf "Creating signature for sdist tarball...\n"
    #gpg -o "dist/$project-$current_version.tar.gz.sig" --default-key "$(git config --local --get user.signingkey)" -s "dist/$project-$current_version.tar.gz"
    #printf "Attach sdist tarball and signature to GitLab release %s...\n" "$current_version"
    #GITLAB_HOST=gitlab.archlinux.org glab release create "$current_version" "./dist/$project-$current_version.tar.gz"* --name="$current_version" --notes="$current_version"

    printf "Pushing the sdist tarball to PyPI...\n"
    twine upload "./dist/$project-$current_version.tar.gz"

# Creates a tag and pushes it (if it does exist yet) and creates a release for it
release:
    #!/usr/bin/env bash
    set -euo pipefail

    current_version="$(just get-current-version)"
    readonly current_version="$current_version"
    if [[ -z "$current_version" ]]; then
        printf "No current version found!\n" >&2
        exit 1
    fi

    if [[ -n "$(git tag -l "$current_version")" ]]; then
        printf "The tag %s exists already!\n" "$current_version" >&2
        exit 1
    fi

    just ensure-command git

    git push origin
    printf "Creating tag %s...\n" "$current_version"
    git tag -a "$current_version" -m "version $current_version"
    printf "Pushing tag %s...\n" "$current_version"
    git push origin refs/tags/"$current_version"

    just create-pypi-release
