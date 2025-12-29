from __future__ import annotations

import json
from abc import abstractmethod
from typing import TYPE_CHECKING, Any
from typing_extensions import override
from enum import Enum
from .workflow_event import WorkflowResult
from loguru import logger

if TYPE_CHECKING:
    from .node import Node
    from .workflow import Workflow

class CallbackEvent(Enum):
    ON_WORKFLOW_START = "on_workflow_start"
    ON_WORKFLOW_END = "on_workflow_end"
    ON_WORKFLOW_ERROR = "on_workflow_error"
    ON_NODE_START = "on_node_start"
    ON_NODE_END = "on_node_end"
    ON_NODE_OUTPUT = "on_node_output"
    ON_NODE_STREAM_OUTPUT = "on_node_stream_output"

class WorkflowCallback:
    @abstractmethod
    async def on_workflow_start(self, workflow: Workflow) -> None:
        ...

    @abstractmethod
    async def on_workflow_end(self, workflow: Workflow, output: Any) -> None:
        pass

    @abstractmethod
    async def on_workflow_error(self, workflow: Workflow, error: Any) -> None:
        pass

    @abstractmethod
    async def on_node_start(self, node: Node) -> None:
        ...

    @abstractmethod
    async def on_node_end(self, node: Node) -> None:
        ...

    @abstractmethod
    async def on_node_stream_output(self, node: Node, output: Any) -> None:
        ...

class BuiltinWorkflowCallback(WorkflowCallback):
    def __init__(self):
        self._websocket_manager = None
    
    def _get_websocket_manager(self):
        if self._websocket_manager is None:
            from service_forge.api.routers.websocket.websocket_manager import websocket_manager
            self._websocket_manager = websocket_manager
        return self._websocket_manager
    
    def _serialize_result(self, result: Any) -> Any:
        try:
            json.dumps(result)
            return result
        except (TypeError, ValueError):
            return str(result)
    
    @override
    async def on_workflow_start(self, workflow: Workflow) -> None:
        ...

    @override
    async def on_workflow_end(self, workflow: Workflow, output: Any) -> None:
        workflow_result = WorkflowResult(result=output, is_end=True, is_error=False)
        
        if workflow.task_id in workflow.real_trigger_node.result_queues:
            workflow.real_trigger_node.result_queues[workflow.task_id].put_nowait(workflow_result)
        if workflow.task_id in workflow.real_trigger_node.stream_queues:
            workflow.real_trigger_node.stream_queues[workflow.task_id].put_nowait(workflow_result)
        
        try:
            manager = self._get_websocket_manager()
            message = {
                "type": "workflow_end",
                "task_id": str(workflow.task_id),
                "result": self._serialize_result(output),
                "is_end": True,
                "is_error": False
            }
            await manager.send_to_task(workflow.task_id, message)
        except Exception as e:
            logger.error(f"发送 workflow_end 消息到 websocket 失败: {e}")

    @override
    async def on_workflow_error(self, workflow: Workflow, error: Any) -> None:
        workflow_result = WorkflowResult(result=error, is_end=False, is_error=True)
        
        if workflow.task_id in workflow.real_trigger_node.result_queues:
            workflow.real_trigger_node.result_queues[workflow.task_id].put_nowait(workflow_result)
        if workflow.task_id in workflow.real_trigger_node.stream_queues:
            workflow.real_trigger_node.stream_queues[workflow.task_id].put_nowait(workflow_result)
        
        try:
            manager = self._get_websocket_manager()
            message = {
                "type": "workflow_error",
                "task_id": str(workflow.task_id),
                "error": self._serialize_result(error),
                "is_end": False,
                "is_error": True
            }
            await manager.send_to_task(workflow.task_id, message)
        except Exception as e:
            logger.error(f"发送 workflow_error 消息到 websocket 失败: {e}")

    @override
    async def on_node_start(self, node: Node) -> None:
        ...

    @override
    async def on_node_end(self, node: Node) -> None:
        ...

    @override
    async def on_node_stream_output(self, node: Node, output: Any) -> None:
        workflow_result = WorkflowResult(result=output, is_end=False, is_error=False)
        
        if node.workflow.task_id in node.workflow.real_trigger_node.stream_queues:
            node.workflow.real_trigger_node.stream_queues[node.workflow.task_id].put_nowait(workflow_result)
        
        try:
            manager = self._get_websocket_manager()
            message = {
                "type": "node_stream_output",
                "task_id": str(node.workflow.task_id),
                "node": node.name,
                "output": self._serialize_result(output),
                "is_end": False,
                "is_error": False
            }
            await manager.send_to_task(node.workflow.task_id, message)
        except Exception as e:
            logger.error(f"发送 node_stream_output 消息到 websocket 失败: {e}")