# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from enum import Enum
from typing import Any, Callable, List, Optional

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["GenericEnum"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                  Generic Enum Class                                                  #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class GenericEnum(Enum):
    """
    Generic class for enums.
    """

    @classmethod
    def keys(cls, fcn_condition: Optional[Callable] = None) -> List[str]:
        """
        Returns the keys of the enum.
        """
        return [entry.name for entry in cls if not fcn_condition or fcn_condition(entry)]

    @classmethod
    def values(cls, fcn_condition: Optional[Callable] = None) -> List[Any]:
        """
        Returns the values of the enum.
        """
        return [entry.value for entry in cls if not fcn_condition or fcn_condition(entry)]

    @classmethod
    def check_conditions(cls, **check_args) -> bool:  # pylint: disable=unused-argument
        return True
