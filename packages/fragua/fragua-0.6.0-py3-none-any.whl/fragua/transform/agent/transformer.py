"""Transformer Class."""

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


class Transformer(FraguaAgent):
    """
    Agent responsible for applying transformation styles to stored data.

    The Transformer retrieves data from the warehouse, applies the
    selected transformation style using the resolved parameters,
    and optionally stores the transformed result back into the warehouse.
    """

    def __init__(self, name: str, environment: FraguaEnvironment):
        """
        Initialize a Transformer agent.

        Args:
            name (str): Name of the transformer agent.
            environment (Environment): Execution environment instance.
        """
        super().__init__(agent_name=name, environment=environment)
        self.role = "transformer"
        self.action = "transform"
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
