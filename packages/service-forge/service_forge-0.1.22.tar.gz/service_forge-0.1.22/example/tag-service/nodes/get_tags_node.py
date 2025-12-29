import re
import json
from loguru import logger
from sqlalchemy import text

from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from service_forge.llm import chat, Model
from proto.entryService.record_pb2 import Record
from proto.tagService.tag_pb2 import Tag


class GetTagsNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("prompt", str),
        Port("record", Record),
        Port("temperature", float),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("tag", Tag),
    ]

    def __init__(self, name: str):
        super().__init__(name)

    async def get_default_tag(self) -> list[Tag]:
        session_factory = await self.default_postgres_database.get_session_factory()
        async with session_factory() as session:
            result = await session.execute(text("SELECT * FROM tag WHERE type = 'DEFAULT'"))
            return result.fetchall()

    async def get_custom_tag(self, user_id: int) -> list[Tag]:
        session_factory = await self.default_postgres_database.get_session_factory()
        async with session_factory() as session:
            result = await session.execute(text("SELECT * FROM tag WHERE type != 'DEFAULT' AND user_id = :user_id"), {"user_id": user_id})
            return result.fetchall()

    def format_tags_prompt(self, tag: list[Tag]) -> str:
        result = ""
        for tag in tag:
            result += f"[{tag.name}]<ID: {tag.id}>（{tag.description}）examples: {tag.example}\n"
        return result

    def get_json_from_result(self, result: str) -> str | None:
        match = re.search(r"```json\s*(.*?)\s*```", str(result), re.DOTALL)
        if match:
            return match.group(1)
        return None

    async def _run(self, prompt: str, record: Record, temperature: float) -> None:
        logger.info(f"Processing record: {record.text} timestamp: {record.timestamp} file_id: {record.file_id} user_id: {record.user_id}")
        default_tags = await self.get_default_tag()
        custom_tags = await self.get_custom_tag(record.user_id)
        prompt = open(prompt, "r").read()
        prompt = prompt.replace("{%default_tags%}", self.format_tags_prompt(default_tags))
        prompt = prompt.replace("{%custom_tags%}", self.format_tags_prompt(custom_tags))

        logger.info(f"Querying LLM...")
        response = chat(record.text, prompt, Model.DEEPSEEK_V3_250324, temperature)

        tags = []

        try:
            json_str = self.get_json_from_result(response)
            logger.info(f"parsed result: {json_str}")
            if json_str is not None:
                tags = json.loads(json_str)['tags']            
        except Exception as e:
            logger.error(f"Failed to parse tags from result: {e}")

        result = Tag(
            proto_id=record.proto_id,
            record_id=record.id,
            user_id=record.user_id,
            tags=tags
        )

        self.activate_output_edges(self.get_output_port_by_name('tag'), result)
