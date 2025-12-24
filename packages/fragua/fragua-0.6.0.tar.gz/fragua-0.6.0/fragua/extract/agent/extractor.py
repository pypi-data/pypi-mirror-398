"""Miner Class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pandas import DataFrame
from fragua.core.agent import FraguaAgent
from fragua.core.params import FraguaParams
from fragua.utils.logger import get_logger

if TYPE_CHECKING:
    from fragua.core.environment import FraguaEnvironment


logger = get_logger(__name__)


# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments


class Extractor(FraguaAgent):
    """
    Agent responsible for executing extraction workflows in Fragua.

    The Extractor applies extraction styles to external data sources
    (files, databases, APIs, etc.) and produces Box storage objects
    containing raw extracted data.

    This agent does not perform transformations or loading operations;
    its sole responsibility is data acquisition.
    """

    def __init__(self, name: str, environment: FraguaEnvironment):
        """
        Initialize the Extractor agent.

        Args:
            name: Logical name of the agent.
            environment: Active Fragua environment instance.
        """
        super().__init__(agent_name=name, environment=environment)
        self.role = "extractor"
        self.action = "extract"
        self.storage_type = "Box"

    def work(
        self,
        style: str,
        apply_to: str | list[str] | None = None,
        save_as: str | None = None,
        params: FraguaParams | None = None,
        input_data: DataFrame | None = None,
        **kwargs: Any,
    ) -> None:
        return super().work(style, apply_to, save_as, params, input_data, **kwargs)
