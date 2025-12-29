
from pydantic import BaseModel

class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    message: str = None
    client_id: str

class WebSocketResponse(BaseModel):
    """WebSocket响应模型"""
    status: str
    message: str
    data: dict = None
