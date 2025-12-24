"""Fragua environment factory and exports."""

from typing import Dict, Type
from fragua.core.environment import FraguaEnvironment
from fragua.environments.basic import BasicEnvironment
from fragua.environments.minimal import MinimalEnvironment

# Registry of available environment types
ENVIRONMENT_TYPES: Dict[str, Type[FraguaEnvironment]] = {
    "minimal": MinimalEnvironment,
    "basic": BasicEnvironment,
}


def create_fragua(
    env_name: str, env_type: str = "basic", fg_config: bool = False
) -> FraguaEnvironment:
    """
    Create a Fragua environment with a specific configuration.

    Args:
        name (str): Environment name.
        env_type (str): Environment type ("basic", "minimal", ...).
        fg_config (bool): If True set default config to initialize
                        default fragua components(params, functions, styles).

    Returns:
        Environment: Instantiated and configured environment.

    Raises:
        ValueError: If env_type is not a recognized type.
    """
    env_type = env_type.lower()
    if env_type not in ENVIRONMENT_TYPES:
        raise ValueError(
            f"Unknown environment type '{env_type}'. "
            f"Available: {list(ENVIRONMENT_TYPES.keys())}"
        )

    env_class = ENVIRONMENT_TYPES[env_type]
    environment = env_class(env_name, fg_config=fg_config)

    return environment


__all__ = [
    "MinimalEnvironment",
    "BasicEnvironment",
    "create_fragua",
]
