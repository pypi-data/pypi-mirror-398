import asyncio
from typing import TYPE_CHECKING, Any, Union
from service_forge.api.http_api import fastapi_app
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from google.protobuf.message import Message
from google.protobuf import descriptor as _descriptor
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH, EXTENDED_AGENT_CARD_PATH

if TYPE_CHECKING:
    from service_forge.service import Service
    from service_forge.workflow.workflow import Workflow
    from service_forge.workflow.workflow_group import WorkflowGroup

def _protobuf_type_to_json_schema_type(field_type: int) -> dict[str, Any]:
    """将 protobuf 字段类型转换为 JSON schema 类型"""
    type_map = {
        _descriptor.FieldDescriptor.TYPE_DOUBLE: {"type": "number", "format": "double"},
        _descriptor.FieldDescriptor.TYPE_FLOAT: {"type": "number", "format": "float"},
        _descriptor.FieldDescriptor.TYPE_INT64: {"type": "integer", "format": "int64"},
        _descriptor.FieldDescriptor.TYPE_UINT64: {"type": "integer", "format": "uint64"},
        _descriptor.FieldDescriptor.TYPE_INT32: {"type": "integer", "format": "int32"},
        _descriptor.FieldDescriptor.TYPE_UINT32: {"type": "integer", "format": "uint32"},
        _descriptor.FieldDescriptor.TYPE_FIXED64: {"type": "integer", "format": "int64"},
        _descriptor.FieldDescriptor.TYPE_FIXED32: {"type": "integer", "format": "int32"},
        _descriptor.FieldDescriptor.TYPE_SFIXED32: {"type": "integer", "format": "int32"},
        _descriptor.FieldDescriptor.TYPE_SFIXED64: {"type": "integer", "format": "int64"},
        _descriptor.FieldDescriptor.TYPE_SINT32: {"type": "integer", "format": "int32"},
        _descriptor.FieldDescriptor.TYPE_SINT64: {"type": "integer", "format": "int64"},
        _descriptor.FieldDescriptor.TYPE_BOOL: {"type": "boolean"},
        _descriptor.FieldDescriptor.TYPE_STRING: {"type": "string"},
        _descriptor.FieldDescriptor.TYPE_BYTES: {"type": "string", "format": "byte"},
    }
    return type_map.get(field_type, {"type": "string"})


def _get_protobuf_message_class_from_descriptor(message_descriptor: _descriptor.Descriptor) -> type[Message] | None:
    """从 Descriptor 获取对应的 Python Message 类"""
    try:
        from google.protobuf import symbol_database
        _sym_db = symbol_database.Default()
        return _sym_db.GetPrototype(message_descriptor)
    except Exception:
        # 如果无法通过 symbol_database 获取，尝试通过模块查找
        try:
            # 尝试从包含的文件描述符中获取
            file_desc = message_descriptor.file
            package = file_desc.package
            message_name = message_descriptor.name
            
            # 尝试导入模块（这需要知道模块路径）
            # 这里我们返回 None，让调用者处理
            return None
        except Exception:
            return None


