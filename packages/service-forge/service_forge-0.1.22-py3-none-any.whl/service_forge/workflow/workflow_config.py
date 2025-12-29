from __future__ import annotations

import yaml
from typing import Any
from pydantic import BaseModel

DEFAULT_WORKFLOW_VERSION = "0"

class WorkflowNodeOutputConfig(BaseModel):
    name: str
    port: str

class WorkflowNodeArgConfig(BaseModel):
    name: str
    value: Any | None = None

class WorkflowInputPortConfig(BaseModel):
    name: str
    port: str
    value: Any | None = None

class WorkflowOutputPortConfig(BaseModel):
    name: str
    port: str

class WorkflowNodeSubWorkflowConfig(BaseModel):
    name: str
    version: str = DEFAULT_WORKFLOW_VERSION

class WorkflowNodeSubWorkflowInputPortConfig(BaseModel):
    name: str
    port: str
    value: Any | None = None

class WorkflowNodeConfig(BaseModel):
    name: str
    type: str
    args: dict | None = None
    outputs: dict | None = None
    sub_workflows: list[WorkflowNodeSubWorkflowConfig] | None = None
    sub_workflows_input_ports: list[WorkflowNodeSubWorkflowInputPortConfig] | None = None

class WorkflowConfig(BaseModel):
    name: str
    version: str = DEFAULT_WORKFLOW_VERSION
    description: str
    nodes: list[WorkflowNodeConfig]
    inputs: list[WorkflowInputPortConfig] | None = None
    outputs: list[WorkflowOutputPortConfig] | None = None

    @classmethod
    def from_yaml_file(cls, filepath: str) -> WorkflowConfig:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)

class WorkflowGroupConfig(BaseModel):
    workflows: list[WorkflowConfig] | None
    main_workflow_name: str | None
    main_workflow_version: str | None = DEFAULT_WORKFLOW_VERSION

    @classmethod
    def from_yaml_file(cls, filepath: str) -> WorkflowGroupConfig:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)