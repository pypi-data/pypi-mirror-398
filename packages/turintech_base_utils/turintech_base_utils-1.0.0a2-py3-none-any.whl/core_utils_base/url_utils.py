# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import re
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["no_http", "no_leading_slash", "no_trailing_slash", "leading_slash", "no_leading_or_trailing_slash"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                      URL Utils                                                       #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def no_http(value: str) -> str:
    """We want a 'http://' string if value is not the empty string."""
    return re.sub(r"https?://", "", value) if value else value


def no_leading_slash(value: str) -> str:
    """
    We want to remove any leading slash if value is not the empty string.
    """
    return value[1:] if value and value.startswith("/") else value


def no_trailing_slash(value: str) -> str:
    """
    We want to remove any trailing slash if value is not the empty string.
    """
    return value[:-1] if value and value.endswith("/") else value


def leading_slash(value: str) -> str:
    """
    We want a leading slash if value is not the empty string.
    """
    return value if (not value) or value.startswith("/") else f"/{value}"


def no_leading_or_trailing_slash(value: Optional[str]) -> Optional[str]:
    """
    We want to remove any leading or trailing slash if value is not the empty string.
    """
    return no_trailing_slash(value=no_leading_slash(value=value)) if value else value
