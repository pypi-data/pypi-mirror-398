#!/usr/bin/env python3
"""Version management script for regscale-cli."""

import re
import sys
from pathlib import Path
from rich.console import Console

console = Console()


def update_version_in_pyproject_toml(version: str) -> None:
    """
    Update the version in pyproject.toml.

    :param str version: The version to update to
    """
    pyproject_file = "pyproject.toml"

    pyproject_path = Path(pyproject_file)
    content = pyproject_path.read_text()

    # Update the version
    pattern = r'version\s*=\s*["\']([^"\']+)["\']'
    replacement = f'version = "{version}"'

    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        pyproject_path.write_text(content)
        console.print(f"[green]Updated version to {version} in {pyproject_file}")
    else:
        console.print(f"[red]Could not find version in {pyproject_file}")


def update_fallback_version_in_version_py(version: str) -> None:
    """
    Update the fallback version in regscale/_version.py.

    :param str version: The version to update to
    """
    version_py_path = Path("regscale/_version.py")
    content = version_py_path.read_text()
    pattern = r'return\s*["\'](\d+\.\d+\.\d+\.\d+)["\']\s*# fallback version'
    replacement = f'return "{version}"  # fallback version'
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        version_py_path.write_text(content)
        console.print(f"[green]Updated fallback version to {version} in regscale/_version.py")
    else:
        console.print("[red]Could not find fallback version in regscale/_version.py")


def get_current_version() -> str:
    """
    Get the current version from the package.

    :return: The current version
    :rtype: str
    """
    try:
        # Add the project root to Python path to ensure we can import regscale
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from regscale import __version__

        return __version__
    except ImportError as e:
        console.print(f"[red]Could not import version from regscale package: {e}")
        console.print("[yellow]Make sure you're running this script from the project root directory")
        sys.exit(1)
