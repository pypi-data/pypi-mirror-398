from ..utils.type_converter import TypeConverter
from ..workflow.workflow import Workflow
from ..api.http_api import fastapi_app
from ..api.kafka_api import KafkaApp, kafka_app
from ..workflow.workflow_type import WorkflowType, workflow_type_register
from fastapi import FastAPI

type_converter = TypeConverter()
type_converter.register(str, Workflow, lambda s, node: node.sub_workflows.get_workflow(s))
type_converter.register(str, FastAPI, lambda s, node: fastapi_app)
type_converter.register(str, KafkaApp, lambda s, node: kafka_app)
type_converter.register(str, type, lambda s, node: workflow_type_register.items[s].type)