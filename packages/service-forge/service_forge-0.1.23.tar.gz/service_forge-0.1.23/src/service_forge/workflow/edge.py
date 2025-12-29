from __future__ import annotations

from typing import TYPE_CHECKING
from ..utils.workflow_clone import edge_clone

if TYPE_CHECKING:
    from .node import Node
    from .port import Port

class Edge:
    def __init__(
        self,
        start_node: Node,
        end_node: Node,
        start_port: Port,
        end_port: Port,
    ) -> None:
        self.start_node = start_node
        self.end_node = end_node
        self.start_port = start_port
        self.end_port = end_port

    def _clone(self, node_map: dict[Node, Node], port_map: dict[Port, Port]) -> Edge:
        return edge_clone(self, node_map, port_map)
