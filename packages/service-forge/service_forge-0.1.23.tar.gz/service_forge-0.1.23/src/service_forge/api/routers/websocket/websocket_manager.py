from fastapi import WebSocket
from typing import Dict, Set
import uuid
import json
import asyncio
from loguru import logger

class WebSocketManager:
    def __init__(self):
        self.task_connections: Dict[uuid.UUID, Set[WebSocket]] = {}
        self.websocket_tasks: Dict[WebSocket, Set[uuid.UUID]] = {}
        self.all_task_subscribers: Set[WebSocket] = set()
        self.websocket_subscribes_all: Dict[WebSocket, bool] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, websocket: WebSocket, task_id: uuid.UUID | None) -> bool:
        async with self._lock:
            if task_id is None:
                self.all_task_subscribers.add(websocket)
                self.websocket_subscribes_all[websocket] = True
            else:
                if task_id not in self.task_connections:
                    self.task_connections[task_id] = set()
                self.task_connections[task_id].add(websocket)
                
                if websocket not in self.websocket_tasks:
                    self.websocket_tasks[websocket] = set()
                self.websocket_tasks[websocket].add(task_id)
            return True
    
    async def unsubscribe(self, websocket: WebSocket, task_id: uuid.UUID | None) -> bool:
        async with self._lock:
            if task_id is None:
                self.all_task_subscribers.discard(websocket)
                self.websocket_subscribes_all.pop(websocket, None)
            else:
                if task_id in self.task_connections:
                    self.task_connections[task_id].discard(websocket)
                    if not self.task_connections[task_id]:
                        del self.task_connections[task_id]
                
                if websocket in self.websocket_tasks:
                    self.websocket_tasks[websocket].discard(task_id)
                    if not self.websocket_tasks[websocket]:
                        del self.websocket_tasks[websocket]
            return True
    
    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.websocket_tasks:
                task_ids = self.websocket_tasks[websocket].copy()
                for task_id in task_ids:
                    if task_id in self.task_connections:
                        self.task_connections[task_id].discard(websocket)
                        if not self.task_connections[task_id]:
                            del self.task_connections[task_id]
                del self.websocket_tasks[websocket]
            
            self.all_task_subscribers.discard(websocket)
            self.websocket_subscribes_all.pop(websocket, None)
    
    async def send_to_task(self, task_id: uuid.UUID, message: dict):
        async with self._lock:
            specific_subscribers = list(self.task_connections.get(task_id, set()))
            all_subscribers = list(self.all_task_subscribers)
            websockets = list(set(specific_subscribers + all_subscribers))
        
        disconnected = set()
        message_str = json.dumps(message)
        
        # logger.debug(f"向 {len(websockets)} 个 websocket 连接发送消息 (task_id: {task_id})")
        
        for websocket in websockets:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"向 task_id {task_id} 的 websocket 发送消息失败: {e}")
                disconnected.add(websocket)
        
        for ws in disconnected:
            await self.disconnect(ws)

websocket_manager = WebSocketManager()
