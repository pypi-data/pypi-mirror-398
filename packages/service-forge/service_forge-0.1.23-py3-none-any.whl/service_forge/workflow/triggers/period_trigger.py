from __future__ import annotations
import asyncio
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from service_forge.workflow.trigger import Trigger
from typing import AsyncIterator
import uuid

class PeriodTrigger(Trigger):
    DEFAULT_INPUT_PORTS = [
        Port("TRIGGER", bool),
        Port("period", float),
        Port("times", int),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("trigger", bool),
    ]

    def __init__(self, name: str):
        super().__init__(name)

    async def _run(self, times: int, period: float) -> AsyncIterator[bool]:
        for _ in range(times):
            await asyncio.sleep(period)
            yield uuid.uuid4()

    async def _stop(self) -> AsyncIterator[bool]:
        pass