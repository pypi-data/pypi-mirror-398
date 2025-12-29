from __future__ import annotations
import os

from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from service_forge.llm import chat_stream, Model

class QueryLLMNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("prompt", str),
        Port("system_prompt", str),
        Port("temperature", float),
        Port("TRIGGER", bool),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("response", str),
    ]

    AUTO_FILL_INPUT_PORTS = [('TRIGGER', True)]

    def __init__(
        self, 
        name: str,
    ) -> None:
        super().__init__(
            name,
        )

    async def _run(self, prompt: str, system_prompt: str, temperature: float) -> None:
        if os.path.exists(system_prompt):
            with open(system_prompt, "r") as f:
                system_prompt = f.read()
        if os.path.exists(prompt):
            with open(prompt, "r") as f:
                prompt = f.read()

        print(f"prompt: {prompt} temperature: {temperature}")
        response = chat_stream(prompt, system_prompt, Model.GEMINI, temperature)
        for chunk in response:
            yield chunk