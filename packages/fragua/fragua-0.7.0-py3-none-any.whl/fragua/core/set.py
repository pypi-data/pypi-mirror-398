"""
Fragua Set class.
"""

from abc import ABC
from typing import Any, Dict, Generic, Optional, TypeVar

from fragua.core.fragua_class import FraguaClass
from fragua.core.fragua_instance import FraguaInstance

T = TypeVar("T")


class FraguaSet(ABC, Generic[T]):
    """
    Logical container for Fragua components.

    A FraguaSet groups homogeneous elements under a common scope
    (params schemas, functions, styles, agents, etc.).

    The set is explicitly configured to store either declarative
    classes or runtime instances.
    """

    def __init__(
        self,
        set_name: str,
        *,
        components: Optional[Dict[str, T]] = None,
    ) -> None:
        """
        Initialize the set.

        Args:
            set_name:
                Identifier of the set within its parent registry.
            components:
                Optional preloaded elements.
        """
        self.set_name = set_name
        self._components: Dict[str, T] = {} if components is None else components

    def _exists(self, key: str) -> bool:
        return key in self._components

    def _not_exists(self, key: str) -> bool:
        return key not in self._components

    def add(self, name: str, component: T) -> bool:
        """
        Add a new element to the set.
        """
        if self._not_exists(name):
            self._components[name] = component
            return True
        return False

    def get_one(self, name: str) -> Optional[T]:
        """
        Retrieve a single element by name.

        Args:
            name: Name of the element.

        Returns:
            The element if found, otherwise None.
        """
        return self._components.get(name)

    def get_all(self) -> Dict[str, T]:
        """
        Retrieve all elements in the set.

        Returns:
            A dictionary mapping element names to elements.
        """
        return self._components

    def update(self, old_name: str, new_name: str) -> bool:
        """
        Rename an element within the set.

        Args:
            old_name: Current element name.
            new_name: New element name.

        Returns:
            True if the element was renamed successfully, False if the
            old name does not exist or the new name is already in use.
        """
        if self._exists(old_name) and self._not_exists(new_name):
            self._components[new_name] = self._components.pop(old_name)
            return True
        return False

    def delete_one(self, name: str) -> bool:
        """
        Remove an element from the set.

        Args:
            name: Name of the element to delete.

        Returns:
            True if the element was removed, False if it did not exist.
        """
        return self._components.pop(name, None) is not None

    def summary(self) -> Dict[str, Any]:
        """
        Return a structured summary of the set contents.

        Delegates summary generation to the contained elements
        according to the declared content kind.
        """
        result: Dict[str, Any] = {}

        for name, component in self._components.items():
            # Case 1: Fragua class
            if isinstance(component, type) and issubclass(component, FraguaClass):
                result[name] = component.summary()

            # Case 2: Fragua instance
            elif isinstance(component, FraguaInstance):
                result[name] = component.summary()

            # Case 3: Dictionary of components (variants / profiles)
            elif isinstance(component, dict):
                nested: Dict[str, Any] = {}
                for key, value in component.items():
                    if isinstance(value, type) and issubclass(value, FraguaClass):
                        nested[key] = value.summary()
                    elif isinstance(value, FraguaInstance):
                        nested[key] = value.summary()
                    else:
                        nested[key] = value.__class__.__name__
                result[name] = nested

            # Fallback (should not normally happen)
            else:
                result[name] = component.__class__.__name__

        return result
