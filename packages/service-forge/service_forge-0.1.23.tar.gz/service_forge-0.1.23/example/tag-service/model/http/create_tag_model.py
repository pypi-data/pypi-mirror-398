from pydantic import BaseModel

class CreateTagModel(BaseModel):
    name: str
    description: str
    example: str