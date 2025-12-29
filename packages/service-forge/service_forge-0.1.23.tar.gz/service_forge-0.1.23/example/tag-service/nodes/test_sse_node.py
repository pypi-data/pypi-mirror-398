import asyncio
from typing import AsyncIterator
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from model.http.test_sse_model import TestSSEModel

class TestSSENode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("message", TestSSEModel)
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("result", str)
    ]

    def __init__(self, name: str):
        super().__init__(name)

    async def _run(self, message: TestSSEModel) -> AsyncIterator[str]:
        for c in message.message:
            yield c
            await asyncio.sleep(0.5)
        self.activate_output_edges('result', "Done!")