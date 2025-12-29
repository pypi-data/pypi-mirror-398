from __future__ import annotations
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from service_forge.api.kafka_api import KafkaApp
from typing import Any

class KafkaOutputNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("app", KafkaApp),
        Port("topic", str),
        Port("data_type", type),
        Port("data", Any),
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

    async def _run(self, app: KafkaApp, topic: str, data_type: type, data: Any) -> None:
        await app.send_message(topic, data_type, data)