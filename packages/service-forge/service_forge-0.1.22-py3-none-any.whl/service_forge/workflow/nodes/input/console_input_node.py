from __future__ import annotations
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from service_forge.llm import chat_stream, Model

class ConsoleInputNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("TRIGGER", bool),
        Port("prompt", str),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("user_input", str),
    ]

    AUTO_FILL_INPUT_PORTS = []

    def __init__(
        self, 
        name: str,
    ) -> None:
        super().__init__(name)

    async def _run(self, prompt: str) -> None:
        user_input = self._query_user(prompt)
        self.activate_output_edges(self.get_output_port_by_name('user_input'), user_input)