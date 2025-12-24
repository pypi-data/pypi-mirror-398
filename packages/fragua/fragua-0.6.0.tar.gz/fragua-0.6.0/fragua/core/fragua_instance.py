"""Runtime component base."""

from abc import ABC, abstractmethod
from typing import Any, Dict

# pylint: disable=too-few-public-methods


class FraguaInstance(ABC):
    """
    Base class for all runtime instances in Fragua.

    FraguaInstance represents stateful objects created during
    environment execution (agents, managers, warehouses, etc.).
    """

    def __init__(self, instance_name: str) -> None:
        self.name = instance_name

    @abstractmethod
    def summary(self) -> Dict[str, Any]:
        """
        Return a structured summary describing the runtime state
        of the instance.
        """
