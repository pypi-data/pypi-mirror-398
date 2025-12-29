from __future__ import annotations
from typing import Any

class Context():
    def __init__(
        self,
        variables: dict[Any, Any] = dict(),
    ) -> None:
        self.variables = variables

    def _clone(self) -> Context:
        return Context(
            variables={key: value for key, value in self.variables.items()},
        )