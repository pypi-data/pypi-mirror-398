from re import T
from service_forge.workflow.node import Node
from service_forge.workflow.port import Port
from model.db.tag_base import TagBase
from model.http.query_tags_model import QueryTagsModel
from sqlalchemy import select, or_, func
from pydantic import BaseModel

class HttpQueryTagsItem(BaseModel):
    id: str
    name: str
    type: str
    description: str
    example: str

class HttpQueryTagsResult(BaseModel):
    items: list[HttpQueryTagsItem]
    page: int
    page_size: int
    total: int

class HttpQueryTagsNode(Node):
    DEFAULT_INPUT_PORTS = [
        Port("user_id", int),
        Port("query", QueryTagsModel)
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("tags", HttpQueryTagsResult)
    ]

    def __init__(self, name: str):
        super().__init__(name)

    async def _run(self, query: QueryTagsModel, user_id: int) -> None:
        self.global_context.variables["test"] = self.global_context.variables.get("test", 0) + 1
        if query.ids:
            tag_ids = query.ids.split(",")
            # search tags in database
            session_factory = await self.default_postgres_database.get_session_factory()
            async with session_factory() as session:
                select_query = select(TagBase).where(TagBase.id.in_(tag_ids), or_(TagBase.user_id == user_id, TagBase.type == "DEFAULT")) \
                                .order_by(getattr(TagBase, query.sort_by).desc() if query.order == "desc" else getattr(TagBase, query.sort_by).asc())
                result = await session.execute(select_query)
                tags = result.scalars().all()
            result = {
                "items": tags,
                "page": query.page,
                "page_size": query.page_size,
                "total": len(tags)
            }
            self.activate_output_edges(self.get_output_port_by_name('tags'), result)
        else:
            session_factory = await self.default_postgres_database.get_session_factory()
            async with session_factory() as session:
                select_query = select(TagBase).where(or_(TagBase.user_id == user_id, TagBase.type == "DEFAULT")) \
                                .order_by(getattr(TagBase, query.sort_by).desc() if query.order == "desc" else getattr(TagBase, query.sort_by).asc())
                total_query = select(func.count(TagBase.id))
                result = await session.execute(select_query.offset((query.page - 1) * query.page_size).limit(query.page_size))
                tags = result.scalars().all()
                total_result = await session.execute(total_query)
                total = total_result.scalar_one() or 0

            result = {
                "items": tags,
                "page": query.page,
                "page_size": query.page_size,
                "total": total
            }

            self.activate_output_edges(self.get_output_port_by_name('tags'), HttpQueryTagsResult(
                items=[HttpQueryTagsItem(
                    id=str(tag.id),
                    name=str(tag.name),
                    type=str(tag.type),
                    description=str(tag.description),
                    example=str(tag.example)
                ) for tag in tags],
                page=query.page,
                page_size=query.page_size,
                total=total
            ))