
from __future__ import annotations
import asyncio
import uuid
import json
from typing import Any
from ...node import Node
from ...port import Port
from ....api.routers.websocket.websocket_manager import websocket_manager

# It's deprecated, just for testing
class TimeConsumingNode(Node):
    """模拟耗时节点，定期发送进度更新"""

    DEFAULT_INPUT_PORTS = [
        Port("input", Any)
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("output", Any)
    ]

    def __init__(self, name: str, duration: float = 2.0):
        super().__init__(name)
        self.duration = duration  # 总耗时（秒）
        self.progress = 0.0
        self.task_id = None

    async def _run(self, input: Any = None, task_id: uuid.UUID = None) -> str:
        """执行耗时任务，定期更新进度"""
        # 保存任务ID（如果有）
        if task_id is not None:
            self.task_id = task_id

        total_steps = 10
        result = f"Completed {self.name} after {self.duration} seconds"

        # 分步骤执行，每步更新进度
        for i in range(total_steps + 1):
            # 更新进度
            self.progress = i / total_steps

            # 发送进度更新
            if self.task_id:
                await websocket_manager.send_progress(
                    self.task_id, 
                    self.name, 
                    self.progress
                )

            # 模拟耗时
            if i < total_steps:  # 最后一步不需要等待
                await asyncio.sleep(self.duration / total_steps)

        # 获取输出端口并设置值
        output_port = self.get_output_port_by_name('output')
        output_port.prepare(result)

        # 激活输出端口
        self.activate_output_edges(output_port, result)

        return result
