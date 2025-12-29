from __future__ import annotations
from ...node import Node
from ...port import Port

class IfNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("TRIGGER", bool),
        Port("condition", str),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("true", bool),
        Port("false", bool),
    ]

    def __init__(
        self, 
        name: str,
    ) -> None:
        super().__init__(
            name,
        )

    async def _run(self, condition: str) -> None:
        result = eval(condition)
        if result:
            self.activate_output_edges('true', True)
        else:
            self.activate_output_edges('false', False)
