from __future__ import annotations
import uuid
from typing import Any
from service_forge.workflow.trigger import Trigger
from typing import AsyncIterator
from service_forge.workflow.port import Port
from service_forge.api.kafka_api import KafkaApp

class KafkaAPITrigger(Trigger):
    DEFAULT_INPUT_PORTS = [
        Port("app", KafkaApp),
        Port("topic", str),
        Port("data_type", type),
        Port("group_id", str),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("trigger", bool),
        Port("data", Any),
    ]
    
    def __init__(self, name: str):
        super().__init__(name)
        self.events = {}
        self.is_setup_kafka_input = False

    def _setup_kafka_input(self, app: KafkaApp, topic: str, data_type: type, group_id: str) -> None:
        @app.kafka_input(topic, data_type, group_id)
        async def handle_message(data):
            task_id = uuid.uuid4()
            self.trigger_queue.put_nowait({
                "id": task_id,
                "data": data,
            })

    async def _run(self, app: KafkaApp, topic: str, data_type: type, group_id: str) -> AsyncIterator[bool]:
        if not self.is_setup_kafka_input:
            self._setup_kafka_input(app, topic, data_type, group_id)
            self.is_setup_kafka_input = True

        while True:
            trigger = await self.trigger_queue.get()
            self.prepare_output_edges(self.get_output_port_by_name('data'), trigger['data'])
            yield self.trigger(trigger['id'])

    async def _stop(self) -> AsyncIterator[bool]:
        pass