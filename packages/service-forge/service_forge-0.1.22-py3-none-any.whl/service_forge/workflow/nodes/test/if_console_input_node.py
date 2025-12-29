from __future__ import annotations
from typing import AsyncIterator
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port

class IfConsoleInputNode(Node):
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
        while True:
            user_input = await self._query_user(condition)
            if user_input.lower() in ['y', 'yes']:
                self.activate_output_edges(self.get_output_port_by_name('true'), True)
                break
            elif user_input.lower() in ['n', 'no']:
                self.activate_output_edges(self.get_output_port_by_name('false'), False)
                break