def _protobuf_message_to_json_schema(message_class: type[Message], openapi_schema: dict[str, Any], visited: set[str] | None = None) -> dict[str, Any]:
    """将 protobuf Message 类型转换为 JSON schema"""
    if visited is None:
        visited = set()
    
    descriptor = message_class.DESCRIPTOR
    model_name = descriptor.name
    
    # 防止循环引用
    if model_name in visited:
        return {"$ref": f"#/components/schemas/{model_name}"}
    
    visited.add(model_name)
    
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    for field in descriptor.fields:
        field_name = field.name
        field_schema: dict[str, Any] = {}
        
        if field.label == field.LABEL_REPEATED:
            # 数组类型
            if field.type == field.TYPE_MESSAGE:
                # 嵌套消息数组
                nested_message_class = _get_protobuf_message_class_from_descriptor(field.message_type)
                if nested_message_class:
                    # 确保嵌套消息的 schema 也被添加
                    _get_protobuf_schema_ref(nested_message_class, openapi_schema, visited)
                    nested_schema_ref = f"#/components/schemas/{field.message_type.name}"
                    field_schema = {
                        "type": "array",
                        "items": {"$ref": nested_schema_ref}
                    }
                else:
                    # 如果无法获取类，使用通用对象类型
                    field_schema = {
                        "type": "array",
                        "items": {"type": "object"}
                    }
            else:
                # 基本类型数组
                item_schema = _protobuf_type_to_json_schema_type(field.type)
                field_schema = {
                    "type": "array",
                    "items": item_schema
                }
        elif field.type == field.TYPE_MESSAGE:
            # 嵌套消息
            nested_message_class = _get_protobuf_message_class_from_descriptor(field.message_type)
            if nested_message_class:
                # 确保嵌套消息的 schema 也被添加
                _get_protobuf_schema_ref(nested_message_class, openapi_schema, visited)
                nested_schema_ref = f"#/components/schemas/{field.message_type.name}"
                field_schema = {"$ref": nested_schema_ref}
            else:
                # 如果无法获取类，使用通用对象类型
                field_schema = {"type": "object"}
        else:
            # 基本类型
            field_schema = _protobuf_type_to_json_schema_type(field.type)
        
        schema["properties"][field_name] = field_schema
    
    visited.remove(model_name)
    return schema


def _get_protobuf_schema_ref(message_class: type[Message], openapi_schema: dict[str, Any], visited: set[str] | None = None) -> str:
    """获取 protobuf Message 的 schema 引用"""
    model_name = message_class.DESCRIPTOR.name
    
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
    
    if model_name not in openapi_schema["components"]["schemas"]:
        json_schema = _protobuf_message_to_json_schema(message_class, openapi_schema, visited)
        openapi_schema["components"]["schemas"][model_name] = json_schema
    
    return f"#/components/schemas/{model_name}"


def _process_pydantic_schema_with_defs(json_schema: dict[str, Any], openapi_schema: dict[str, Any], visited: set[str] | None = None) -> dict[str, Any]:
    """处理 Pydantic 生成的 JSON schema，将 $defs 中的嵌套模型迁移到 components/schemas"""
    if visited is None:
        visited = set()
    
    # 确保 components/schemas 存在
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
    
    # 处理 $defs 中的嵌套模型定义
    if "$defs" in json_schema:
        defs = json_schema.pop("$defs")
        for def_name, def_schema in defs.items():
            if def_name not in visited:
                visited.add(def_name)
                # 递归处理嵌套的 $defs
                processed_def_schema = _process_pydantic_schema_with_defs(def_schema.copy(), openapi_schema, visited)
                openapi_schema["components"]["schemas"][def_name] = processed_def_schema
                visited.remove(def_name)
    
    # 更新 schema 中的 $ref 引用，从 #/$defs/ModelName 改为 #/components/schemas/ModelName
    def update_refs(obj: Any) -> Any:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                if ref.startswith("#/$defs/"):
                    obj["$ref"] = ref.replace("#/$defs/", "#/components/schemas/")
            else:
                for key, value in obj.items():
                    obj[key] = update_refs(value)
        elif isinstance(obj, list):
            return [update_refs(item) for item in obj]
        return obj
    
    return update_refs(json_schema)


def _get_model_schema_ref(model: Union[type[BaseModel], type[Message]], openapi_schema: dict[str, Any], visited: set[str] | None = None) -> str:
    """获取模型的 schema 引用，支持 Pydantic BaseModel 和 protobuf Message"""
    if issubclass(model, BaseModel):
        model_name = model.__name__
        
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "schemas" not in openapi_schema["components"]:
            openapi_schema["components"]["schemas"] = {}
        
        if model_name not in openapi_schema["components"]["schemas"]:
            json_schema = model.model_json_schema()
            # 处理嵌套模型定义
            processed_schema = _process_pydantic_schema_with_defs(json_schema, openapi_schema, visited)
            openapi_schema["components"]["schemas"][model_name] = processed_schema
        
        return f"#/components/schemas/{model_name}"
    elif issubclass(model, Message):
        return _get_protobuf_schema_ref(model, openapi_schema, visited)
    else:
        raise ValueError(f"Unsupported model type: {type(model)}")


