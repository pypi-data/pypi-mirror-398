"""
Base class for all registries of an environment in Fragua.
"""

from typing import Any, Dict, Optional

from fragua.core.fragua_instance import FraguaInstance
from fragua.core.set import FraguaSet


class FraguaRegistry(FraguaInstance):
    """
    Runtime registry within a Fragua environment.

    A FraguaRegistry manages a collection of FraguaSet instances,
    each representing a logical grouping of related components
    (such as styles, params, or functions).

    Registries are stateful and exist only at runtime.
    """

    def __init__(self, registry_name: str) -> None:
        """
        Initialize the registry with a name.

        Args:
            registry_name:
                Identifier used to reference this registry
                within the environment.
        """
        super().__init__(instance_name=registry_name)

        self._sets: Dict[str, FraguaSet[Any]] = {}

    def _exists(self, key: str) -> bool:
        """Return True if a set exists in the registry."""
        return key in self._sets

    def _not_exists(self, key: str) -> bool:
        """Return True if a set does not exist in the registry."""
        return key not in self._sets

    def get_sets(self) -> Dict[str, FraguaSet[Any]]:
        """
        Retrieve all registered sets.

        Returns:
            A mapping of set names to FraguaSet instances.
        """
        return self._sets

    def add_set(self, name: str, registry_set: FraguaSet[Any]) -> bool:
        """
        Register a new FraguaSet.

        Returns:
            True if created successfully, False if already exists.
        """
        if self._not_exists(name):
            self._sets[name] = registry_set
            return True
        return False

    def get_set(self, name: str) -> Optional[FraguaSet[Any]]:
        """
        Retrieve a set by name.
        """
        return self._sets.get(name)

    def update_set(self, old_name: str, new_name: str) -> bool:
        """
        Rename an existing set.
        """
        if self._exists(old_name) and self._not_exists(new_name):
            self._sets[new_name] = self._sets.pop(old_name)
            return True
        return False

    def delete_set(self, name: str) -> bool:
        """
        Remove a set from the registry.
        """
        return self._sets.pop(name, None) is not None

    # ------------------------------------------------------------------
    @property
    def params(self) -> FraguaSet[Any]:
        """
        Access the set containing extract parameter schemas.

        Returns:
            ExtractParamsSet instance.
        """
        if "params" in self._sets:
            return self._sets["params"]
        raise KeyError("Params set not found in registry.")

    @property
    def functions(self) -> FraguaSet[Any]:
        """
        Access the set containing extract functions.

        Returns:
            ExtractFunctionSet instance.
        """
        if "functions" in self._sets:
            return self._sets["functions"]
        raise KeyError("Functions set not found in registry.")

    @property
    def styles(self) -> FraguaSet[Any]:
        """
        Access the set containing extract styles.

        Returns:
            ExtractStyleSet instance.
        """
        if "styles" in self._sets:
            return self._sets["styles"]
        raise KeyError("Styles set not found in registry.")

    @property
    def agents(self) -> FraguaSet[Any]:
        """
        Access the set containing extract agents.

        Returns:
            ExtractAgentSet instance.
        """
        if "agents" in self._sets:
            return self._sets["agents"]
        raise KeyError("Agents set not found in registry.")

    def summary(self) -> Dict[str, Any]:
        """
        Return a summary of the registry contents.
        Returns:
            A dictionary summarizing the contents of each set.

        """
        summary = {
            "params": self.params.summary(),
            "functions": self.functions.summary(),
            "styles": self.styles.summary(),
            "agents": self.agents.summary(),
        }

        return summary

    def __repr__(self) -> str:
        """
        Return a concise string representation of the registry.
        """
        return f"{self.__class__.__name__}('{self.name}')"
