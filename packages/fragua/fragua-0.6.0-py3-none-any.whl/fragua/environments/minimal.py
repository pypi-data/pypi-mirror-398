"""Minimal Environment Class."""

from __future__ import annotations

from fragua.core.environment import FraguaEnvironment
from fragua.utils.logger import get_logger

logger = get_logger(__name__)


class MinimalEnvironment(FraguaEnvironment):
    """
    A minimal Environment subclass that starts only with a Warehouse and FraguaManager, but
    without Agents. Useful for flexible or custom setups.
    """

    def __init__(self, env_name: str, fg_config: bool = False):
        super().__init__(env_name=env_name, env_type="minimal", fg_config=fg_config)

        logger.debug("Minimal environment '%s' initialized.", self.name)
        logger.info("Minimal environment '%s' is ready for manual setup.", self.name)
