
from __future__ import annotations
import asyncio
import uuid
import datetime
from typing import Dict, List, Set, Any, Optional

class TaskManager:
    """任务管理器，用于跟踪任务状态和队列信息"""

    def __init__(self):
        # 存储所有任务信息: {task_id: task_info}
        self.tasks: Dict[uuid.UUID, Dict[str, Any]] = {}
        # 任务队列，按添加顺序排列
        self.task_queue: List[uuid.UUID] = []
        # 正在执行的任务ID集合
        self.running_tasks: Set[uuid.UUID] = set()
        # 已完成的任务ID集合
        self.completed_tasks: Set[uuid.UUID] = set()
        # 客户端与任务的映射: {client_id: set(task_id)}
        self.client_tasks: Dict[str, Set[uuid.UUID]] = {}

    def add_task(self, task_id: uuid.UUID, client_id: str, workflow_name: str, steps: int) -> Dict[str, Any]:
        """添加新任务到队列"""
        current_time = asyncio.get_event_loop().time()
        task_info = {
            "task_id": task_id,
            "client_id": client_id,
            "workflow_name": workflow_name,
            "steps": steps,
            "current_step": 0,  # 当前步骤，从0开始
            "status": "pending",  # pending, running, completed, failed
            "created_at": datetime.datetime.fromtimestamp(current_time).isoformat(),
            "queue_position": len(self.task_queue) + 1
        }
        self.tasks[task_id] = task_info
        self.task_queue.append(task_id)

        # 更新客户端任务映射
        if client_id not in self.client_tasks:
            self.client_tasks[client_id] = set()
        self.client_tasks[client_id].add(task_id)

        return task_info

    def start_task(self, task_id: uuid.UUID) -> bool:
        """标记任务开始执行"""
        if task_id not in self.tasks:
            return False

        current_time = asyncio.get_event_loop().time()
        self.tasks[task_id]["status"] = "running"
        self.tasks[task_id]["started_at"] = datetime.datetime.fromtimestamp(current_time).isoformat()
        self.tasks[task_id]["current_step"] = 1  # 开始执行第一步
        self.running_tasks.add(task_id)

        # 从队列中移除
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)

        # 更新队列中所有任务的位置
        for i, q_task_id in enumerate(self.task_queue):
            self.tasks[q_task_id]["queue_position"] = i + 1

        return True

    def complete_task(self, task_id: uuid.UUID) -> bool:
        """标记任务完成"""
        if task_id not in self.tasks:
            return False

        current_time = asyncio.get_event_loop().time()
        self.tasks[task_id]["status"] = "completed"
        self.tasks[task_id]["completed_at"] = datetime.datetime.fromtimestamp(current_time).isoformat()
        self.tasks[task_id]["current_step"] = self.tasks[task_id]["steps"]  # 完成所有步骤
        self.running_tasks.discard(task_id)
        self.completed_tasks.add(task_id)

        return True

    def fail_task(self, task_id: uuid.UUID, error: str = None) -> bool:
        """标记任务失败"""
        if task_id not in self.tasks:
            return False

        current_time = asyncio.get_event_loop().time()
        self.tasks[task_id]["status"] = "failed"
        self.tasks[task_id]["failed_at"] = datetime.datetime.fromtimestamp(current_time).isoformat()
        if error:
            self.tasks[task_id]["error"] = error
        self.running_tasks.discard(task_id)

        return True

    def get_client_tasks(self, client_id: str) -> List[Dict[str, Any]]:
        """获取客户端的所有任务"""
        if client_id not in self.client_tasks:
            return []

        return [
            self.tasks[task_id] 
            for task_id in self.client_tasks[client_id] 
            if task_id in self.tasks
        ]

    def get_queue_position(self, task_id: uuid.UUID) -> int:
        """获取任务在队列中的位置，从1开始计数，如果不在队列中返回-1"""
        if task_id not in self.tasks:
            return -1

        return self.tasks[task_id].get("queue_position", -1)

    def get_global_queue_info(self) -> Dict[str, int]:
        """获取全局队列信息"""
        return {
            "total": len(self.running_tasks) + len(self.task_queue),
            "waiting": len(self.task_queue),
            "running": len(self.running_tasks),
        }

    def get_task_info(self, task_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """获取特定任务的详细信息"""
        task_info = self.tasks.get(task_id)
        if task_info:
            # 创建任务信息的副本，并将UUID转换为字符串
            task_copy = task_info.copy()
            task_copy["task_id"] = str(task_id)
            return task_copy
        return None
        
    def update_current_step(self, task_id: uuid.UUID, step: int) -> bool:
        """更新当前任务的步骤"""
        if task_id not in self.tasks:
            return False
            
        # 确保步骤在有效范围内
        if step < 0 or step > self.tasks[task_id]["steps"]:
            return False
            
        self.tasks[task_id]["current_step"] = step
        return True
