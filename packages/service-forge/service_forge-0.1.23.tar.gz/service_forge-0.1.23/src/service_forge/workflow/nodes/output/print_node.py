from __future__ import annotations
import asyncio
from typing import AsyncIterator
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port

class PrintNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("TRIGGER", bool),
        Port("message", str),
    ]

    DEFAULT_OUTPUT_PORTS = [
    ]

    AUTO_FILL_INPUT_PORTS = [('TRIGGER', True)]

    def __init__(
        self, 
        name: str,
    ) -> None:
        super().__init__(
            name,
        )

    async def _run(self, message: str) -> AsyncIterator[str]:
        for char in str(message):
            await asyncio.sleep(0.1)
            yield char
