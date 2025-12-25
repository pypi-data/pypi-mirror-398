"""Module for Python utility functions."""

# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from importlib.metadata import PackageNotFoundError, version
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#         Defines the public interface of the module that will be imported when using 'from package import *'.         #
#    This helps control what is exposed to the global namespace, limiting imports to only those listed in __all__.     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["get_lib_version", "get_optional_lib_version"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Module Implementation                                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def get_lib_version(lib_name: str) -> str:
    """Retrieve the current version of the specified package.

    Args:
        lib_name (str): The name of the package whose version is to be retrieved.

    Returns:
        str: The version of the specified package.

    Raises:
        importlib.metadata.PackageNotFoundError: If the specified package is not found.
    """
    return version(lib_name)


def get_optional_lib_version(lib_name: str) -> Optional[str]:
    """Retrieve the current version of the specified package.

    Args:
        lib_name (str): The name of the package whose version is to be retrieved.

    Returns:
        Optional[str]: The version of the specified package.
    """
    try:
        return version(lib_name)
    except PackageNotFoundError:
        return None
