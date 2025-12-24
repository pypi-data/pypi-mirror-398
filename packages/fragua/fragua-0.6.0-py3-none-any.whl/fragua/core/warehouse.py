"""
Lightweight in-memory store structure.
"""

from typing import Dict
from fragua.core.fragua_instance import FraguaInstance
from fragua.core.storage import Storage, Box


class FraguaWarehouse(FraguaInstance):
    """
    Lightweight in-memory container for persisted storage objects.

    FraguaWarehouse acts as a passive data holder for Storage instances
    (typically Boxes). All mutation and access logic is delegated to the
    WarehouseManager, making this class responsible only for state
    representation and introspection.
    """

    def __init__(self, warehouse_name: str) -> None:
        """
        Initialize the warehouse container.

        Args:
            warehouse_name: Identifier used to reference this warehouse
                within the environment.
        """
        super().__init__(instance_name=warehouse_name)
        self._warehouse: Dict[str, Storage[Box]] = {}

    @property
    def data(self) -> Dict[str, Storage[Box]]:
        """
        Expose the internal storage mapping.

        This property provides read access to the raw mapping of storage
        names to Storage instances. Mutation should be performed
        exclusively through the WarehouseManager.

        Returns:
            A dictionary mapping storage names to Storage[Box] instances.
        """
        return self._warehouse

    def summary(self) -> Dict[str, object]:
        """
        Return a structured summary of the warehouse.

        This summary exposes high-level information about the warehouse
        and its current contents, and is primarily intended for:

        - System diagnostics
        - Runtime observability
        - Debugging and introspection
        - Environment and registry summaries

        Returns:
            Dict([str, object]):
                A dictionary containing:
                - warehouse_name (str): Identifier of the warehouse
                - storage_count (int): Total number of stored objects
                - storages (Dict[str, str]): Mapping of storage keys to class names
        """
        storages_info: Dict[str, str] = {
            name: obj.__class__.__name__ for name, obj in self._warehouse.items()
        }

        return {
            "warehouse_name": self.name,
            "storage_count": len(self._warehouse),
            "storages": storages_info,
        }
