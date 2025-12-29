from pydantic import BaseModel

class UpdateTagModel(BaseModel):
    id: str
    name: str
    description: str
    example: str