from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from model.http.create_tag_model import CreateTagModel
from model.db.tag_base import TagBase

class HttpCreateTagNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("user_id", int),
        Port("tag", CreateTagModel)
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("tag", TagBase)
    ]

    def __init__(self, name: str):
        super().__init__(name)
    
    async def _run(self, tag: CreateTagModel, user_id: int) -> None:
        session_factory = await self.default_postgres_database.get_session_factory()
        async with session_factory() as session:
            tag = TagBase(
                name=tag.name,
                description=tag.description,
                example=tag.example,
                user_id=user_id,
                type="CUSTOM",
            )
            session.add(tag)
            await session.commit()
        self.activate_output_edges(self.get_output_port_by_name('tag'), tag)