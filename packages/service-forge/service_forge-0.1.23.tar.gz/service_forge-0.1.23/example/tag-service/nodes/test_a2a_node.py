import asyncio
from typing import AsyncIterator
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from model.http.test_sse_model import TestSSEModel
from a2a.server.agent_execution.context import RequestContext

class TestA2ANode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("context", RequestContext)
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("result", str)
    ]

    def __init__(self, name: str):
        super().__init__(name)

    async def _run(self, context: RequestContext) -> AsyncIterator[str]:
        for c in "Hello, world!":
            await self.stream_output(c)
            await asyncio.sleep(0.05)
        self.activate_output_edges('result', "Done!")