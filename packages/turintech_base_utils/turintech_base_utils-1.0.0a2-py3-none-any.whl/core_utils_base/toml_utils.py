"""Utility module for working with TOML files."""

# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from os import PathLike
from pathlib import Path
from typing import Optional

import toml

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#         Defines the public interface of the module that will be imported when using 'from package import *'.         #
#    This helps control what is exposed to the global namespace, limiting imports to only those listed in __all__.     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["get_project_version"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Module Implementation                                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def get_project_version(file_path: PathLike) -> Optional[str]:
    """Fetches the project version from a TOML file.

    Args:
        file_path (PathLike): Path to the TOML file.

    Returns:
        Optional[str]: Project version if found, otherwise None.
    """
    if Path(file_path).is_file():
        with open(file_path, "r", encoding="utf-8") as f:
            pyproject_data = toml.load(f)
            version = pyproject_data.get("project", {}).get("version") or pyproject_data.get("tool", {}).get(
                "poetry", {}
            ).get("version")
            return version
    return None
