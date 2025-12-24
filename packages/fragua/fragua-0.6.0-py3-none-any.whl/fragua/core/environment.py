"""Base environment class for Fragua, refactored with docstrings."""

from __future__ import annotations

from typing import Any, Dict, Optional, Type, cast

from fragua.core.agent import FraguaAgent
from fragua.core.actions import FraguaActions
from fragua.core.fragua_class import FraguaClass
from fragua.core.fragua_instance import FraguaInstance
from fragua.core.registry import FraguaRegistry
from fragua.core.set import FraguaSet
from fragua.core.warehouse import FraguaWarehouse
from fragua.core.manager import FraguaManager


from fragua.extract import Extractor
from fragua.transform import Transformer
from fragua.load import Loader


from fragua.utils.logger import get_logger

logger = get_logger(__name__)

# pylint: disable=too-many-lines
# pylint: disable=too-many-public-methods


class FraguaEnvironment(FraguaInstance):
    """
    Core environment abstraction for Fragua.

    This class represents the top-level orchestration layer of the framework.
    It encapsulates and coordinates all fundamental components, including
    the warehouse, warehouse manager, action registries, and agents.

    The Environment is responsible for initializing, exposing, and managing
    the lifecycle of all ETL-related components within a given execution context.
    """

    def __init__(self, env_name: str, env_type: str = "base", fg_config: bool = False):
        """
        Initialize a Fragua execution environment.

        This constructor bootstraps all core components required for
        ETL operations, including the warehouse, its manager, and
        the action registries (extract, transform, load).

        Args:
            env_name (str):
                Logical name of the environment instance.
            env_type (str):
                Environment classification or variant.
                Defaults to "base".
            fg_config (bool):
                Enables the default Fragua configuration.
                When True, built-in components such as parameters,
                functions, styles, and agents are automatically registered.
        """

        super().__init__(instance_name=env_name)
        self.env_type = env_type
        self.fg_config = fg_config
        self.warehouse = self._initialize_warehouse()
        self.manager = self._initialize_manager()
        self.actions = self._initialize_actions()

        logger.debug(
            "Environment '%s' initialized (type=%s).", self.name, self.env_type
        )

    # ---------------------- Error Handle ---------------------- #
    def agent_not_found(self) -> ValueError:
        """
        Generate a standardized error for missing agents.

        Returns:
            ValueError:
                Exception indicating that the requested agent
                does not exist within the current environment.
        """

        return ValueError("Agent not found.")

    # ---------------------- Initializers ---------------------- #

    def _initialize_warehouse(self) -> FraguaWarehouse:
        """
        Initialize the warehouse for the environment.

        The warehouse serves as the central data container where
        intermediate and final datasets are stored during
        extract, transform, and load operations.

        Returns:
            FraguaWarehouse:
                Initialized warehouse instance bound to this environment.
        """

        warehouse = FraguaWarehouse(f"{self.name}_warehouse")

        logger.info("Default warehouse initialized for environment '%s'.", self.name)
        return warehouse

    def _initialize_manager(self) -> FraguaManager:
        """
        Initialize the warehouse manager for the environment.

        The warehouse manager acts as the coordination layer between
        agents and the underlying warehouse, controlling access,
        execution flow, and resource usage.

        Returns:
            FraguaManager:
                Fully initialized warehouse manager instance.
        """

        manager = FraguaManager(f"{self.name}_manager", self)

        logger.info(
            "Default warehouse manager initialized for environment '%s'.", self.name
        )
        return manager

    def _initialize_actions(self) -> FraguaActions:
        """
        Initialize action registries for the environment.

        This method sets up all action-specific registries
        (extract, transform, load), optionally preloading
        default Fragua components when fg_config is enabled.

        Returns:
            FraguaActions:
                Container holding all action registries.
        """

        actions = FraguaActions(self)
        logger.info("Default actions initialized for environment '%s'.", self.name)
        return actions

    # ---------------------- Helper Properties ---------------------- #
    @property
    def extract(self) -> FraguaRegistry:
        """
        Access the Extract action registry.

        Returns:
            ExtractRegistry:
                Registry containing all extract-related components
                (agents, params, functions, and styles).
        """
        return self.actions.extract

    @property
    def transform(self) -> FraguaRegistry:
        """
        Access the Transform action registry.

        Returns:
            TransformRegistry:
                Registry containing all transform-related components
                (agents, params, functions, and styles).
        """
        return self.actions.transform

    @property
    def load(self) -> FraguaRegistry:
        """
        Access the Load action registry.

        Returns:
            LoadRegistry:
                Registry containing all load-related components
                (agents, params, functions, and styles).
        """
        return self.actions.load

    @property
    def params(self) -> Dict[str, FraguaSet[Any]]:
        """
        Retrieve all parameter sets grouped by action.

        Returns:
            Dict[str, FraguaSet]:
                Mapping of action name to its corresponding params set.
        """
        return self.actions.params

    @property
    def functions(self) -> Dict[str, FraguaSet[Any]]:
        """
        Retrieve all function sets grouped by action.

        Returns:
            Dict[str, FraguaSet]:
                Mapping of action name to its corresponding functions set.
        """
        return self.actions.functions

    @property
    def agents(self) -> Dict[str, FraguaSet[Any]]:
        """
        Retrieve all agent sets grouped by action.

        Returns:
            Dict([str, FraguaSet]):
                Mapping of action name to its corresponding agents set.
        """
        return self.actions.agents

    @property
    def styles(self) -> Dict[str, FraguaSet[Any]]:
        """
        Retrieve all style sets grouped by action.

        Returns:
            Dict([str, FraguaSet]):
                Mapping of action name to its corresponding styles set.
        """
        return self.actions.styles

    # ---------------------- Internal helpers ---------------------- #
    def _get_set(self, action: str, kind: str) -> FraguaSet[Any]:
        """
        Resolve a FraguaSet by action and component kind.

        Args:
            action: Action type ("extract", "transform", "load").
            kind: Component kind ("agents", "params", "functions", "styles").

        Returns:
            The resolved FraguaSet.

        Raises:
            ValueError: If the action or component kind is invalid.
        """
        registries = {
            "agents": self.agents,
            "params": self.params,
            "functions": self.functions,
            "styles": self.styles,
        }

        if kind not in registries:
            raise ValueError(f"Invalid component kind: {kind}")

        action_sets = registries[kind]
        fragua_set = action_sets.get(action)

        if fragua_set is None:
            raise ValueError(f"Invalid action type: {action}")

        return fragua_set

    def _create(
        self,
        *,
        action: str,
        kind: str,
        name: str,
        component: Any,
    ) -> bool:
        fragua_set = self._get_set(action, kind)
        created = fragua_set.add(name, component)

        if created:
            logger.info("%s registered: %s (%s)", kind[:-1].capitalize(), name, action)

        return created

    def _get(
        self,
        *,
        action: str,
        kind: str,
        name: str | None = None,
    ) -> Any:
        fragua_set = self._get_set(action, kind)

        if name is None:
            all_items = fragua_set.get_all()
            return next(iter(all_items.values()), None)

        return fragua_set.get_one(name)

    def _update(
        self,
        *,
        action: str,
        kind: str,
        old_name: str,
        new_name: str,
    ) -> bool:
        fragua_set = self._get_set(action, kind)
        updated = fragua_set.update(old_name, new_name)

        if not updated:
            raise ValueError(f"{kind[:-1].capitalize()} not found.")

        logger.info(
            "%s renamed: %s -> %s (%s)",
            kind[:-1].capitalize(),
            old_name,
            new_name,
            action,
        )

        return updated

    def _delete(
        self,
        *,
        action: str,
        kind: str,
        name: str,
    ) -> bool:
        fragua_set = self._get_set(action, kind)
        deleted = fragua_set.delete_one(name)

        if not deleted:
            raise ValueError(f"{kind[:-1].capitalize()} not found.")

        logger.info(
            "%s deleted: %s (%s)",
            kind[:-1].capitalize(),
            name,
            action,
        )

        return deleted

    # ----------------------Agents API ---------------------- #
    def create_agent(self, action: str, agent_name: str) -> bool:
        """
        Create and register a new agent for a given action.

        This method instantiates the appropriate Agent subclass based on the
        provided action type and registers it into the corresponding agent set.

        Args:
            action: Action type ("extract", "transform", "load").
            agent_name: Name to assign to the new agent.

        Returns:
            True if the agent was successfully created and registered,
            False if an agent with the same name already exists.

        Raises:
            ValueError: If the provided action type is invalid.
        """

        def _build_agent() -> FraguaAgent:
            """Instantiate the correct agent class based on action."""
            class_map: Dict[str, Type[FraguaAgent]] = {
                "extract": Extractor,
                "transform": Transformer,
                "load": Loader,
            }

            agent_class = class_map.get(action)
            if agent_class is None:
                raise ValueError(f"Invalid action type: {action}")

            return agent_class(agent_name, self)

        def _register_agent(agent: FraguaAgent) -> bool:
            """Register the agent into the corresponding set."""

            type_set = self.agents.get(action)
            if type_set is None:
                return False

            return type_set.add(agent_name, agent)

        new_agent = _build_agent()
        created = _register_agent(new_agent)

        if created:
            logger.info(
                "Agent created: %s (%s)",
                agent_name,
                new_agent.__class__.__name__,
            )

        return created

    def get_agent(
        self, action: str, agent_name: Optional[str] = None
    ) -> Optional[FraguaAgent]:
        """
        Retrieve an agent by action type and optional agent name.

        If an agent name is provided, the method returns the matching agent
        from the specified action registry. If no name is provided, the
        first registered agent for that action is returned.

        Args:
            action: Action type ("extract", "transform", "load").
            agent_name: Optional name of the agent to retrieve.

        Returns:
            The requested Agent instance if found, otherwise None.
        """

        def _set_agent() -> Optional[Any]:
            """Select agent object based on action and agent name."""

            agents_set = self.agents.get(action)
            if agents_set is None:
                return None

            if agent_name is None:
                agents = agents_set.get_all()
                return next(iter(agents.values()), None)

            return agents_set.get_one(agent_name)

        def _validate_agent(agent: Any) -> Optional[FraguaAgent]:
            """Validate and safely cast the agent to Agent type."""
            if agent is None:
                return None
            return cast(FraguaAgent, agent)

        agent = _set_agent()

        return _validate_agent(agent)

    def update_agent(
        self,
        action: str,
        old_name: str,
        new_name: str,
    ) -> bool:
        """
        Rename an existing agent within a specific action.

        Args:
            action: Action type ("extract", "transform", "load").
            old_name: Current agent name.
            new_name: New agent name.

        Returns:
            True if the agent was successfully renamed, False otherwise.
        """

        agents_set = self.agents.get(action)
        if agents_set is None:
            raise ValueError(f"Invalid action type: {action}")

        updated = agents_set.update(old_name, new_name)

        if not updated:
            raise self.agent_not_found()

        logger.info(
            "Agent renamed: %s -> %s (%s)",
            old_name,
            new_name,
            action,
        )

        return updated

    def delete_agent(self, action: str, agent_name: str) -> bool:
        """
        Delete an existing agent from a specific action.

        Args:
            action: Action type ("extract", "transform", "load").
            agent_name: Name of the agent to delete.

        Returns:
            True if the agent was successfully deleted.
        """

        agents_set = self.agents.get(action)
        if agents_set is None:
            raise ValueError(f"Invalid action type: {action}")

        deleted = agents_set.delete_one(agent_name)

        if not deleted:
            raise self.agent_not_found()

        logger.info(
            "Agent deleted: %s (%s)",
            agent_name,
            action,
        )

        return deleted

    # ----------------------Functions API ---------------------- #
    def create_function(
        self,
        action: str,
        function_name: str,
        function: Any,
    ) -> bool:
        """
        Create and register a new function for a given action.

        Functions are stored as opaque objects inside the registry.
        They may be callables, classes, or structured descriptors,
        depending on the execution model.

        Args:
            action (str):
                Action type ("extract", "transform", "load").
            function_name (str):
                Unique name for the function.
            function (Any):
                Function object to register.

        Returns:
            bool:
                True if the function was successfully registered.
                False if a function with the same name already exists.

        Raises:
            ValueError:
                If the provided action type is invalid.
        """

        functions_set = self.functions.get(action)
        if functions_set is None:
            raise ValueError(f"Invalid action type: {action}")

        created = functions_set.add(function_name, function)

        if created:
            logger.info(
                "Function created: %s (%s)",
                function_name,
                action,
            )

        return created

    def get_function(
        self,
        action: str,
        function_name: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Retrieve a function by action and optional name.

        If a function name is provided, the matching function is returned.
        If no name is provided, the first registered function for the
        given action is returned.

        Args:
            action (str):
                Action type ("extract", "transform", "load").
            function_name (Optional[str]):
                Name of the function to retrieve.

        Returns:
            Optional[Any]:
                The requested function if found, otherwise None.
        """

        functions_set = self.functions.get(action)
        if functions_set is None:
            return None

        if function_name is None:
            functions = functions_set.get_all()
            return next(iter(functions.values()), None)

        return functions_set.get_one(function_name)

    def update_function(
        self,
        action: str,
        old_name: str,
        new_name: str,
    ) -> bool:
        """
        Rename an existing function within a specific action registry.

        This operation only updates the registry key.
        The underlying function object remains unchanged.

        Args:
            action (str):
                Action type ("extract", "transform", "load").
            old_name (str):
                Current function name.
            new_name (str):
                New function name.

        Returns:
            bool:
                True if the function was successfully renamed.

        Raises:
            ValueError:
                If the action is invalid or the function does not exist.
        """

        functions_set = self.functions.get(action)
        if functions_set is None:
            raise ValueError(f"Invalid action type: {action}")

        updated = functions_set.update(old_name, new_name)

        if not updated:
            raise ValueError("Function not found.")

        logger.info(
            "Function renamed: %s -> %s (%s)",
            old_name,
            new_name,
            action,
        )

        return updated

    def delete_function(self, action: str, function_name: str) -> bool:
        """
        Delete a function from a specific action registry.

        Args:
            action (str):
                Action type ("extract", "transform", "load").
            function_name (str):
                Name of the function to delete.

        Returns:
            bool:
                True if the function was successfully deleted.

        Raises:
            ValueError:
                If the action is invalid or the function does not exist.
        """

        functions_set = self.functions.get(action)
        if functions_set is None:
            raise ValueError(f"Invalid action type: {action}")

        deleted = functions_set.delete_one(function_name)

        if not deleted:
            raise ValueError("Function not found.")

        logger.info(
            "Function deleted: %s (%s)",
            function_name,
            action,
        )

        return deleted

    # ----------------------Styles API ---------------------- #
    def create_style(
        self,
        action: str,
        style_name: str,
        style: Any,
    ) -> bool:
        """
        Create and register a new style for a given action.

        Styles are stored as opaque objects inside the registry.
        The Environment does not enforce a concrete base class,
        allowing flexible style implementations.

        Args:
            action (str):
                Action type ("extract", "transform", "load").
            style_name (str):
                Unique name for the style.
            style (Any):
                Style object or class to register.

        Returns:
            bool:
                True if the style was successfully registered.
                False if a style with the same name already exists.

        Raises:
            ValueError:
                If the provided action type is invalid.
        """

        styles_set = self.styles.get(action)
        if styles_set is None:
            raise ValueError(f"Invalid action type: {action}")

        created = styles_set.add(style_name, style)

        if created:
            logger.info(
                "Style created: %s (%s)",
                style_name,
                action,
            )

        return created

    def get_style(
        self,
        action: str,
        style_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a style by action and optional name.

        If a style name is provided, the matching style is returned.
        If no name is provided, the first registered style for the
        given action is returned.

        Args:
            action (str):
                Action type ("extract", "transform", "load").
            style_name (Optional[str]):
                Name of the style to retrieve.

        Returns:
            Optional[Any]:
                The requested style if found, otherwise None.
        """

        styles_set = self.styles.get(action)
        if styles_set is None:
            return None

        if style_name is None:
            styles = styles_set.get_all()
            return next(iter(styles.values()), None)

        return styles_set.get_one(style_name)

    def update_style(
        self,
        action: str,
        old_name: str,
        new_name: str,
    ) -> bool:
        """
        Rename an existing style within a specific action registry.

        This operation updates only the registry key.
        The underlying style object remains unchanged.

        Args:
            action (str):
                Action type ("extract", "transform", "load").
            old_name (str):
                Current style name.
            new_name (str):
                New style name.

        Returns:
            bool:
                True if the style was successfully renamed.

        Raises:
            ValueError:
                If the action is invalid or the style does not exist.
        """

        styles_set = self.styles.get(action)
        if styles_set is None:
            raise ValueError(f"Invalid action type: {action}")

        updated = styles_set.update(old_name, new_name)

        if not updated:
            raise ValueError("Style not found.")

        logger.info(
            "Style renamed: %s -> %s (%s)",
            old_name,
            new_name,
            action,
        )

        return updated

    def delete_style(self, action: str, style_name: str) -> bool:
        """
        Delete a style from a specific action registry.

        Args:
            action (str):
                Action type ("extract", "transform", "load").
            style_name (str):
                Name of the style to delete.

        Returns:
            bool:
                True if the style was successfully deleted.

        Raises:
            ValueError:
                If the action is invalid or the style does not exist.
        """

        styles_set = self.styles.get(action)
        if styles_set is None:
            raise ValueError(f"Invalid action type: {action}")

        deleted = styles_set.delete_one(style_name)

        if not deleted:
            raise ValueError("Style not found.")

        logger.info(
            "Style deleted: %s (%s)",
            style_name,
            action,
        )

        return deleted

    # ----------------------Params Management ---------------------- #
    def create_params(
        self,
        action: str,
        param_name: str,
        param: FraguaClass,
    ) -> bool:
        """
        Register a new parameter in the corresponding action registry.

        Args:
            action: Action type ("extract", "transform", "load").
            param_name: Name to assign to the parameter.
            param: Parameter component to register.

        Returns:
            True if the parameter was successfully registered,
            False if a parameter with the same name already exists.

        Raises:
            ValueError: If the provided action type is invalid.
        """

        params_set = self.params.get(action)
        if params_set is None:
            raise ValueError(f"Invalid action type: {action}")

        created = params_set.add(param_name, param)

        if created:
            logger.info(
                "Parameter registered: %s (%s)",
                param_name,
                action,
            )

        return created

    def get_params(
        self,
        action: str,
        param_name: Optional[str] = None,
    ) -> Optional[FraguaClass]:
        """
        Retrieve a parameter by action type and optional name.

        If a parameter name is provided, the method returns the matching
        parameter from the specified action registry. If no name is provided,
        the first registered parameter is returned.

        Args:
            action: Action type ("extract", "transform", "load").
            param_name: Optional name of the parameter to retrieve.

        Returns:
            The requested parameter if found, otherwise None.
        """

        params_set = self.params.get(action)
        if params_set is None:
            return None

        if param_name is None:
            params = params_set.get_all()
            return next(iter(params.values()), None)

        return params_set.get_one(param_name)

    def update_params(
        self,
        action: str,
        old_name: str,
        new_name: str,
    ) -> bool:
        """
        Rename an existing parameter within a specific action.

        Args:
            action: Action type ("extract", "transform", "load").
            old_name: Current parameter name.
            new_name: New parameter name.

        Returns:
            True if the parameter was successfully renamed.

        Raises:
            ValueError: If the action is invalid or the parameter is not found.
        """

        params_set = self.params.get(action)
        if params_set is None:
            raise ValueError(f"Invalid action type: {action}")

        updated = params_set.update(old_name, new_name)

        if not updated:
            raise ValueError("Parameter not found.")

        logger.info(
            "Parameter renamed: %s -> %s (%s)",
            old_name,
            new_name,
            action,
        )

        return updated

    def delete_params(self, action: str, param_name: str) -> bool:
        """
        Delete a parameter from a specific action registry.

        Args:
            action: Action type ("extract", "transform", "load").
            param_name: Name of the parameter to delete.

        Returns:
            True if the parameter was successfully deleted.

        Raises:
            ValueError: If the action is invalid or the parameter is not found.
        """

        params_set = self.params.get(action)
        if params_set is None:
            raise ValueError(f"Invalid action type: {action}")

        deleted = params_set.delete_one(param_name)

        if not deleted:
            raise ValueError("Parameter not found.")

        logger.info(
            "Parameter deleted: %s (%s)",
            param_name,
            action,
        )

        return deleted

    # ----------------------Shortcut functions ---------------------- #
    def get_extractor(self, agent_name: Optional[str] = None) -> Extractor:
        """
        Retrieve an Extractor agent by name.

        If an agent name is provided, the method returns the matching Extractor
        from the extract registry. If no name is provided, the first registered
        Extractor is returned.

        Args:
            agent_name: Optional name of the Extractor agent to retrieve.

        Returns:
            The requested Extractor agent.

        Raises:
            ValueError: If no Extractor agent is found.
        """
        extractor = self.get_agent("extract", agent_name)

        if extractor is None:
            self.agent_not_found()

        return cast(Extractor, extractor)

    def get_transformer(self, agent_name: str | None = None) -> Transformer:
        """
        Retrieve a Transformer agent by name.

        If an agent name is provided, the method returns the matching Transformer
        from the transform registry. If no name is provided, the first registered
        Transformer is returned.

        Args:
            agent_name: Optional name of the Transformer agent to retrieve.

        Returns:
            The requested Transformer agent.

        Raises:
            ValueError: If no Transformer agent is found.
        """
        transformer = self.get_agent("transform", agent_name)

        if transformer is None:
            self.agent_not_found()

        return cast(Transformer, transformer)

    def get_loader(self, agent_name: str | None = None) -> Loader:
        """
        Retrieve a Loader agent by name.

        If an agent name is provided, the method returns the matching Loader
        from the load registry. If no name is provided, the first registered
        Loader is returned.

        Args:
            agent_name: Optional name of the Loader agent to retrieve.

        Returns:
            The requested Loader agent.

        Raises:
            ValueError: If no Loader agent is found.
        """

        loader = self.get_agent("load", agent_name)

        if loader is None:
            self.agent_not_found()

        return cast(Loader, loader)

    # ---------------------- Summary ---------------------- #

    def summary(self) -> Dict[str, Any]:
        """
        Return a structured summary of the Environment instance.

        This summary aggregates high-level metadata and detailed
        information from all core environment components, including:

        - Environment identity (name and type)
        - Warehouse state and configuration
        - Warehouse manager summary
        - Action registries (extract, transform, load), each including
        their respective agents, parameters, functions, and styles

        Returns:
            Dict([str, Any]):
                A hierarchical dictionary representing the complete
                environment configuration and registered components.
        """

        return {
            "env_name": self.name,
            "env_type": self.env_type,
            "warehouse": self.warehouse.summary(),
            "manager": self.manager.summary(),
            "actions": self.actions.summary(),
        }

    def __repr__(self) -> str:
        return f"<Environment name={self.name!r} type={self.env_type!r}>"
