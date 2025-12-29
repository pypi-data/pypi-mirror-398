from pydantic import BaseModel

class FooInput(BaseModel):
    user_id: int
    data: str
