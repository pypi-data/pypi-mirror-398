from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from service_forge.workflow.node import Node
    from service_forge.workflow.port import Port
    from service_forge.workflow.edge import Edge
    from service_forge.workflow.workflow import Workflow
    from service_forge.workflow.trigger import Trigger
    from service_forge.workflow.context import Context

def workflow_clone(self: Workflow, task_id: uuid.UUID, trigger_node: Trigger) -> Workflow:
    from service_forge.workflow.workflow import Workflow

    if self.nodes is not None and len(self.nodes) > 0:
        context = self.nodes[0].context._clone()
    else:
        context = Context(variables={})

    node_map: dict[Node, Node] = {node: node._clone(context) for node in self.nodes}

    port_map: dict[Port, Port] = {}
    port_map.update({port: port._clone(node_map) for port in self.input_ports})
    port_map.update({port: port._clone(node_map) for port in self.output_ports})
    for node in self.nodes:
        for port in node.input_ports:
            if port not in port_map:
                port_map[port] = port._clone(node_map)
        for port in node.output_ports:
            if port not in port_map:
                port_map[port] = port._clone(node_map)

    edge_map: dict[Edge, Edge] = {}
    for node in self.nodes:
        for edge in node.input_edges:
            if edge not in edge_map:
                edge_map[edge] = edge._clone(node_map, port_map)
        for edge in node.output_edges:
            if edge not in edge_map:
                edge_map[edge] = edge._clone(node_map, port_map)

    # fill port.port
    for old_port, new_port in port_map.items():
        if old_port.port is not None:
            new_port.port = port_map[old_port.port]


    # fill ports and edges in nodes
    for old_node, new_node in node_map.items():
        new_node.input_edges = [edge_map[edge] for edge in old_node.input_edges]
        new_node.output_edges = [edge_map[edge] for edge in old_node.output_edges]
        new_node.input_ports = [port_map[port] for port in old_node.input_ports]
        new_node.output_ports = [port_map[port] for port in old_node.output_ports]
        new_node.input_variables = {
            port_map[port]: value for port, value in old_node.input_variables.items()
        }

    workflow = Workflow(
        id=self.id,
        config=self.config,
        nodes=[node_map[node] for node in self.nodes],
        input_ports=[port_map[port] for port in self.input_ports],
        output_ports=[port_map[port] for port in self.output_ports],
        _handle_stream_output=self._handle_stream_output,
        _handle_query_user=self._handle_query_user,
        database_manager=self.database_manager,
        max_concurrent_runs=self.max_concurrent_runs,
        callbacks=self.callbacks,
        task_id=task_id,
        real_trigger_node=trigger_node,
        global_context=self.global_context,
    )

    for node in workflow.nodes:
        node.workflow = workflow

    return workflow

def port_clone(self: Port, node_map: dict[Node, Node]) -> Port:
    from service_forge.workflow.port import Port
    node = node_map[self.node] if self.node is not None else None
    port = Port(
        name=self.name,
        type=self.type,
        node=node,
        port=None,
        value=self.value,
        default=self.default,
        is_extended=self.is_extended,
        is_extended_generated=self.is_extended_generated,
    )
    port.is_prepared = self.is_prepared
    return port

def node_clone(self: Node, context: Context) -> Node:
    node = self.__class__(
        name=self.name
    )
    node.context = context
    node.input_edges = []
    node.output_edges = []
    node.input_ports = []
    node.output_ports = []
    node.query_user = self.query_user
    node.workflow = None

    if self.sub_workflows is not None:
        raise ValueError("Sub workflows are not supported in node clone.")
    node.sub_workflows = None
    node.input_variables = {}
    node.num_activated_input_edges = self.num_activated_input_edges

    return node

def edge_clone(self: Edge, node_map: dict[Node, Node], port_map: dict[Port, Port]) -> Edge:
    from service_forge.workflow.edge import Edge
    start_node = node_map[self.start_node] if self.start_node is not None else None
    end_node = node_map[self.end_node] if self.end_node is not None else None
    return Edge(
        start_node=start_node,
        end_node=end_node,
        start_port=port_map[self.start_port],
        end_port=port_map[self.end_port],
    )
