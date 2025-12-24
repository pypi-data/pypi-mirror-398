# fledge-cli

[![PyPI - Version](https://img.shields.io/pypi/v/fledge-cli.svg)](https://pypi.org/project/fledge-cli)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/fledge-cli.svg)](https://pypi.org/project/fledge-cli)

-----

**fledge-cli** is a command-line tool that bootstraps Python projects with best-practice development configurations and tools. It automatically sets up pre-commit hooks, linting configurations, GitHub Actions workflows, and documentation scaffolding to help you get started quickly with a well-configured Python project.

## What It Does

Running `fledge` in your Python project directory will install and configure:

- **Pre-commit hooks** - Automatically installed with `.pre-commit-config.yaml`
- **Git commit/tag signing** - Enables GPG signing via git config
- **Linting & formatting configs** - `.yamllint`, `.gitlint` for code quality
- **GitHub Actions workflows** - CI/CD pipelines for publishing docs and releases
- **MkDocs documentation** - Basic `mkdocs.yaml` and `docs/index.md` structure
- **GitHub Copilot instructions** - Project-specific AI assistant guidance
- **Enhanced .gitignore** - Common Python ignore patterns
- **Updated pyproject.toml** - Additional Hatch build configurations
- **Example test file** - Basic import test to get you started
- **Custom sed transformations** - Optional user-defined file transformations via `~/.config/fledge/init.sed` (using Python regex)

All file names are automatically customized with your project name from `pyproject.toml`.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Options](#options)
- [License](#license)

## Prerequisites

Before using fledge-cli, ensure your project meets these requirements:

1. **Hatch project structure** - Your project should be initialized with `hatch new <project-name>`
2. **PyPI Trusted Publisher** - For the release workflow to work, configure a [trusted publisher](https://docs.pypi.org/trusted-publishers/) on PyPI for your repository
3. **GitHub Pages** - Enable GitHub Pages in your repository settings and set the source to "GitHub Actions" for automated documentation deployment

## Installation

```console
pip install fledge-cli
```

## Usage

Navigate to your Python project directory and run:

```console
fledge
```

This will install all configuration files and set up your development environment. By default, existing files are not overwritten.

## Options

- `-f, --force` - Overwrite existing files
- `-C, --chdir <directory>` - Change to specified directory before installing

Example:
```console
# Install in current directory, overwriting existing configs
fledge --force

# Install in a different directory
fledge --chdir /path/to/project
```

## Custom Sed Transformations

You can define custom file transformations by creating a sed script at `~/.config/fledge/init.sed`. This script will be applied to all `.py`, `.toml`, `.md`, and `.txt` files in your project using Python regex syntax (not traditional sed syntax).

Example `~/.config/fledge/init.sed`:

```
s/YOUR_NAME/John Doe/g
s/YOUR_EMAIL/john@example.com/g
```

## License

`fledge-cli` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
