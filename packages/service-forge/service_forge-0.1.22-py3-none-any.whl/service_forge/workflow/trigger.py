from __future__ import annotations
import asyncio
from typing import AsyncIterator
from abc import ABC, abstractmethod
import uuid
from .node import Node
from .workflow_event import WorkflowResult

class Trigger(Node, ABC):
    def __init__(self, name: str):
        super().__init__(name)
        self.trigger_queue = asyncio.Queue()
        # for workflow result
        self.result_queues: dict[uuid.UUID, asyncio.Queue[WorkflowResult]] = {}
        # for node stream output
        self.stream_queues: dict[uuid.UUID, asyncio.Queue[WorkflowResult]] = {}

    @abstractmethod
    async def _run(self) -> AsyncIterator[bool]:
        ...

    @abstractmethod
    async def _stop(self) -> AsyncIterator[bool]:
        ...

    def trigger(self, task_id: uuid.UUID) -> bool:
        self.prepare_output_edges(self.get_output_port_by_name('trigger'), True)
        return task_id
