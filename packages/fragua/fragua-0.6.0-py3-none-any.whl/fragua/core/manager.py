"""
FraguaManager class in Fragua.
Handles all logic for adding, getting, removing, and listing storages.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    TypeAlias,
    Union,
    Optional,
    Mapping,
    Dict,
    List,
    Literal,
)
from datetime import datetime
import copy as py_copy


from fragua.core.fragua_instance import FraguaInstance
from fragua.core.storage import Storage, Box, STORAGE_CLASSES
from fragua.utils.logger import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from fragua.core.environment import FraguaEnvironment


StorageType = Literal["box", "all"]

StorageResult: TypeAlias = Union[
    Optional[Storage[Box]],
    Mapping[str, Storage[Box]],
]


class FraguaManager(FraguaInstance):
    """
    Central coordinator for managing Storage objects within a FraguaWarehouse.

    The FraguaManager encapsulates all operational logic for Box-based storages,
    providing a controlled API to add, retrieve, delete, rename, copy, and
    batch-process storage objects.
    """

    def __init__(
        self,
        manager_name: str,
        environment: FraguaEnvironment,
    ) -> None:
        """
        Initialize the manager and bind it to a Warehouse.

        Args:
            manager_name: Logical name of the manager instance.
            warehouse: Warehouse instance to operate on.
        """
        super().__init__(instance_name=manager_name)
        self.environment = environment
        self.warehouse = self.environment.warehouse
        self._movement_log: List[dict[str, object]] = []
        self._undo_stack: List[dict[str, Any]] = []

    # ----------------------------- Summary ----------------------------- #
    def summary(self) -> Dict[str, Any]:
        """
        This method provides a structured snapshot of the manager,
        exposing both configuration and runtime information, including:

        - Manager identity
        - Associated warehouse metadata
        - Current storage inventory and their concrete types
        - Full movement history registered by the manager
        - Operational counters for traceability and debugging

        Returns:
            Dict([str, Any]):
                A hierarchical dictionary containing:
                - manager_name (str): Manager identifier
                - warehouse_name (str | None): Linked warehouse name
                - storage_count (int): Total number of stored objects
                - storages (Dict[str, str]): Mapping of storage names to class types
                - movement_log (List[Any]): Complete movement history
                - log_entries (int): Total number of logged movements
                - undo_stack_size (int): Current undo stack depth
        """

        storages_info = {
            name: obj.__class__.__name__ for name, obj in self.warehouse.data.items()
        }

        return {
            "manager_name": self.name,
            "warehouse_name": self.warehouse.name,
            "storage_count": len(self.warehouse.data),
            "storages": storages_info,
            "movement_log": self._movement_log.copy(),
            "log_entries": len(self._movement_log),
            "undo_stack_size": len(self._undo_stack),
        }

    # ----------------------------- Logging ----------------------------- #
    def _log_movement(self, /, **movement_log: Any) -> None:
        """
        Record an operation performed on the warehouse.
        """
        now = datetime.now().astimezone()
        entry = {
            "date": now.date().isoformat(),
            "time": now.time().strftime("%H:%M:%S"),
            "timezone": now.strftime("%z"),
            "operation": movement_log.get("operation"),
            "storage_name": movement_log.get("storage_name"),
            "agent_name": movement_log.get("agent_name"),
            "warehouse": getattr(self.warehouse, "warehouse_name", None),
            "success": movement_log.get("success"),
            "details": movement_log.get("details") or {},
        }
        self._movement_log.append(entry)

        logger.info(
            "[%s] %s '%s' (success=%s)",
            self.name,
            entry["operation"],
            entry["storage_name"],
            entry["success"],
        )

    def get_movements_log(self) -> List[dict[str, object]]:
        """
        Return a snapshot of the movement log.
        """
        return self._movement_log.copy()

    # ----------------------------- Helpers ----------------------------- #
    def _resolve_targets(
        self, storage_type: StorageType, storage_name: str
    ) -> Dict[str, Storage[Box]]:
        """
        Resolve target storages based on name and type filters.
        """
        classes = Box if storage_type == "all" else STORAGE_CLASSES[storage_type]

        if storage_name != "all":
            obj = self.warehouse.data.get(storage_name)
            if obj and isinstance(obj, classes):
                return {storage_name: obj}
            return {}

        return {
            name: obj
            for name, obj in self.warehouse.data.items()
            if isinstance(obj, classes)
        }

    def _register_undo(
        self,
        operation: Literal["add", "delete"],
        name: str,
        backup: Optional[Storage[Box]],
    ) -> None:
        """
        Register undo information for a destructive operation.
        """
        self._undo_stack.append(
            {
                "operation": operation,
                "name": name,
                "backup": py_copy.deepcopy(backup) if backup else None,
            }
        )

    # ----------------------------- Add ----------------------------- #
    def add(
        self,
        storage: Storage[Box],
        storage_name: Optional[str] = None,
        agent_name: Optional[str] = None,
        overwrite: bool = False,
    ) -> None:
        """
        Add a Box to the Warehouse.
        """
        if storage_name is None:
            raise ValueError("Missing required argument: 'storage_name'")

        old_obj = self.warehouse.data.get(storage_name)
        if old_obj and not overwrite:
            self._log_movement(
                operation="add",
                storage_name=storage_name,
                agent_name=agent_name,
                success=False,
                details={"reason": "exists"},
            )
            return

        self._register_undo("add", storage_name, old_obj)
        self.warehouse.data[storage_name] = storage

        self._log_movement(
            operation="add",
            storage_name=storage_name,
            agent_name=agent_name,
            success=True,
        )

    # ----------------------------- Get ----------------------------- #
    def get(
        self,
        agent_name: str,
        storage_type: StorageType = "all",
        storage_name: str = "all",
    ) -> StorageResult:
        """
        Retrieve one or more storage objects from the Warehouse.
        """
        targets = self._resolve_targets(storage_type, storage_name)

        result: StorageResult
        if storage_name != "all":
            result = next(iter(targets.values()), None)
        else:
            result = targets

        self._log_movement(
            operation="get",
            storage_type=storage_type,
            storage_name=storage_name,
            agent_name=agent_name,
            success=True,
            details={"count": len(targets)},
        )
        return result

    # ----------------------------- Delete ----------------------------- #
    def delete(
        self, storage_type: StorageType, storage_name: str = "all"
    ) -> StorageResult:
        """
        Remove one or more storage objects from the Warehouse.
        """
        targets = self._resolve_targets(storage_type, storage_name)

        for name, obj in targets.items():
            self._register_undo("delete", name, obj)
            del self.warehouse.data[name]

        result: StorageResult
        if storage_name != "all":
            result = next(iter(targets.values()), None)
        else:
            result = targets

        self._log_movement(
            operation="delete",
            storage_type=storage_type,
            storage_name=storage_name,
            agent_name=None,
            success=bool(targets),
            details={"removed_count": len(targets)},
        )
        return result

    # ----------------------------- Utilities ----------------------------- #
    def rename(self, old_name: str, new_name: str) -> bool:
        """
        Rename an existing storage object.
        """
        if old_name not in self.warehouse.data or new_name in self.warehouse.data:
            return False

        self.warehouse.data[new_name] = self.warehouse.data.pop(old_name)
        self._log_movement(
            operation="rename",
            storage_name=new_name,
            agent_name=None,
            success=True,
            details={"from": old_name, "to": new_name},
        )
        return True

    def copy(self, storage_name: str, new_name: str) -> bool:
        """
        Create a deep copy of an existing storage object.
        """
        obj = self.warehouse.data.get(storage_name)
        if not obj or new_name in self.warehouse.data:
            return False

        self.warehouse.data[new_name] = py_copy.deepcopy(obj)
        self._log_movement(
            operation="copy",
            storage_name=new_name,
            agent_name=None,
            success=True,
            details={"from": storage_name},
        )
        return True

    def batch_add(
        self, items: Dict[str, Storage[Box]], overwrite: bool = False
    ) -> None:
        """
        Add multiple storage objects in a single operation.
        """
        for name, obj in items.items():
            self.add(obj, storage_name=name, overwrite=overwrite)

    def search_by_metadata(self, key: str, value: Any) -> Dict[str, Storage[Box]]:
        """
        Search storage objects by metadata key-value match.
        """
        return {
            name: obj
            for name, obj in self.warehouse.data.items()
            if getattr(obj, "metadata", {}).get(key) == value
        }

    def snapshot(self) -> Dict[str, Storage[Box]]:
        """
        Capture a shallow snapshot of the current warehouse state.
        """
        return self.warehouse.data.copy()

    def undo_last_action(self) -> bool:
        """
        Revert the most recent add or delete operation.
        """
        if not self._undo_stack:
            return False

        last = self._undo_stack.pop()
        op, name, backup = last["operation"], last["name"], last["backup"]

        if op == "add":
            if backup:
                self.warehouse.data[name] = backup
            else:
                self.warehouse.data.pop(name, None)

        elif op == "delete" and backup:
            self.warehouse.data[name] = backup

        self._log_movement(
            operation="undo",
            storage_name=name,
            agent_name=None,
            success=True,
            details={"reverted_operation": op},
        )
        return True
