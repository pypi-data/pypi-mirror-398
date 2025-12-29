from __future__ import annotations

import os
import asyncio
import threading
import uuid
from loguru import logger
from typing import Callable, AsyncIterator, Awaitable, Any, TYPE_CHECKING
from service_forge.workflow.node import node_register
from service_forge.workflow.workflow_factory import create_workflow_group
from service_forge.api.http_api import start_fastapi_server
from service_forge.api.kafka_api import start_kafka_server
from service_forge.db.database import DatabaseManager
from service_forge.api.http_api_doc import generate_service_http_api_doc
from service_forge.sft.config.sf_metadata import SfMetadata
from service_forge.service_config import ServiceConfig
from service_forge.current_service import set_service

if TYPE_CHECKING:
    from service_forge.workflow.workflow_group import WorkflowGroup
    from service_forge.workflow.workflow import Workflow

class Service:
    def __init__(
        self,
        metadata: SfMetadata,
        config: ServiceConfig,
        config_path: str,
        service_env: dict[str, Any] = None,
        database_manager: DatabaseManager = None,
        _handle_stream_output: Callable[[str, AsyncIterator[str]], Awaitable[None]] = None,
        _handle_query_user: Callable[[str, str], Awaitable[str]] = None,
    ) -> None:
        self.metadata = metadata
        self.config = config
        self.config_path = config_path
        self._handle_stream_output = _handle_stream_output
        self._handle_query_user = _handle_query_user
        self.service_env = {} if service_env is None else service_env
        self.database_manager = database_manager
        self.workflow_groups: list[WorkflowGroup] = []
        self.workflow_tasks: dict[str, asyncio.Task] = {}  # workflow_name -> task mapping
        self.workflow_config_map: dict[uuid.UUID, str] = {}  # workflow_id -> config_path mapping
        self.fastapi_thread: threading.Thread | None = None
        self.fastapi_loop: asyncio.AbstractEventLoop | None = None

    @property
    def name(self) -> str:
        return self.metadata.name
    
    @property
    def version(self) -> str:
        return self.metadata.version
    
    @property
    def description(self) -> str:
        return self.metadata.description

    async def start(self):
        set_service(self)
        
        if self.config.enable_http:
            fastapi_task = asyncio.create_task(start_fastapi_server(self.config.http_host, self.config.http_port))
            doc_task = asyncio.create_task(generate_service_http_api_doc(self))
        else:
            fastapi_task = None
            doc_task = None

        if self.config.enable_kafka:
            kafka_task = asyncio.create_task(start_kafka_server(f"{self.config.kafka_host}:{self.config.kafka_port}"))
        else:
            kafka_task = None

        workflow_tasks: list[asyncio.Task] = []

        for workflow_config_path in self.config.workflows:
            logger.info(f"Loading workflow from {self.parse_workflow_path(workflow_config_path)}")
            workflow_group = create_workflow_group(
                config_path=self.parse_workflow_path(workflow_config_path),
                service_env=self.service_env,
                _handle_stream_output=self._handle_stream_output, 
                _handle_query_user=self._handle_query_user,
                database_manager=self.database_manager,
            )
            self.workflow_groups.append(workflow_group)
            main_workflow = workflow_group.get_main_workflow()
            task = asyncio.create_task(workflow_group.run())
            workflow_tasks.append(task)
            self.workflow_tasks[main_workflow.id] = task
            self.workflow_config_map[main_workflow.name] = workflow_config_path

        try:
            core_tasks = []
            if fastapi_task:
                core_tasks.append(fastapi_task)
            if doc_task:
                core_tasks.append(doc_task)
            if kafka_task:
                core_tasks.append(kafka_task)
            
            all_tasks = core_tasks + workflow_tasks
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            
            # Check core tasks
            for i, result in enumerate(results[:len(core_tasks)]):
                if isinstance(result, Exception):
                    logger.error(f"Error in service {self.name} core task {i}: {result}")
                    raise result
            
            # Check workflow tasks
            for i, result in enumerate(results[len(core_tasks):], start=len(core_tasks)):
                if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                    # Workflow task exception should not stop the service
                    logger.error(f"Error in service {self.name} workflow task {i}: {result}")

        except Exception as e:
            logger.error(f"Error in service {self.name}: {e}")
            if fastapi_task:
                fastapi_task.cancel()
            if kafka_task:
                kafka_task.cancel()
            for workflow_task in workflow_tasks:
                workflow_task.cancel()
            raise

    def parse_workflow_path(self, workflow_config_path: str) -> str:
        if os.path.isabs(workflow_config_path):
            return workflow_config_path
        else:
            return os.path.join(os.path.dirname(self.config_path), workflow_config_path)
    
    def get_workflow_group_by_name(self, workflow_name: str, workflow_version: str, allow_none: bool = True) -> WorkflowGroup | None:
        for workflow_group in self.workflow_groups:
            if workflow_group.get_workflow_by_name(workflow_name, workflow_version) is not None:
                return workflow_group
        if not allow_none:
            raise ValueError(f"Workflow group with name {workflow_name} and version {workflow_version} not found in service {self.name}")
        return None

    def get_workflow_group_by_id(self, workflow_id: str, allow_none: bool = True) -> WorkflowGroup | None:
        for workflow_group in self.workflow_groups:
            if workflow_group.get_workflow_by_id(workflow_id) is not None:
                return workflow_group
        if not allow_none:
            raise ValueError(f"Workflow group with id {workflow_id} not found in service {self.name}")
        return None

    def trigger_workflow(self, workflow_group: WorkflowGroup, trigger_name: str, **kwargs) -> uuid.UUID:
        workflow = workflow_group.get_main_workflow(allow_none=False)
        return workflow.trigger(trigger_name, **kwargs)

    def trigger_workflow_by_name(self, workflow_name: str, workflow_version: str, trigger_name: str, **kwargs) -> uuid.UUID:
        workflow_group = self.get_workflow_group_by_name(workflow_name, workflow_version, allow_none=False)
        return self.trigger_workflow(workflow_group, trigger_name, **kwargs)

    def trigger_workflow_by_id(self, workflow_id: str, trigger_name: str, **kwargs) -> uuid.UUID:
        workflow_group = self.get_workflow_group_by_id(workflow_id, allow_none=False)
        return self.trigger_workflow(workflow_group, trigger_name, **kwargs)

    def start_workflow(self, workflow_group: WorkflowGroup) -> bool:
        workflow = workflow_group.get_main_workflow(allow_none=False)
        if workflow.id in self.workflow_tasks:
            task = self.workflow_tasks[workflow.id]
            if not task.done():
                logger.warning(f"Workflow {workflow.id} is already running")
                return False
            del self.workflow_tasks[workflow.id]
        
        task = asyncio.create_task(workflow_group.run())
        self.workflow_tasks[workflow.id] = task
        logger.info(f"Started workflow {workflow.id}")
        return True

    def start_workflow_by_name(self, workflow_name: str, workflow_version: str) -> bool:
        workflow_group = self.get_workflow_group_by_name(workflow_name, workflow_version, allow_none=False)
        return self.start_workflow(workflow_group)
    
    def start_workflow_by_id(self, workflow_id: str) -> bool:
        workflow_group = self.get_workflow_group_by_id(workflow_id, allow_none=False)
        return self.start_workflow(workflow_group)

    async def stop_workflow(self, workflow_group: WorkflowGroup) -> bool:
        workflow = workflow_group.get_main_workflow(allow_none=False)
        if workflow.id not in self.workflow_tasks:
            logger.warning(f"Workflow {workflow.id} is not running")
            return False
        task = self.workflow_tasks[workflow.id]
        if task.done():
            logger.warning(f"Workflow {workflow.id} is already stopped")
            del self.workflow_tasks[workflow.id]
            return False
        task.cancel()
        await workflow.stop()
        try:
            await task
        except asyncio.CancelledError:
            pass
        del self.workflow_tasks[workflow.id]
        logger.info(f"Stopped workflow {workflow.id}")
        return True

    async def stop_workflow_by_name(self, workflow_name: str, workflow_version: str) -> bool:
        workflow_group = self.get_workflow_group_by_name(workflow_name, workflow_version, allow_none=False)
        return await self.stop_workflow(workflow_group)
    
    async def stop_workflow_by_id(self, workflow_id: str) -> bool:
        workflow_group = self.get_workflow_group_by_id(workflow_id, allow_none=False)
        return await self.stop_workflow(workflow_group)
    
    async def load_workflow_from_config(self, config_path: str = None, config: dict = None) -> uuid.UUID:
        workflow_group = create_workflow_group(
            config_path=config_path,
            config=config,
            service_env=self.service_env,
            _handle_stream_output=self._handle_stream_output,
            _handle_query_user=self._handle_query_user,
            database_manager=self.database_manager,
        )

        for workflow in workflow_group.workflows:
            existing_workflow_group = self.get_workflow_group_by_name(workflow.name, workflow.version)
            if existing_workflow_group is not None:
                raise ValueError(f"Workflow group with name {workflow.name} and version {workflow.version} already exists")

        self.workflow_groups.append(workflow_group)
        main_workflow = workflow_group.get_main_workflow()
        
        if main_workflow.id in self.workflow_tasks:
            await self.stop_workflow(workflow_group)

        self.start_workflow(workflow_group)
        return main_workflow.id
    
    def get_service_status(self) -> dict[str, Any]:
        workflow_statuses = []
        for workflow_group in self.workflow_groups:
            for workflow in workflow_group.workflows:
                workflow_id = workflow.id
                workflow_version = workflow.version
                workflow_config = workflow.config
                workflow_name = workflow.name
                is_running = workflow_id in self.workflow_tasks and not self.workflow_tasks[workflow_id].done()
                config_path = self.workflow_config_map.get(workflow_name, "unknown")
                workflow_statuses.append({
                    "name": workflow_name,
                    "id": workflow_id,
                    "version": workflow_version,
                    "config": workflow_config,
                    "description": workflow.description,
                    "status": "running" if is_running else "stopped",
                    "config_path": config_path,
                })
        
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "workflows": workflow_statuses,
        }
    
    @staticmethod
    def from_config(metadata: SfMetadata, service_env: dict[str, Any] = None, config: ServiceConfig = None) -> Service:
        if config is not None:
            config_path = None
        else:
            config_path = metadata.service_config
            config = ServiceConfig.from_yaml_file(config_path)
        database_manager = DatabaseManager.from_config(config=config)
        return Service(
            metadata=metadata,
            config_path=config_path,
            config=config,
            service_env=service_env,
            database_manager=database_manager,
            _handle_stream_output=None,
            _handle_query_user=None,
        )

def create_service(config_path: str, name: str, version: str, service_env: dict[str, Any] = None) -> Service:
    return Service.from_config(config_path, name, version, service_env)