def _convert_model_to_parameters(model: Union[type[BaseModel], type[Message]], openapi_schema: dict[str, Any]) -> list[dict[str, Any]]:
    """将模型转换为 OpenAPI query parameters，支持 Pydantic BaseModel 和 protobuf Message"""
    parameters = []
    
    if issubclass(model, BaseModel):
        # 先处理嵌套模型定义，确保它们都在 components/schemas 中
        # 这会返回处理后的 schema 引用，同时将所有嵌套模型添加到 components/schemas
        _get_model_schema_ref(model, openapi_schema)
        
        # 从已经处理过的 components/schemas 中获取 schema
        model_name = model.__name__
        if model_name in openapi_schema.get("components", {}).get("schemas", {}):
            processed_schema = openapi_schema["components"]["schemas"][model_name]
        else:
            # 如果还没有处理过，则处理它
            json_schema = model.model_json_schema()
            processed_schema = _process_pydantic_schema_with_defs(json_schema, openapi_schema)
        
        properties = processed_schema.get("properties", {})
        required = processed_schema.get("required", [])
        
        for field_name, field_info in properties.items():
            param = {
                "name": field_name,
                "in": "query",
                "required": field_name in required,
                "schema": field_info
            }
            parameters.append(param)
    elif issubclass(model, Message):
        descriptor = model.DESCRIPTOR
        for field in descriptor.fields:
            field_name = field.name
            field_schema = _protobuf_type_to_json_schema_type(field.type)
            
            # 对于数组和嵌套消息，在 query 参数中可能不太适用，但我们可以尝试
            if field.label == field.LABEL_REPEATED:
                if field.type == field.TYPE_MESSAGE:
                    # 嵌套消息数组，在 query 中不支持，跳过
                    continue
                else:
                    # 基本类型数组
                    field_schema = {
                        "type": "array",
                        "items": field_schema
                    }
            elif field.type == field.TYPE_MESSAGE:
                # 嵌套消息，在 query 中不支持，跳过
                continue
            
            param = {
                "name": field_name,
                "in": "query",
                "required": False,  # protobuf 字段在 proto3 中默认都是可选的
                "schema": field_schema
            }
            parameters.append(param)
    
    return parameters


def _convert_model_to_request_body(model: Union[type[BaseModel], type[Message]], openapi_schema: dict[str, Any]) -> dict[str, Any]:
    """将模型转换为 OpenAPI request body，支持 Pydantic BaseModel 和 protobuf Message"""
    schema_ref = _get_model_schema_ref(model, openapi_schema)
    return {
        "content": {
            "application/json": {
                "schema": {"$ref": schema_ref}
            }
        }
    }


def _convert_model_to_response_schema(model: Union[type[BaseModel], type[Message]], openapi_schema: dict[str, Any]) -> dict[str, Any]:
    """将模型转换为 OpenAPI response schema，支持 Pydantic BaseModel 和 protobuf Message"""
    schema_ref = _get_model_schema_ref(model, openapi_schema)
    return {
        "description": "Success",
        "content": {
            "application/json": {
                "schema": {"$ref": schema_ref}
            }
        }
    }


