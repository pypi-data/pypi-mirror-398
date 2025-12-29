from __future__ import annotations
import os
import importlib
import inspect
from pathlib import Path
from typing import Type, Any

from service_forge.utils.register import Register

class WorkflowType:
    CLASS_NOT_REQUIRED_TO_REGISTER = ['WorkflowType']

    def __init__(self, name: str, type: type) -> None:
        self.name = name
        self.type = type

    def __init_subclass__(cls) -> None:
        if cls.__name__ not in WorkflowType.CLASS_NOT_REQUIRED_TO_REGISTER:
            workflow_type_register.register(cls.__name__, cls)
        return super().__init_subclass__()

workflow_type_register = Register[WorkflowType]()

def _load_proto_classes():
    # TODO: load from config
    proto_dir = Path(__file__).parent.parent / "proto"
    
    if not proto_dir.exists():
        return
    
    for py_file in proto_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        module_name = py_file.stem
        module_path = f"service_forge.proto.{module_name}"
        
        try:
            module = importlib.import_module(module_path)
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (not name.startswith('_') and 
                    obj.__module__ == module_path and
                    hasattr(obj, '__bases__')):
                    
                    workflow_type = WorkflowType(name, obj)
                    workflow_type_register.register(name, workflow_type)
                    
        except Exception as e:
            print(f"Failed to load module {module_path}: {e}")

_load_proto_classes()
