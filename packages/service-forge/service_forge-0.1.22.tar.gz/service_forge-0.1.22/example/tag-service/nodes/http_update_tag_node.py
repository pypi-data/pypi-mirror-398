from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from model.http.update_tag_model import UpdateTagModel
from model.db.tag_base import TagBase
from sqlalchemy import select
from fastapi import HTTPException

class HttpUpdateTagNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("user_id", int),
        Port("tag", UpdateTagModel)
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("tag", TagBase)
    ]

    def __init__(self, name: str):
        super().__init__(name)

    async def _run(self, tag: UpdateTagModel, user_id: int) -> None:
        session_factory = await self.default_postgres_database.get_session_factory()
        async with session_factory() as session:
            try:
                result = await session.execute(
                    select(TagBase).where(TagBase.id == tag.id, TagBase.user_id == user_id)
                )
                db_tag = result.scalar_one_or_none()
                if db_tag is None:
                    self.activate_output_edges(self.get_output_port_by_name('tag'), HTTPException(status_code=404, detail="Tag not found"))
                    return
                for key, value in tag.model_dump().items():
                    setattr(db_tag, key, value)
                await session.commit()
            except Exception as e:
                self.activate_output_edges(self.get_output_port_by_name('tag'), HTTPException(status_code=500, detail="Tag not found"))
                return

        self.activate_output_edges(self.get_output_port_by_name('tag'), db_tag)