async def generate_service_http_api_doc(service: 'Service') -> None:
    await asyncio.sleep(1)
    openapi_schema = get_openapi(
        title=service.name,
        version=service.version,
        description=service.description,
        routes=fastapi_app.routes,
    )


    from service_forge.workflow.triggers.fast_api_trigger import FastAPITrigger
    from service_forge.workflow.triggers.a2a_api_trigger import A2AAPITrigger

    for workflow_group in service.workflow_groups:
        main_workflow = workflow_group.get_main_workflow()
        fastapi_triggers = [node for node in main_workflow.nodes if isinstance(node, FastAPITrigger)]
        a2a_triggers = [node for node in main_workflow.nodes if isinstance(node, A2AAPITrigger)]

        # TODO: multiple output ports
        if main_workflow.output_ports:
            output_type = main_workflow.output_ports[0].port.type
        else:
            output_type = None

        for trigger in fastapi_triggers:
            path = trigger.get_input_port_by_name("path").value
            method = trigger.get_input_port_by_name("method").value
            data_type = trigger.get_input_port_by_name("data_type").value

            if "paths" not in openapi_schema:
                openapi_schema["paths"] = {}
            if path not in openapi_schema["paths"]:
                openapi_schema["paths"][path] = {}
            
            operation: dict[str, Any] = {
                "summary": main_workflow.name,
                "description": main_workflow.description,
            }
            
            method_lower = method.lower()
            if method_lower == "get":
                if data_type and isinstance(data_type, type) and (issubclass(data_type, BaseModel) or issubclass(data_type, Message)):
                    operation["parameters"] = _convert_model_to_parameters(data_type, openapi_schema)
            else:
                if data_type and isinstance(data_type, type) and (issubclass(data_type, BaseModel) or issubclass(data_type, Message)):
                    operation["requestBody"] = _convert_model_to_request_body(data_type, openapi_schema)
            
            if output_type and isinstance(output_type, type) and (issubclass(output_type, BaseModel) or issubclass(output_type, Message)):
                operation["responses"] = {
                    "200": _convert_model_to_response_schema(output_type, openapi_schema)
                }
            else:
                operation["responses"] = {
                    "200": {
                        "description": "Success",
                    }
                }
            
            openapi_schema["paths"][path][method_lower] = operation

        # Handle A2A triggers
        for trigger in a2a_triggers:
            if not trigger.agent_card:
                continue
            
            agent_card = trigger.agent_card
            base_path = "/a2a"
            
            # Add agent card endpoint
            agent_card_path = base_path + AGENT_CARD_WELL_KNOWN_PATH
            if "paths" not in openapi_schema:
                openapi_schema["paths"] = {}
            if agent_card_path not in openapi_schema["paths"]:
                openapi_schema["paths"][agent_card_path] = {}
            
            openapi_schema["paths"][agent_card_path]["get"] = {
                "summary": f"Get {agent_card.name} Agent Card",
                "description": agent_card.description or f"Retrieve the agent card for {agent_card.name}",
                "tags": ["A2A Agent"],
                "responses": {
                    "200": {
                        "description": "Agent card JSON",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "description": "A2A Agent Card specification"
                                }
                            }
                        }
                    }
                }
            }
            
            # Add JSON-RPC endpoint
            rpc_path = base_path + "/"
            if rpc_path not in openapi_schema["paths"]:
                openapi_schema["paths"][rpc_path] = {}
            
            openapi_schema["paths"][rpc_path]["post"] = {
                "summary": f"{agent_card.name} JSON-RPC Endpoint",
                "description": agent_card.description or f"JSON-RPC endpoint for {agent_card.name}",
                "tags": ["A2A Agent"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "description": "JSON-RPC request",
                                "properties": {
                                    "jsonrpc": {"type": "string", "example": "2.0"},
                                    "method": {"type": "string"},
                                    "params": {"type": "object"},
                                    "id": {"type": ["string", "integer", "null"]}
                                },
                                "required": ["jsonrpc", "method"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "JSON-RPC response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "description": "JSON-RPC response"
                                }
                            }
                        }
                    }
                }
            }
            
            # Add extended card endpoint if supported
            if agent_card.supports_authenticated_extended_card:
                extended_card_path = base_path + EXTENDED_AGENT_CARD_PATH
                if extended_card_path not in openapi_schema["paths"]:
                    openapi_schema["paths"][extended_card_path] = {}
                
                openapi_schema["paths"][extended_card_path]["get"] = {
                    "summary": f"Get {agent_card.name} Authenticated Extended Agent Card",
                    "description": f"Retrieve the authenticated extended agent card for {agent_card.name}",
                    "tags": ["A2A Agent"],
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Extended agent card JSON",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "description": "A2A Extended Agent Card specification"
                                    }
                                }
                            }
                        }
                    }
                }

    fastapi_app.openapi_schema = openapi_schema
