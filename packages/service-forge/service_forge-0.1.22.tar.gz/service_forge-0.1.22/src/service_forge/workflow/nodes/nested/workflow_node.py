from __future__ import annotations

from typing import TYPE_CHECKING
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port

class WorkflowNode(Node):
    from service_forge.workflow.workflow import Workflow
    DEFAULT_INPUT_PORTS = [
        Port("workflow", Workflow),
    ]

    DEFAULT_OUTPUT_PORTS = [
    ]

    def __init__(
        self, 
        name: str,
    ) -> None:
        super().__init__(
            name,
        )

    async def _run(self, workflow: Workflow, **kwargs) -> None:
        for input_port in self.input_ports:
            if input_port.is_sub_workflow_input_port():
                input_port.port.node.fill_input(input_port.port, input_port.value)
        await workflow.run()