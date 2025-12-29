import os
import uuid
from pydantic import BaseModel
import omegaconf

config_folders = [
    os.path.join("configs", "workflow"),
    os.path.join("example", "tag-service", "configs", "workflow"),
]


class NodeModel(BaseModel):
    id: str
    type: str

class EdgeModel(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: str
    targetHandle: str

class WorkflowModel(BaseModel):
    id: str
    name: str
    path: str
    nodes: list[NodeModel]
    edges: list[EdgeModel]

def get_workflow_path(workflow_id: str) -> str:
    for workflow in workflows:
        if workflow.id == workflow_id:
            return workflow.path
    return None

def load_workflow(workflow_path: str) -> WorkflowModel:
    config = omegaconf.OmegaConf.load(workflow_path)
    if 'workflows' in config:
        return None # sub workflow is not supported yet
    nodes = []
    edges = []
    print(workflow_path)
    if 'nodes' in config:
        for node in config['nodes']:
            nodes.append(NodeModel(id=node['name'], type='base'))
        for node in config['nodes']:
            if outputs := node.get('outputs', None):
                for port, value in outputs.items():
                    if value is None:
                        continue
                    source_node_name, source_port_name = node['name'], port
                    if type(value) == str:
                        value = [value]
                    for edge_value in list(value):
                        target_node_name, target_port_name = edge_value.split('|')
                        edges.append(EdgeModel(
                            id=str(uuid.uuid4()),
                            source=node['name'],
                            target=target_node_name,
                            sourceHandle=f"{source_node_name}#source#{source_port_name}",
                            targetHandle=f"{target_node_name}#target#{target_port_name}"
                        ))
    return WorkflowModel(
        id=str(uuid.uuid4()),
        name=config.get('name', 'Unknown Workflow'),
        path=workflow_path,
        nodes=nodes,
        edges=edges
    )

def load_workflows() -> list[WorkflowModel]:
    workflows = []

    for config_folder in config_folders:
        for config_path in os.listdir(config_folder):
            if config_path.endswith(".yaml"):
                if workflow := load_workflow(os.path.join(config_folder, config_path)):
                    workflows.append(workflow)
    return workflows

workflows = load_workflows()