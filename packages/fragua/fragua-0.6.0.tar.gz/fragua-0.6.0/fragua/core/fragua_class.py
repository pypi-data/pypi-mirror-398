"""Declarative component base."""

from abc import ABC
from typing import Any, Dict

# pylint: disable=too-few-public-methods


class FraguaClass(ABC):
    """
    Base class for declarative Fragua components.

    These components are never instantiated. All metadata lives at
    class level.
    """

    @classmethod
    def summary(cls) -> Dict[str, Any]:
        """
        Default class summary.
        """
        return {
            "name": cls.__name__,
            "type": cls.__name__,
        }
