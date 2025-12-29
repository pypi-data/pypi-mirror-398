from __future__ import annotations
import uuid
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request, Query
from fastapi.responses import JSONResponse
from loguru import logger
from typing import Dict, Any, Optional
from .websocket_manager import websocket_manager

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = Query(None)):
    """WebSocket连接端点，支持指定客户端ID"""
    client_id = await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_client_message(client_id, message)
            except json.JSONDecodeError:
                logger.error(f"从客户端 {client_id} 收到无效JSON消息: {data}")
                await websocket_manager.send_personal_message(
                    json.dumps({"error": "Invalid JSON format"}),
                    client_id
                )
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket连接处理异常: {e}")
        websocket_manager.disconnect(client_id)

async def handle_client_message(client_id: str, message: Dict[str, Any]):
    """处理来自客户端的消息"""
    message_type = message.get("type")

    if message_type == "subscribe":
        # 客户端订阅任务
        task_id_str = message.get("task_id")
        if not task_id_str:
            await websocket_manager.send_personal_message(
                json.dumps({"error": "Missing task_id in subscribe message"}),
                client_id
            )
            return

        try:
            task_id = uuid.UUID(task_id_str)
            success = await websocket_manager.subscribe_to_task(client_id, task_id)
            response = {"success": success}
            await websocket_manager.send_personal_message(json.dumps(response), client_id)
        except ValueError:
            await websocket_manager.send_personal_message(
                json.dumps({"error": "Invalid task_id format"}),
                client_id
            )

    elif message_type == "unsubscribe":
        # 客户端取消订阅任务
        task_id_str = message.get("task_id")
        if not task_id_str:
            await websocket_manager.send_personal_message(
                json.dumps({"error": "Missing task_id in unsubscribe message"}),
                client_id
            )
            return

        try:
            task_id = uuid.UUID(task_id_str)
            success = await websocket_manager.unsubscribe_from_task(client_id, task_id)
            response = {"success": success}
            await websocket_manager.send_personal_message(json.dumps(response), client_id)
        except ValueError:
            await websocket_manager.send_personal_message(
                json.dumps({"error": "Invalid task_id format"}),
                client_id
            )

    else:
        await websocket_manager.send_personal_message(
            json.dumps({"error": f"Unknown message type: {message_type}"}),
            client_id
        )
