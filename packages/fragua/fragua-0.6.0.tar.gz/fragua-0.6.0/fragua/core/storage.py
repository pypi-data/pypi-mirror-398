"""
Base storage class for all storage objects in Fragua (Wagon, Box, Container).
"""

from typing import Any, Dict, Generic, Optional, TypeVar
from fragua.core.fragua_instance import FraguaInstance
from fragua.utils.logger import get_logger
from fragua.utils.metrics import add_metadata_to_storage, generate_metadata

T = TypeVar("T")

logger = get_logger(__name__)


class Storage(FraguaInstance, Generic[T]):
    """
    Core runtime storage abstraction for all persistable objects in Fragua.
    """

    def __init__(self, storage_name: str, data: Optional[T] = None) -> None:
        super().__init__(instance_name=storage_name)
        self._data: Optional[T] = data
        self._metadata: dict[str, object] = {}

        if data is not None:
            self._generate_base_metadata()

    @property
    def data(self) -> Optional[T]:
        """Access the stored data."""
        return self._data

    def _generate_base_metadata(self) -> None:
        """
        Generate and attach base metadata to the storage.

        Base metadata typically includes information such as storage type,
        creation context, and timestamps.
        """
        metadata = generate_metadata(self, metadata_type="base")
        add_metadata_to_storage(self, metadata)

    def summary(self) -> Dict[str, Any]:
        return {
            "type": "storage",
            "name": self.name,
            "class": self.__class__.__name__,
            "has_data": self._data is not None,
            "metadata_keys": list(self._metadata.keys()),
        }


class Box(Storage[Any]):
    """
    Storage type representing a single unit of data.

    A Box typically contains the output of a style execution and is the
    most common persistable storage unit within the warehouse.
    """


class Container(Storage[Any]):
    """
    Composite storage capable of grouping multiple Box instances.

    A Container acts as a hierarchical storage structure, allowing
    multiple Boxes to be stored and managed under a single logical unit.
    """

    def __init__(self, container_name: str) -> None:
        """
        Initialize an empty Container.

        Containers do not hold direct data; instead, they manage a
        collection of named Box instances.
        """
        super().__init__(storage_name=container_name, data=None)
        self._content: Dict[str, Box] = {}

    def add_storage(self, storage_name: str, storage: Box) -> None:
        """
        Add a Box to the container.

        Args:
            storage_name: Name under which the Box will be stored.
            storage: Box instance to add.
        """
        self._content[storage_name] = storage

    def get_storage(self, name: str) -> Box:
        """
        Retrieve a Box from the container by name.

        Args:
            name: Name of the Box.

        Returns:
            The requested Box instance.
        """
        return self._content[name]

    def list_storages(self) -> dict[str, str]:
        """
        List all contained storages.

        Returns:
            A mapping of storage names to their class names.
        """
        return {name: s.__class__.__name__ for name, s in self._content.items()}

    def remove_storage(self, name: str) -> None:
        """
        Remove a Box from the container.

        Args:
            name: Name of the Box to remove.
        """
        self._content.pop(name, None)

    def clear(self) -> None:
        """
        Remove all contained Boxes from the container.
        """
        self._content.clear()

    def __repr__(self) -> str:
        """
        Return a string representation of the container and its contents.

        Returns:
            A string listing contained storage names or indicating emptiness.
        """
        items = ", ".join(self._content.keys()) or "empty"
        return f"<Container: {items}>"


STORAGE_CLASSES: dict[str, type[Storage[Any]]] = {
    "Box": Box,
    "Container": Container,
}
