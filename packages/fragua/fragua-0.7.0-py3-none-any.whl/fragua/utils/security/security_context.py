"""Internal security context for Fragua components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final
import uuid


@dataclass(frozen=True)
class FraguaToken:
    """
    Internal identity token for Fragua components.

    Tokens are immutable and can only be created by a
    FraguaSecurityContext.
    """

    env_id: str
    component_kind: str
    component_name: str
    token_id: str


class FraguaSecurityContext:
    """
    Central authority for issuing and validating Fragua internal tokens.

    A single instance exists per Environment.
    """

    def __init__(self, env_name: str) -> None:
        self._env_id: Final[str] = f"env::{env_name}"
        self._issued_tokens: set[str] = set()

    def issue_token(
        self,
        *,
        component_kind: str,
        component_name: str,
    ) -> FraguaToken:
        """Issue a new FraguaToken for the given component."""
        token_id = str(uuid.uuid4())

        token = FraguaToken(
            env_id=self._env_id,
            component_kind=component_kind,
            component_name=component_name,
            token_id=token_id,
        )

        self._issued_tokens.add(token_id)
        return token

    def validate(self, token: FraguaToken) -> bool:
        """Validate a FraguaToken issued by this context."""
        return token.env_id == self._env_id and token.token_id in self._issued_tokens
