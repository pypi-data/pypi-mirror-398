from __future__ import annotations
from typing import Any
from ...node import Node
from ...port import Port

class SwitchNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("TRIGGER", bool),
        Port("condition", str, is_extended=True),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("result", Any, is_extended=True),
    ]

    def __init__(
        self, 
        name: str,
    ) -> None:
        super().__init__(
            name,
        )

    async def _run(self, condition: list[tuple[int, str]]) -> None:
        for index, cond in condition:
            if eval(cond):
                self.activate_output_edges(self.extended_output_name('result', index), str(index))
                break
