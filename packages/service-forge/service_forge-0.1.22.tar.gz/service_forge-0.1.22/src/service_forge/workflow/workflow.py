from __future__ import annotations
import traceback
import asyncio
import uuid
from typing import AsyncIterator, Awaitable, Callable, Any
from loguru import logger
from copy import deepcopy
from .node import Node
from .port import Port
from .trigger import Trigger
from .edge import Edge
from ..db.database import DatabaseManager
from ..utils.workflow_clone import workflow_clone
from .workflow_callback import WorkflowCallback, BuiltinWorkflowCallback, CallbackEvent
from .workflow_config import WorkflowConfig
from .context import Context

class Workflow:
    def __init__(
        self,
        id: uuid.UUID,
        config: WorkflowConfig,
        nodes: list[Node],
        input_ports: list[Port],
        output_ports: list[Port],
        _handle_stream_output: Callable[[str, AsyncIterator[str]], Awaitable[None]] = None, # deprecated
        _handle_query_user: Callable[[str, str], Awaitable[str]] = None,
        database_manager: DatabaseManager = None,
        max_concurrent_runs: int = 10,
        callbacks: list[WorkflowCallback] = [],

        # for run
        task_id: uuid.UUID = None,
        real_trigger_node: Trigger = None,

        # global variables
        global_context: Context = None,
    ) -> None:
        self.id = id
        self.config = config
        self.nodes = nodes
        self.ready_nodes: list[Node] = []
        self.input_ports = input_ports
        self.output_ports = output_ports
        self._handle_stream_output = _handle_stream_output
        self._handle_query_user = _handle_query_user
        self.after_trigger_workflow = None
        self.result_port = Port("result", Any)
        self.database_manager = database_manager
        self.max_concurrent_runs = max_concurrent_runs
        self.run_semaphore = asyncio.Semaphore(max_concurrent_runs)
        self.callbacks = callbacks
        self.task_id = task_id
        self.real_trigger_node = real_trigger_node
        self.global_context = global_context
        self._validate()
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def version(self) -> str:
        return self.config.version
    
    @property
    def description(self) -> str:
        return self.config.description

    def register_callback(self, callback: WorkflowCallback) -> None:
        self.callbacks.append(callback)

    def unregister_callback(self, callback: WorkflowCallback) -> None:
        self.callbacks.remove(callback)

    async def call_callbacks(self, callback_type: CallbackEvent, *args, **kwargs) -> None:
        for callback in self.callbacks:
            if callback_type == CallbackEvent.ON_WORKFLOW_START:
                await callback.on_workflow_start(*args, **kwargs)
            elif callback_type == CallbackEvent.ON_WORKFLOW_END:
                await callback.on_workflow_end(*args, **kwargs)
            elif callback_type == CallbackEvent.ON_NODE_START:
                await callback.on_node_start(*args, **kwargs)
            elif callback_type == CallbackEvent.ON_NODE_END:
                await callback.on_node_end(*args, **kwargs)
            elif callback_type == CallbackEvent.ON_NODE_STREAM_OUTPUT:
                await callback.on_node_stream_output(*args, **kwargs)

    def add_nodes(self, nodes: list[Node]) -> None:
        for node in nodes:
            node.workflow = self
        self.nodes.extend(nodes)

    def remove_nodes(self, nodes: list[Node]) -> None:
        for node in nodes:
            self.nodes.remove(node)

    def load_config(self) -> None:
        ...

    def _validate(self) -> None:
        # DAG
        ...

    def get_input_port_by_name(self, name: str) -> Port:
        for input_port in self.input_ports:
            if input_port.name == name:
                return input_port
        return None

    def get_output_port_by_name(self, name: str) -> Port:
        for output_port in self.output_ports:
            if output_port.name == name:
                return output_port
        return None

    def get_trigger_node(self) -> Trigger:
        trigger_nodes = [node for node in self.nodes if isinstance(node, Trigger)]
        if not trigger_nodes:
            raise ValueError("No trigger nodes found in workflow.")
        if len(trigger_nodes) > 1:
            raise ValueError("Multiple trigger nodes found in workflow.")
        return trigger_nodes[0]

    async def _run_node_with_callbacks(self, node: Node) -> None:
        await self.call_callbacks(CallbackEvent.ON_NODE_START, node=node)
        
        try:
            result = node.run()
            if hasattr(result, '__anext__'):
                await self.handle_node_stream_output(node, result)
            elif asyncio.iscoroutine(result):
                await result
        finally:
            await self.call_callbacks(CallbackEvent.ON_NODE_END, node=node)

    async def run_after_trigger(self) -> Any:
        logger.info(f"Running workflow: {self.name}")

        await self.call_callbacks(CallbackEvent.ON_WORKFLOW_START, workflow=self)

        self.ready_nodes = []
        for edge in self.get_trigger_node().output_edges:
            edge.end_port.trigger()

        try:
            for input_port in self.input_ports:
                if input_port.value is not None:
                    input_port.port.node.fill_input(input_port.port, input_port.value)

            for node in self.nodes:
                for key in node.AUTO_FILL_INPUT_PORTS:
                    if key[0] not in [edge.end_port.name for edge in node.input_edges]:
                        node.fill_input_by_name(key[0], key[1])

            while self.ready_nodes:
                nodes = self.ready_nodes.copy()
                self.ready_nodes = []

                tasks = []
                for node in nodes:
                    tasks.append(asyncio.create_task(self._run_node_with_callbacks(node)))

                await asyncio.gather(*tasks)

        except Exception as e:
            error_msg = f"Error in run_after_trigger: {str(e)}"
            logger.error(error_msg)
            raise e

        if len(self.output_ports) > 0:
            if len(self.output_ports) == 1:
                if self.output_ports[0].is_prepared:
                    result = self.output_ports[0].value
                else:
                    result = None
            else:
                result = {}
                for port in self.output_ports:
                    if port.is_prepared:
                        result[port.name] = port.value
            await self.call_callbacks(CallbackEvent.ON_WORKFLOW_END, workflow=self, output=result)
        else:
            await self.call_callbacks(CallbackEvent.ON_WORKFLOW_END, workflow=self, output=None)

    async def _run(self, task_id: uuid.UUID, trigger_node: Trigger) -> None:
        async with self.run_semaphore:
            try:
                new_workflow = self._clone(task_id, trigger_node)
                await new_workflow.run_after_trigger()
                # TODO: clear new_workflow

            except Exception as e:
                error_msg = f"Error running workflow: {str(e)}, {traceback.format_exc()}"
                logger.error(error_msg)

    async def run(self):
        tasks = []
        trigger = self.get_trigger_node()

        async for task_id in trigger.run():
            tasks.append(asyncio.create_task(self._run(task_id, trigger)))

        if tasks:
            await asyncio.gather(*tasks)

    async def stop(self):
        trigger = self.get_trigger_node()
        await trigger._stop()

    def trigger(self, trigger_name: str, **kwargs) -> uuid.UUID:
        trigger = self.get_trigger_node()
        task_id = uuid.uuid4()
        for key, value in kwargs.items():
            trigger.prepare_output_edges(key, value)
        task = asyncio.create_task(self._run(task_id, trigger))
        return task_id

    async def handle_node_stream_output(
        self,
        node: Node,
        stream: AsyncIterator[Any],
    ) -> None:
        async for data in stream:
            await self.call_callbacks(CallbackEvent.ON_NODE_STREAM_OUTPUT, node=node, output=data)

    # TODO: refactor this
    async def handle_query_user(self, node_name: str, prompt: str) -> Awaitable[str]:
        return await asyncio.to_thread(input, f"[{node_name}] {prompt}: ")
    
    def _clone(self, task_id: uuid.UUID, trigger_node: Trigger) -> Workflow:
        return workflow_clone(self, task_id, trigger_node)
