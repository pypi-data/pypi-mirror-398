import asyncio
from typing import AsyncIterator
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from model.http.test_sse_model import TestSSEModel

class TestContextNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("message", TestSSEModel)
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("result", TestSSEModel)
    ]

    def __init__(self, name: str):
        super().__init__(name)

    async def _run(self, message: TestSSEModel) -> AsyncIterator[str]:
        if self.context.variables.get('count') is None:
            self.context.variables['count'] = 0
        self.context.variables['count'] += 1
        print(f"TestContextNode {self.name} count: {self.context.variables['count']}")
        self.activate_output_edges('result', message)