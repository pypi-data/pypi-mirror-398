from pydantic import BaseModel

class QueryTagsModel(BaseModel):
    ids: str = ""
    page: int = 1
    page_size: int = 10
    sort_by: str = "created_at"
    order: str = "desc"