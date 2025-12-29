from __future__ import annotations
from typing import TYPE_CHECKING, Any
from ..utils.workflow_clone import port_clone

if TYPE_CHECKING:
    from .node import Node

class Port:
    def __init__(
        self,
        name: str,
        type: type,
        node: Node = None,
        port: Port = None,
        value: Any = None,
        default: Any = None,
        is_extended: bool = False,
        is_extended_generated: bool = False,
    ) -> None:
        self.name = name
        self.type = type
        self.node = node
        self.port = port
        self.value = value
        # not used yet
        self.default = default
        self.is_prepared = False
        self.is_extended = is_extended
        self.is_extended_generated = is_extended_generated
    
    def is_sub_workflow_input_port(self) -> bool:
        return self.port != None

    def prepare(self, data: Any) -> None:
        from ..utils.default_type_converter import type_converter
        data = type_converter.convert(data, self.type, node=self.node)
        self.value = data
        self.is_prepared = True

    def trigger(self) -> None:
        if self.node is None:
            return
        if self in self.node.input_variables:
            return
        self.node.input_variables[self] = self.value
        self.node.num_activated_input_edges += 1
        if self.node.is_ready():
            self.node.workflow.ready_nodes.append(self.node)

    def activate(self, data: Any) -> None:
        self.prepare(data)
        self.trigger()

    def get_extended_name(self) -> str:
        if self.is_extended_generated:
            return '_'.join(self.name.split('_')[:-1])
        raise ValueError(f"Port {self.name} is not extended generated.")
    
    def get_extended_index(self) -> int:
        if self.is_extended_generated:
            return int(self.name.split('_')[-1])
        raise ValueError(f"Port {self.name} is not extended generated.")

    def _clone(self, node_map: dict[Node, Node]) -> Port:
        return port_clone(self, node_map)

# node port
def create_port(name: str, type: type, node: Node = None, value: Any = None, port: Port = None) -> Port:
    return Port(name, type, node, port, value)

# workflow input port
def create_workflow_input_port(name: str, port: Port, value: Any = None) -> Port:
    if value is None:
        value = port.value
    return Port(name, port.type, port.node, port, value)

# sub workflow input port
# node is the node that the sub workflow is running on
def create_sub_workflow_input_port(name: str, node: Node, port: Port, value: Any = None) -> Port:
    if value is None:
        value = port.value
    return Port(name, port.type, node, port, value)

PORT_DELIMITER = '|'

def parse_port_name(port_name: str) -> tuple[str, str]:
    if PORT_DELIMITER not in port_name or len(port_name.split(PORT_DELIMITER)) != 2:
        raise ValueError(f"Invalid port name: {port_name}")
    return port_name.split(PORT_DELIMITER)