"""
Lightweight in-memory warehouse structure.
"""

from __future__ import annotations
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    TypeAlias,
    Union,
    TYPE_CHECKING,
)
from datetime import datetime
import copy as py_copy
from fragua.core.fragua_instance import FraguaInstance
from fragua.core.storage import Storage, Box, STORAGE_CLASSES
from fragua.utils.security.security_context import FraguaToken
from fragua.utils.logger import get_logger
from fragua.utils.types.enums import AttrType, OperationType, StorageType

logger = get_logger(__name__)

AllowedTypes = Literal[StorageType.BOX, StorageType.ALL]

StorageResult: TypeAlias = Union[
    Optional[Storage[Box]],
    Mapping[str, Storage[Box]],
]

if TYPE_CHECKING:
    from fragua.core.environment import FraguaEnvironment

# pylint: disable=too-many-arguments


class MovementLog:
    """
    Append-only log for warehouse operations.
    """

    def __init__(self) -> None:
        self._entries: List[Mapping[str, object]] = []

    def record(
        self,
        *,
        operation: str,
        storage_name: str | None,
        agent_name: str | None,
        warehouse_name: str | None,
        success: bool,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record a new log entry."""
        now = datetime.now().astimezone()
        entry = {
            "date": now.date().isoformat(),
            "time": now.time().strftime("%H:%M:%S"),
            "timezone": now.strftime("%z"),
            "operation": operation,
            "storage_name": storage_name,
            "agent_name": agent_name,
            "warehouse": warehouse_name,
            "success": success,
            "details": details or {},
        }
        self._entries.append(entry)

        logger.info(
            "[%s] %s '%s' (success=%s)",
            warehouse_name,
            operation,
            storage_name,
            success,
        )

    def snapshot(self) -> List[Mapping[str, object]]:
        """Get a copy of all log entries."""
        return self._entries.copy()

    def __len__(self) -> int:
        return len(self._entries)


class FraguaWarehouse(FraguaInstance):
    """
    In-memory aggregate root for Storage objects.

    The Warehouse is responsible for:
    - Storage lifecycle management
    - Authorization
    - Consistency rules
    - Movement logging
    - Undo operations
    """

    def __init__(self, warehouse_name: str, environment: FraguaEnvironment) -> None:
        super().__init__(instance_name=warehouse_name)

        self._storages: Dict[str, Storage[Box]] = {}
        self._environment = environment
        self._movement_log = MovementLog()
        self._undo_stack: list[dict[str, Any]] = []

    # ----------------------------- Security ---------------------------- #
    def _authorize(self, token: FraguaToken) -> None:
        if not self._environment.security.validate(token):
            raise PermissionError(
                "Unauthorized warehouse access: invalid or foreign token."
            )

    # ----------------------------- Internals --------------------------- #
    def _register_undo(
        self,
        operation: Literal[OperationType.ADD, OperationType.DELETE],
        name: str,
        backup: Storage[Box] | None,
    ) -> None:
        self._undo_stack.append(
            {
                "operation": operation.value,
                AttrType.NAME: name,
                "backup": py_copy.deepcopy(backup) if backup else None,
            }
        )

    def _resolve_targets(
        self,
        storage_type: AllowedTypes,
        storage_name: str,
    ) -> Dict[str, Storage[Box]]:
        classes = (
            Box
            if storage_type.value == StorageType.ALL.value
            else STORAGE_CLASSES[storage_type.value]
        )

        if storage_name != StorageType.ALL.value:
            obj = self._storages.get(storage_name)
            if obj and isinstance(obj, classes):
                return {storage_name: obj}
            return {}

        return {
            name: obj
            for name, obj in self._storages.items()
            if isinstance(obj, classes)
        }

    # ----------------------------- Mutations --------------------------- #
    def add_storage(
        self,
        name: str,
        storage: Storage[Box],
        *,
        token: FraguaToken,
        agent_name: str | None = None,
        overwrite: bool = False,
    ) -> bool:
        """Add storage to warehouse."""
        self._authorize(token)

        if name in self._storages and not overwrite:
            self._movement_log.record(
                operation=OperationType.ADD.value,
                storage_name=name,
                agent_name=agent_name,
                warehouse_name=self.name,
                success=False,
                details={"reason": "exists"},
            )
            return False

        previous = self._storages.get(name)
        self._register_undo(OperationType.ADD, name, previous)

        self._storages[name] = storage

        self._movement_log.record(
            operation=OperationType.ADD.value,
            storage_name=name,
            agent_name=agent_name,
            warehouse_name=self.name,
            success=True,
        )
        return True

    def delete_storages(
        self,
        *,
        token: FraguaToken,
        storage_type: AllowedTypes = StorageType.ALL,
        storage_name: str = StorageType.ALL.value,
        agent_name: str | None = None,
    ) -> StorageResult:
        """Delete storage from warehouse."""
        self._authorize(token)

        targets = self._resolve_targets(storage_type, storage_name)

        for name, obj in targets.items():
            self._register_undo(OperationType.DELETE, name, obj)
            self._storages.pop(name, None)

        self._movement_log.record(
            operation=OperationType.DELETE.value,
            storage_name=storage_name,
            agent_name=agent_name,
            warehouse_name=self.name,
            success=bool(targets),
            details={"removed_count": len(targets)},
        )

        return (
            next(iter(targets.values()), None)
            if storage_name != StorageType.ALL
            else targets
        )

    # ----------------------------- Queries ----------------------------- #
    def get_storages(
        self,
        *,
        token: FraguaToken,
        storage_type: AllowedTypes = StorageType.ALL,
        storage_name: str = StorageType.ALL.value,
        agent_name: str | None = None,
    ) -> StorageResult:
        """Get storage from warehouse."""
        self._authorize(token)

        targets = self._resolve_targets(storage_type, storage_name)

        self._movement_log.record(
            operation=OperationType.GET,
            storage_name=storage_name,
            agent_name=agent_name,
            warehouse_name=self.name,
            success=True,
            details={"count": len(targets)},
        )

        return (
            next(iter(targets.values()), None)
            if storage_name != StorageType.ALL.value
            else targets
        )

    def search_by_metadata(self, key: str, value: Any) -> Dict[str, Storage[Box]]:
        """Search storage by metadata."""
        return {
            name: obj
            for name, obj in self._storages.items()
            if getattr(obj, "metadata", {}).get(key) == value
        }

    def snapshot(self) -> Dict[str, Storage[Box]]:
        """Return a view from the warehouse."""
        return dict(self._storages)

    # ----------------------------- Utilities --------------------------- #
    def rename_storage(
        self, old_name: str, new_name: str, *, token: FraguaToken
    ) -> bool:
        """Rename an storage from warehouse."""
        self._authorize(token)

        if old_name not in self._storages or new_name in self._storages:
            return False

        self._storages[new_name] = self._storages.pop(old_name)

        self._movement_log.record(
            operation=OperationType.RENAME.value,
            storage_name=new_name,
            agent_name=None,
            warehouse_name=self.name,
            success=True,
            details={"from": old_name, "to": new_name},
        )
        return True

    def copy_storage(self, name: str, new_name: str, *, token: FraguaToken) -> bool:
        """Copy an storage from the warehouse."""
        self._authorize(token)

        obj = self._storages.get(name)
        if not obj or new_name in self._storages:
            return False

        self._storages[new_name] = py_copy.deepcopy(obj)

        self._movement_log.record(
            operation=OperationType.COPY.value,
            storage_name=new_name,
            agent_name=None,
            warehouse_name=self.name,
            success=True,
            details={"from": name},
        )
        return True

    # ----------------------------- Undo -------------------------------- #
    def undo_last_action(self, *, token: FraguaToken) -> bool:
        """Revert last action done."""
        self._authorize(token)

        if not self._undo_stack:
            return False

        action = self._undo_stack.pop()
        op = action["operation"]
        name = action[AttrType.NAME.value]
        backup = action["backup"]

        if op == OperationType.ADD.value:
            if backup:
                self._storages[name] = backup
            else:
                self._storages.pop(name, None)

        elif op == OperationType.DELETE.value and backup:
            self._storages[name] = backup

        self._movement_log.record(
            operation=OperationType.UNDO.value,
            storage_name=name,
            agent_name=None,
            warehouse_name=self.name,
            success=True,
            details={"reverted_operation": op},
        )
        return True

    # ----------------------------- Introspection ----------------------- #
    def summary(self) -> Dict[str, Any]:
        return {
            "warehouse_name": self.name,
            "storage_count": len(self),
            "storages": {
                name: storage.__class__.__name__
                for name, storage in self._storages.items()
            },
            "log_entries": len(self._movement_log),
            "undo_stack_size": len(self._undo_stack),
        }

    def __len__(self) -> int:
        return len(self._storages)
