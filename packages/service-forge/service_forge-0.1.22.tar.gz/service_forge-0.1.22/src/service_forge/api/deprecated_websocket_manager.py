from __future__ import annotations
import asyncio
import uuid
import json
from typing import Dict, List, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from .task_manager import TaskManager

class WebSocketManager:
    def __init__(self):
        # 存储活动连接: {client_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储任务与客户端的映射: {task_id: client_id}
        self.task_client_mapping: Dict[uuid.UUID, str] = {}
        # 存储客户端订阅的任务: {client_id: set(task_id)}
        self.client_task_subscriptions: Dict[str, Set[uuid.UUID]] = {}
        # 存储客户端历史记录，用于重连时恢复订阅: {client_id: last_active_time}
        self.client_history: Dict[str, float] = {}
        # 设置客户端记录过期时间（秒），默认0.5小时
        self.client_history_expiry = 0.5 * 60 * 60
        # 初始化任务管理器
        self.task_manager = TaskManager()
        # 启动定期清理任务
        self._cleanup_task = None
        self._start_cleanup_task()

    async def connect(self, websocket: WebSocket, client_id: str = None) -> str:
        """接受WebSocket连接，可以使用指定客户端ID或生成新ID"""
        await websocket.accept()

        # 如果没有提供客户端ID，则生成一个新的
        if client_id is None:
            client_id = f"client_{uuid.uuid4().hex[:12]}"

        # 如果客户端ID已存在，先断开旧连接
        if client_id in self.active_connections:
            logger.warning(f"客户端 {client_id} 已存在连接，断开旧连接")
            await self.active_connections[client_id].close()

        # 更新连接记录
        self.active_connections[client_id] = websocket
        self.client_history[client_id] = asyncio.get_event_loop().time()
        logger.info(f"客户端 {client_id} 已连接到WebSocket")

        # 确保清理任务已启动
        self._start_cleanup_task()

        # 发送连接确认消息，包含客户端ID和恢复的订阅信息
        connection_message = {
            "type": "connection established",
            "client_id": client_id,
            "timestamp": str(asyncio.get_event_loop().time()),
            "restored_subscriptions": []
        }

        # 如果有历史订阅，恢复它们
        if client_id in self.client_task_subscriptions and self.client_task_subscriptions[client_id]:
            restored_tasks = []
            for task_id in self.client_task_subscriptions[client_id]:
                restored_tasks.append(str(task_id))
                logger.info(f"恢复客户端 {client_id} 对任务 {task_id} 的订阅")

            connection_message["restored_subscriptions"] = restored_tasks

        await self.send_personal_message(json.dumps(connection_message), client_id)
        return client_id

    def disconnect(self, client_id: str):
        """断开WebSocket连接，但保留客户端的订阅信息"""
        if client_id in self.active_connections:
            # 删除连接记录，但保留订阅信息
            del self.active_connections[client_id]
            # 更新客户端的最后活动时间
            self.client_history[client_id] = asyncio.get_event_loop().time()
            logger.info(f"客户端 {client_id} 已断开WebSocket连接，保留订阅信息")

    async def subscribe_to_task(self, client_id: str, task_id: uuid.UUID) -> bool:
        """客户端订阅任务"""
        if client_id not in self.client_task_subscriptions:
            self.client_task_subscriptions[client_id] = set()

        # 添加任务到客户端的订阅列表
        self.client_task_subscriptions[client_id].add(task_id)
        logger.info(f"客户端 {client_id} 已订阅任务 {task_id}")
        return True

    async def unsubscribe_from_task(self, client_id: str, task_id: uuid.UUID) -> bool:
        """客户端取消订阅任务"""
        if client_id not in self.client_task_subscriptions:
            return False

        # 从客户端的订阅列表中移除任务
        if task_id in self.client_task_subscriptions[client_id]:
            self.client_task_subscriptions[client_id].remove(task_id)
            logger.info(f"客户端 {client_id} 已取消订阅任务 {task_id}")
            return True

        return False

    def create_task_with_client(self, task_id: uuid.UUID, client_id: str, workflow_name: str = "Unknown", steps: int = 1) -> bool:
        """创建任务与客户端的映射，并添加到任务管理器"""
        # 建立任务与客户端的映射
        self.task_client_mapping[task_id] = client_id

        # 自动将任务添加到客户端的订阅列表
        if client_id not in self.client_task_subscriptions:
            self.client_task_subscriptions[client_id] = set()
        self.client_task_subscriptions[client_id].add(task_id)
        
        # 添加任务到任务管理器
        self.task_manager.add_task(task_id, client_id, workflow_name, steps)

        logger.info(f"已为任务 {task_id} 与客户端 {client_id} 建立映射")
        return True

    async def send_personal_message(self, message: str, client_id: str):
        """向特定客户端发送消息"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
                return True
            except Exception as e:
                logger.error(f"向客户端 {client_id} 发送消息失败: {e}")
                self.disconnect(client_id)
                return False
        return False

    async def send_to_task_client(self, task_id: uuid.UUID, message: Dict[str, Any]):
        """向任务关联的客户端发送消息"""
        if task_id not in self.task_client_mapping:
            return  # 没有关联的客户端

        client_id = self.task_client_mapping[task_id]
        
        # 确保task_id是字符串，避免JSON序列化问题
        if "task_id" in message and isinstance(message["task_id"], uuid.UUID):
            message["task_id"] = str(message["task_id"])
            
        # 递归处理嵌套字典中的UUID
        def convert_uuids(obj):
            if isinstance(obj, dict):
                return {k: convert_uuids(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_uuids(item) for item in obj]
            elif isinstance(obj, uuid.UUID):
                return str(obj)
            else:
                return obj
                
        message = convert_uuids(message)
        message_str = json.dumps(message)
        await self.send_personal_message(message_str, client_id)

    async def send_task_status(self, task_id: uuid.UUID, status: str, node: str = None, progress: float = None, error: str = None):
        """发送任务状态更新"""
        message = {
            "task_id": str(task_id),
            "type": "status",
            "status": status
        }

        if node is not None:
            message["node"] = node

        if progress is not None:
            message["progress"] = progress

        if error is not None:
            message["error"] = error

        await self.send_to_task_client(task_id, message)

    async def send_execution_start(self, task_id: uuid.UUID):
        """发送任务开始执行消息"""
        # 获取客户端ID
        client_id = self.task_client_mapping.get(task_id)
        
        # 更新任务状态为运行中
        self.task_manager.start_task(task_id)

        # 获取客户端的任务队列信息
        client_tasks = []
        if client_id:
            client_tasks = self.task_manager.get_client_tasks(client_id)

        # 获取全局任务队列信息
        global_queue_info = self.task_manager.get_global_queue_info()
        
        # 获取当前任务在队列中的位置
        queue_position = self.task_manager.get_queue_position(task_id)

        message = {
            "task_id": str(task_id),
            "type": "execution start",
            "client_tasks": {
                "total": len(client_tasks),
                "tasks": client_tasks
            },
            "global_queue": global_queue_info,
            "queue_position": queue_position
        }
        await self.send_to_task_client(task_id, message)

    async def send_executing(self, task_id: uuid.UUID, node: str):
        """发送节点正在执行消息"""
        # 获取客户端ID
        client_id = self.task_client_mapping.get(task_id)

        # 获取客户端的任务队列信息
        client_tasks = []
        if client_id:
            client_tasks = self.task_manager.get_client_tasks(client_id)

        # 获取全局任务队列信息
        global_queue_info = self.task_manager.get_global_queue_info()
        
        # 获取当前任务在队列中的位置
        queue_position = self.task_manager.get_queue_position(task_id)

        message = {
            "task_id": str(task_id),
            "type": "executing",
            "node": node,
            "client_tasks": {
                "total": len(client_tasks),
                "tasks": client_tasks
            },
            "global_queue": global_queue_info,
            "queue_position": queue_position
        }
        await self.send_to_task_client(task_id, message)

    async def send_progress(self, task_id: uuid.UUID, node: str, progress: float):
        """发送节点执行进度消息"""
        # 获取客户端ID
        client_id = self.task_client_mapping.get(task_id)

        # 获取客户端的任务队列信息
        client_tasks = []
        if client_id:
            client_tasks = self.task_manager.get_client_tasks(client_id)

        # 获取全局任务队列信息
        global_queue_info = self.task_manager.get_global_queue_info()
        
        # 获取当前任务在队列中的位置
        queue_position = self.task_manager.get_queue_position(task_id)

        message = {
            "task_id": str(task_id),
            "type": "progress",
            "node": node,
            "progress": progress,
            "client_tasks": {
                "total": len(client_tasks),
                "tasks": client_tasks
            },
            "global_queue": global_queue_info,
            "queue_position": queue_position
        }
        await self.send_to_task_client(task_id, message)

    async def send_executed(self, task_id: uuid.UUID, node: str, result: Any = None):
        """发送节点执行完成消息"""
        # 获取客户端ID
        client_id = self.task_client_mapping.get(task_id)

        # 获取客户端的任务队列信息
        client_tasks = []
        if client_id:
            client_tasks = self.task_manager.get_client_tasks(client_id)

        # 获取全局任务队列信息
        global_queue_info = self.task_manager.get_global_queue_info()
        
        # 获取当前任务在队列中的位置
        queue_position = self.task_manager.get_queue_position(task_id)

        message = {
            "task_id": str(task_id),
            "type": "executed",
            "node": node,
            "client_tasks": {
                "total": len(client_tasks),
                "tasks": client_tasks
            },
            "global_queue": global_queue_info,
            "queue_position": queue_position
        }

        if result is not None:
            # 检查是否为协程对象
            import asyncio
            if asyncio.iscoroutine(result):
                message["result"] = "<coroutine object>"
            else:
                # 尝试序列化结果，如果失败则转换为字符串
                try:
                    message["result"] = result
                except TypeError:
                    message["result"] = str(result)

        await self.send_to_task_client(task_id, message)

    async def send_execution_error(self, task_id: uuid.UUID, node: str, error: str):
        """发送执行错误消息"""
        # 获取客户端ID
        client_id = self.task_client_mapping.get(task_id)
        
        # 更新任务状态为失败
        self.task_manager.fail_task(task_id, error)

        # 获取客户端的任务队列信息
        client_tasks = []
        if client_id:
            client_tasks = self.task_manager.get_client_tasks(client_id)

        # 获取全局任务队列信息
        global_queue_info = self.task_manager.get_global_queue_info()
        
        # 获取当前任务在队列中的位置
        queue_position = self.task_manager.get_queue_position(task_id)

        message = {
            "task_id": str(task_id),
            "type": "execution error",
            "node": node,
            "error": error,
            "client_tasks": {
                "total": len(client_tasks),
                "tasks": client_tasks
            },
            "global_queue": global_queue_info,
            "queue_position": queue_position
        }
        await self.send_to_task_client(task_id, message)

    def _start_cleanup_task(self):
        """启动定期清理任务"""
        # 检查是否有运行的事件循环
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行的事件循环，延迟启动清理任务
            return

        if self._cleanup_task is None:
            self._cleanup_task = loop.create_task(self._cleanup_expired_clients())

    async def _cleanup_expired_clients(self):
        """定期清理过期的客户端记录"""
        while True:
            try:
                # 每小时执行一次清理
                await asyncio.sleep(60 * 60)
                current_time = asyncio.get_event_loop().time()
                expired_clients = []

                # 查找过期的客户端记录
                for client_id, last_active_time in self.client_history.items():
                    # 如果客户端不在活动连接中且超过过期时间，则标记为过期
                    if (client_id not in self.active_connections and 
                        current_time - last_active_time > self.client_history_expiry):
                        expired_clients.append(client_id)

                # 清理过期客户端的订阅记录
                for client_id in expired_clients:
                    # 移除客户端的订阅记录
                    if client_id in self.client_task_subscriptions:
                        del self.client_task_subscriptions[client_id]

                    # 移除客户端的历史记录
                    del self.client_history[client_id]

                    # 清理任务映射中的过期记录
                    tasks_to_remove = []
                    for task_id, mapped_client_id in self.task_client_mapping.items():
                        if mapped_client_id == client_id:
                            tasks_to_remove.append(task_id)

                    for task_id in tasks_to_remove:
                        del self.task_client_mapping[task_id]

                    logger.info(f"已清理过期客户端 {client_id} 的所有记录")

                if expired_clients:
                    logger.info(f"清理了 {len(expired_clients)} 个过期客户端记录")

            except Exception as e:
                logger.error(f"清理过期客户端时出错: {e}")
                # 出错后继续尝试清理，不中断任务

    def set_client_history_expiry(self, seconds: int):
        """设置客户端记录过期时间"""
        self.client_history_expiry = seconds
        logger.info(f"客户端记录过期时间已设置为 {seconds} 秒")

    async def send_node_output(self, task_id: uuid.UUID, node: str, port: str, value: Any):
        """发送节点输出结果消息"""
        message = {
            "task_id": str(task_id),
            "type": "node output",
            "node": node,
            "port": port
        }

        # 尝试将值序列化为JSON
        try:
            import json
            # 如果值是基本类型，直接使用
            if isinstance(value, (str, int, float, bool)) or value is None:
                message["value"] = value
            else:
                # 尝试JSON序列化复杂对象
                json.dumps(value)  # 测试是否可以序列化
                message["value"] = value
        except (TypeError, ValueError, json.JSONDecodeError):
            # 如果序列化失败，转换为字符串
            message["value"] = str(value)

        await self.send_to_task_client(task_id, message)

# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()
