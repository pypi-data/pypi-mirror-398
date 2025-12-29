from pydantic import BaseModel

class TestSSEModel(BaseModel):
    message: str