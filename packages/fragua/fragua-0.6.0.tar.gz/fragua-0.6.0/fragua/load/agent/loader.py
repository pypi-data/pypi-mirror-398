"""
Loader Agent Class.

Defines the Loader agent responsible for applying load styles to
stored Box objects and persisting their data into target destinations
(e.g. files, databases, external systems).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Union

from fragua.core.agent import FraguaAgent
from fragua.core.params import FraguaParams
from fragua.core.storage import Box, Container
from fragua.utils.logger import get_logger

if TYPE_CHECKING:
    from fragua.core.environment import FraguaEnvironment


logger = get_logger(__name__)

# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments


class Loader(FraguaAgent):
    """
    Loader agent responsible for executing load workflows.

    The Loader:
    - retrieves Box objects from the Warehouse
    - groups them into a Container
    - executes load functions over each Box
    - does not generate new data storages, but performs side effects
    (files, databases, external systems)
    """

    def __init__(self, name: str, environment: FraguaEnvironment) -> None:
        """
        Initialize the Loader agent.

        Args:
            name: Agent identifier.
            environment: Active Fragua environment.
        """
        super().__init__(agent_name=name, environment=environment)
        self.role = "loader"
        self.action = "load"
        self.storage_type = "Container"

    # ----------------- Container helpers ----------------- #
    def _create_container(self, sources: Union[str, List[str]]) -> Container:
        """
        Create a Container populated with Box objects from the warehouse.

        Args:
            sources: One or more storage names to retrieve.

        Returns:
            A Container holding the resolved Box objects.

        Raises:
            TypeError: If resolved objects are not Box instances.
        """
        container = self.create_storage(
            style_name=self.action,
            storage_name="load_container",
            data=None,
        )

        if not isinstance(container, Container):
            raise TypeError(f"Expected Container, got {type(container).__name__}.")

        names = [sources] if isinstance(sources, str) else sources

        for name in names:
            box = self.get_from_warehouse(name)

            if not isinstance(box, Box):
                raise TypeError(f"Storage '{name}' is not a Box and cannot be loaded.")

            container.add_storage(name, box)

        return container

    def _resolve_params_for_box(
        self,
        style: str,
        box_name: str,
        params: Optional[FraguaParams],
        **kwargs: Any,
    ) -> FraguaParams:
        """
        Resolve Params for a specific Box.
        """
        if params is not None:
            return params

        params_cls = self._get_params(style)

        resolved_kwargs = dict(kwargs)

        # Excel-style: auto sheet_name
        if "sheet_name" in params_cls.FIELDS and not resolved_kwargs.get("sheet_name"):
            resolved_kwargs["sheet_name"] = box_name

        # SQL-style: auto table_name
        if "table_name" in params_cls.FIELDS and not resolved_kwargs.get("table_name"):
            resolved_kwargs["table_name"] = box_name

        return params_cls(**resolved_kwargs)

    # ----------------- Work method ----------------- #
    def work(
        self,
        style: str,
        apply_to: Union[str, List[str], None] = None,
        save_as: Optional[str] = None,
        params: Optional[FraguaParams] = None,
        input_data: Any = None,
        **kwargs: Any,
    ) -> None:
        """
        Execute the load workflow.
        Args:
            style: Load style to apply.
            apply_to: One or more Box names to load from the warehouse.
            save_as: Not used in Loader; present for interface consistency.
            params: Optional Params instance to use for loading.
            input_data: Not used in Loader; present for interface consistency.
            **kwargs: Additional parameters for the load function.
        Raises:
            TypeError: If 'apply_to' is not provided.
        """
        if apply_to is None:
            raise TypeError("Missing required argument: 'apply_to'.")

        style = style.lower()

        style_spec = self._resolve_style(style)
        func = self._resolve_function(style_spec["function_key"])
        container = self._create_container(apply_to)

        for box_name in container.list_storages():
            box = container.get_storage(box_name)

            params_instance = self._resolve_params_for_box(
                style=style,
                box_name=box_name,
                params=params,
                **kwargs,
            )

            func(input_data=box.data, params=params_instance)

            self._add_operation(style, params_instance)
