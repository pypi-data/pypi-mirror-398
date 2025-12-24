"""Actions class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional
from fragua.core.fragua_instance import FraguaInstance
from fragua.core.registry import FraguaRegistry

from fragua.core.set import FraguaSet
from fragua.extract import EXTRACT_STYLES, EXTRACT_FUNCTIONS, EXTRACT_PARAMS
from fragua.transform import (
    TRANSFORM_STYLES,
    TRANSFORM_FUNCTIONS,
    TRANSFORM_PARAMS,
)
from fragua.load import LOAD_STYLES, LOAD_FUNCTIONS, LOAD_PARAMS


if TYPE_CHECKING:
    from fragua.core.environment import FraguaEnvironment


class FraguaActions(FraguaInstance):
    """Container for all action registries (extract, transform, load)."""

    SET_TYPES = ["functions", "params", "styles", "agents"]
    FG_SETS: Dict[str, Dict[str, Any]] = {
        "extract": {
            "functions": EXTRACT_FUNCTIONS,
            "params": EXTRACT_PARAMS,
            "styles": EXTRACT_STYLES,
            "agents": {},
        },
        "transform": {
            "functions": TRANSFORM_FUNCTIONS,
            "params": TRANSFORM_PARAMS,
            "styles": TRANSFORM_STYLES,
            "agents": {},
        },
        "load": {
            "functions": LOAD_FUNCTIONS,
            "params": LOAD_PARAMS,
            "styles": LOAD_STYLES,
            "agents": {},
        },
    }

    def __init__(
        self,
        environment: FraguaEnvironment,
        extract: Optional[FraguaRegistry] = None,
        transform: Optional[FraguaRegistry] = None,
        load: Optional[FraguaRegistry] = None,
    ) -> None:
        super().__init__(instance_name="actions")
        self.environment: FraguaEnvironment = environment
        self._extract = (
            self._initialize_registry("extract") if extract is None else extract
        )
        self._transform = (
            self._initialize_registry("transform") if transform is None else transform
        )
        self._load = self._initialize_registry("load") if load is None else load

    def _to_fg_registry(
        self, registry: FraguaRegistry, dict_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Populate registries with default Fragua sets.
        """
        for set_type, components in dict_data.items():
            fragua_set = FraguaSet(set_name=set_type, components=components)
            registry.add_set(set_type, fragua_set)

    def _to_empty_registry(self, registry: FraguaRegistry) -> None:
        """
        Populate registries with empty Fragua sets.
        """
        for set_type in self.SET_TYPES:
            fragua_set: FraguaSet[Any] = FraguaSet(set_name=set_type, components={})
            registry.add_set(set_type, fragua_set)

    def _initialize_registry(self, registry_name: str) -> FraguaRegistry:
        """Initialize a generic action registry."""
        registry = FraguaRegistry(registry_name)
        if self.environment.fg_config:
            fg_data = self.FG_SETS[registry_name]

            self._to_fg_registry(registry, fg_data)
        else:
            self._to_empty_registry(registry)
        return registry

    @property
    def extract(self) -> FraguaRegistry:
        """
        Access the Extract action registry.

        Returns:
            The ExtractRegistry instance.
        """
        return self._extract

    @property
    def transform(self) -> FraguaRegistry:
        """
        Access the Transform action registry.

        Returns:
            The TransformRegistry instance.
        """
        return self._transform

    @property
    def load(self) -> FraguaRegistry:
        """
        Access the Load action registry.

        Returns:
            The LoadRegistry instance.
        """
        return self._load

    @property
    def params(self) -> Dict[str, FraguaSet[Any]]:
        """
        Retrieve all parameter sets grouped by action.

        Returns:
            Dict[str, FraguaSet]:
                Mapping of action name to its corresponding params set.
        """
        return {
            "extract": self.extract.params,
            "transform": self.transform.params,
            "load": self.load.params,
        }

    @property
    def functions(self) -> Dict[str, FraguaSet[Any]]:
        """
        Retrieve all function sets grouped by action.

        Returns:
            Dict[str, FraguaSet]:
                Mapping of action name to its corresponding functions set.
        """
        return {
            "extract": self.extract.functions,
            "transform": self.transform.functions,
            "load": self.load.functions,
        }

    @property
    def agents(self) -> Dict[str, FraguaSet[Any]]:
        """
        Retrieve all agent sets grouped by action.

        Returns:
            Dict([str, FraguaSet]):
                Mapping of action name to its corresponding agents set.
        """
        return {
            "extract": self.extract.agents,
            "transform": self.transform.agents,
            "load": self.load.agents,
        }

    @property
    def styles(self) -> Dict[str, FraguaSet[Any]]:
        """
        Retrieve all style sets grouped by action.

        Returns:
            Dict([str, FraguaSet]):
                Mapping of action name to its corresponding styles set.
        """
        return {
            "extract": self.extract.styles,
            "transform": self.transform.styles,
            "load": self.load.styles,
        }

    def summary(self) -> Dict[str, Any]:
        """
        Return a structured summary of all registered actions.

        This method aggregates the summaries of each action registry
        (extract, transform, and load) into a single structured object.


        Returns:
            Dict([str, Any]):
                A dictionary with the following structure:
                - extract (dict): Summary of the Extract registry
                - transform (dict): Summary of the Transform registry
                - load (dict): Summary of the Load registry
        """
        return {
            "extract": self.extract.summary(),
            "transform": self.transform.summary(),
            "load": self.load.summary(),
        }
