#!/usr/bin/env python3
import os
import pathlib
import shutil
from typing import Any

import click
import toml
import tomlkit
from platformdirs import user_config_dir
from PythonSed import Sed


def deep_merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge update dict into base dict, preserving existing keys.

    Args:
        base: Base dictionary to merge into
        update: Dictionary with updates to apply

    Returns:
        Merged dictionary
    """
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def safe_copy(src: pathlib.Path, dest: pathlib.Path, force: bool = False) -> bool:
    """Copy a file only if it doesn't exist or force is True.

    Args:
        src: Source file path
        dest: Destination file path
        force: If True, overwrite existing files

    Returns:
        True if file was copied, False if skipped
    """
    if dest.exists() and not force:
        click.echo(f"Skipping {dest.name} (already exists)")
        return False
    shutil.copy(src, dest)
    click.echo(f"Installed {dest.name}")
    return True


@click.command()
@click.option("-f", "--force", is_flag=True, help="Overwrite existing files")
@click.option(
    "-C",
    "--chdir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Change to this directory before installing",
)
def install(force: bool, chdir: str | None) -> None:
    """Install pre-commit hooks."""

    pyinit_dir = pathlib.Path(__file__).resolve().parent
    if chdir:
        os.chdir(chdir)
    current_dir = pathlib.Path.cwd()

    # Copy pre-commit configuration file
    src = pyinit_dir / "data" / "pre-commit-config.yaml"
    dest = current_dir / ".pre-commit-config.yaml"
    safe_copy(src, dest, force)

    # If this is not a git repository, initialize it
    if not (current_dir / ".git").exists():
        os.system("git init")
        click.echo("Initialized a new git repository")

    # Install pre-commit hooks
    os.system("pre-commit install")

    # Enable GPG signing for commits and tags
    os.system("git config commit.gpgsign true")
    os.system("git config tag.gpgsign true")
    click.echo("Enabled GPG signing for commits and tags")

    # Read project name from pyproject.toml
    pyproject_path = current_dir / "pyproject.toml"
    if not pyproject_path.exists():
        click.echo("pyproject.toml not found in the current directory.")
        return

    with open(pyproject_path) as f:
        pyproject_data = toml.load(f)
    project_name = pyproject_data["project"]["name"]

    # Install workflow files for GitHub Actions
    workflows_src = pyinit_dir / "data" / "github" / "workflows"
    workflows_dest = current_dir / ".github" / "workflows"
    workflows_dest.mkdir(parents=True, exist_ok=True)

    for workflow_file in workflows_src.iterdir():
        dest_file = workflows_dest / workflow_file.name
        if dest_file.exists() and not force:
            click.echo(f"Skipping {dest_file.name} (already exists)")
            continue
        with open(workflow_file) as f:
            content = f.read()
        content = content.replace("{PROJECT_NAME}", project_name)
        with open(dest_file, "w") as f:
            f.write(content)
        click.echo(f"Installed {dest_file.name}")

    # Install copilot-instructions.md
    copilot_src = pyinit_dir / "data" / "github" / "copilot-instructions.md"
    copilot_dest = current_dir / ".github" / "copilot-instructions.md"
    safe_copy(copilot_src, copilot_dest, force)

    # Install yamllint configuration
    yamllint_src = pyinit_dir / "data" / "yamllint"
    yamllint_dest = current_dir / ".yamllint"
    safe_copy(yamllint_src, yamllint_dest, force)

    # Install gitlint configuration
    gitlint_src = pyinit_dir / "data" / "gitlint"
    gitlint_dest = current_dir / ".gitlint"
    safe_copy(gitlint_src, gitlint_dest, force)

    # Install or update .gitignore with required entries
    gitignore_src = pyinit_dir / "data" / "gitignore"
    gitignore_dest = current_dir / ".gitignore"

    with open(gitignore_src) as f:
        required_entries = set(line.strip() for line in f if line.strip())

    existing_entries = set()
    if gitignore_dest.exists():
        with open(gitignore_dest) as f:
            existing_entries = set(line.strip() for line in f if line.strip())

    new_entries = required_entries - existing_entries
    if new_entries:
        with open(gitignore_dest, "a") as f:
            if gitignore_dest.exists() and existing_entries:
                f.write("\n")  # Add newline before new entries
            f.write("\n".join(sorted(new_entries)) + "\n")
        click.echo(f"Updated .gitignore with {len(new_entries)} new entries")
    elif not gitignore_dest.exists():
        safe_copy(gitignore_src, gitignore_dest, force)
    else:
        click.echo("Skipping .gitignore (all entries already present)")

    # Install a minimal mkdocs.yaml if it doesn't exist
    mkdocs_dest = current_dir / "mkdocs.yaml"
    if not mkdocs_dest.exists() or force:
        mkdocs_src = pyinit_dir / "data" / "mkdocs.yml"
        with open(mkdocs_src) as f:
            mkdocs_content = f.read()
        mkdocs_content = mkdocs_content.replace("{project_name}", project_name)
        with open(mkdocs_dest, "w") as f:
            f.write(mkdocs_content)
        click.echo("Installed mkdocs.yaml")

    # Install a minimal docs/index.md if it doesn't exist
    docs_index_dest = current_dir / "docs" / "index.md"
    if not docs_index_dest.exists() or force:
        docs_index_dest.parent.mkdir(parents=True, exist_ok=True)
        index_content = (
            f"# {project_name}\n\nWelcome to the documentation for {project_name}."
        )
        with open(docs_index_dest, "w") as f:
            f.write(index_content)
        click.echo("Installed docs/index.md")
    else:
        click.echo("Skipping docs/index.md (already exists)")

    # Update pyproject.toml with data/pyproject.toml
    pyproject_update_src = pyinit_dir / "data" / "pyproject-update.toml"
    with open(pyproject_update_src) as f:
        update_data = toml.load(f)

    # Convert project name from kebab-case to snake_case for package directory
    package_name = project_name.replace("-", "_")

    # Dynamically set the version-file path based on the project name
    if "tool" not in update_data:
        update_data["tool"] = {}
    if "hatch" not in update_data["tool"]:
        update_data["tool"]["hatch"] = {}
    if "build" not in update_data["tool"]["hatch"]:
        update_data["tool"]["hatch"]["build"] = {}
    if "hooks" not in update_data["tool"]["hatch"]["build"]:
        update_data["tool"]["hatch"]["build"]["hooks"] = {}
    if "vcs" not in update_data["tool"]["hatch"]["build"]["hooks"]:
        update_data["tool"]["hatch"]["build"]["hooks"]["vcs"] = {}

    update_data["tool"]["hatch"]["build"]["hooks"]["vcs"]["version-file"] = (
        f"src/{package_name}/__about__.py"
    )

    with open(pyproject_path) as f:
        current_data = tomlkit.load(f)
    deep_merge(current_data, update_data)
    with open(pyproject_path, "w") as f:
        tomlkit.dump(current_data, f)
    click.echo("Updated pyproject.toml with additional configurations.")

    # Write an example test into the package's test directory (can be trivial)
    tests_dir = current_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    test_file = tests_dir / f"test_{package_name}_import.py"
    if not test_file.exists() or force:
        test_content = f"""import sys

import {package_name}


def test_import() -> None:
    dir({package_name})  # Ensure package can be used
    assert "{package_name}" in sys.modules
"""
        with open(test_file, "w") as f:
            f.write(test_content)
        click.echo(f"Installed example test file {test_file.name}")
    else:
        click.echo(f"Skipping example test file {test_file.name} (already exists)")

    # If there is a init.sed in the user's config directory, apply it to all files with type: .py, .toml, .md, .txt
    # Use platformdirs and pythonsed
    config_dir = pathlib.Path(user_config_dir("fledge"))
    sed_file = config_dir / "init.sed"
    click.echo(f"Looking for user sed script at {sed_file}")
    if sed_file.exists():
        click.echo(f"Applying user sed script from {sed_file}")
        for ext in [".py", ".toml", ".md", ".txt"]:
            for file_path in current_dir.rglob(f"*{ext}"):
                sed = Sed(
                    sed_compatible=False, in_place=""
                )  # Use Python regex and edit in-place without backup
                sed.load_string(sed_file.read_text())
                sed.apply(str(file_path))
        click.echo("Applied user sed script to relevant files.")
    else:
        click.echo("No user sed script found; skipping this step.")


if __name__ == "__main__":
    install()
