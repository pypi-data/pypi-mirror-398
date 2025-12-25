# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from hashlib import md5
from typing import Any, List

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["compose_hash_id"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                     Util methods                                                     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def compose_hash_id(values: List[Any]) -> str:
    """
    Compose a hash ID for the given values.
    """
    _id = "-".join([str(value) for value in values])
    return md5(_id.encode("utf-8")).hexdigest()
