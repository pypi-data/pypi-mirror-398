from __future__ import annotations

from typing import Any, AsyncIterator, Union, TYPE_CHECKING, Callable, Awaitable
from abc import ABC, abstractmethod
import uuid
from loguru import logger
from .edge import Edge
from .port import Port
from .context import Context
from ..utils.register import Register
from ..db.database import DatabaseManager, PostgresDatabase, MongoDatabase, RedisDatabase
from ..utils.workflow_clone import node_clone
from .workflow_callback import CallbackEvent

if TYPE_CHECKING:
    from .workflow import Workflow

class Node(ABC):
    DEFAULT_INPUT_PORTS: list[Port] = []
    DEFAULT_OUTPUT_PORTS: list[Port] = []

    CLASS_NOT_REQUIRED_TO_REGISTER = ['Node']
    AUTO_FILL_INPUT_PORTS = []

    def __init__(
        self,
        name: str,
        context: Context = None,
        input_edges: list[Edge] = None,
        output_edges: list[Edge] = None,
        input_ports: list[Port] = DEFAULT_INPUT_PORTS,
        output_ports: list[Port] = DEFAULT_OUTPUT_PORTS,
        query_user: Callable[[str, str], Awaitable[str]] = None,
    ) -> None:
        from .workflow_group import WorkflowGroup
        self.name = name
        self.input_edges = [] if input_edges is None else input_edges
        self.output_edges = [] if output_edges is None else output_edges
        self.input_ports = input_ports
        self.output_ports = output_ports
        self.workflow: Workflow = None
        self.query_user = query_user
        self.sub_workflows: WorkflowGroup = None

        # runtime variables
        self.context = context
        self.input_variables: dict[Port, Any] = {}
        self.num_activated_input_edges = 0

    @property
    def default_postgres_database(self) -> PostgresDatabase | None:
        return self.database_manager.get_default_postgres_database()

    @property
    def default_mongo_database(self) -> MongoDatabase | None:
        return self.database_manager.get_default_mongo_database()

    @property
    def default_redis_database(self) -> RedisDatabase | None:
        return self.database_manager.get_default_redis_database()
    
    @property
    def database_manager(self) -> DatabaseManager:
        return self.workflow.database_manager

    @property
    def global_context(self) -> Context:
        return self.workflow.global_context

    def backup(self) -> None:
        # do NOT use deepcopy here
        # self.bak_context = deepcopy(self.context)
        # TODO: what if the value changes after backup?
        self.bak_input_variables = {port: value for port, value in self.input_variables.items()}
        self.bak_num_activated_input_edges = self.num_activated_input_edges

    def reset(self) -> None:
        # self.context = deepcopy(self.bak_context)
        self.input_variables = {port: value for port, value in self.bak_input_variables.items()}
        self.num_activated_input_edges = self.bak_num_activated_input_edges

    def __init_subclass__(cls) -> None:
        if cls.__name__ not in Node.CLASS_NOT_REQUIRED_TO_REGISTER:
            node_register.register(cls.__name__, cls)
        return super().__init_subclass__()

    def _query_user(self, prompt: str) -> Callable[[str, str], Awaitable[str]]:
        return self.query_user(self.name, prompt)
    
    def variables_to_params(self) -> dict[str, Any]:
        params = {port.name: self.input_variables[port] for port in self.input_variables.keys() if not port.is_extended_generated}
        for port in self.input_variables.keys():
            if port.is_extended_generated:
                if port.get_extended_name() not in params:
                    params[port.get_extended_name()] = []
                params[port.get_extended_name()].append((port.get_extended_index(), self.input_variables[port]))
                params[port.get_extended_name()].sort()
        return params

    def is_trigger(self) -> bool:
        from .trigger import Trigger
        return isinstance(self, Trigger)

    # TODO: maybe add a function before the run function?

    @abstractmethod
    async def _run(self, **kwargs) -> Union[None, AsyncIterator]:
        ...
    
    def run(self) -> Union[None, AsyncIterator]:
        for key in list(self.input_variables.keys()):
            if key and key.name[0].isupper():
                del self.input_variables[key]
        params = self.variables_to_params()
        return self._run(**params)

    def get_input_port_by_name(self, name: str) -> Port:
        # TODO: add warning if port is extended
        for port in self.input_ports:
            if port.name == name:
                return port
        return None

    def get_output_port_by_name(self, name: str) -> Port:
        # TODO: add warning if port is extended
        for port in self.output_ports:
            if port.name == name:
                return port
        return None

    def try_create_extended_input_port(self, name: str) -> None:
        for port in self.input_ports:
            if port.is_extended and name.startswith(port.name + '_') and name[len(port.name + '_'):].isdigit():
                self.input_ports.append(Port(name=name, type=port.type, node=port.node, port=port.port, value=port.value, default=port.default, is_extended=False, is_extended_generated=True))

    def try_create_extended_output_port(self, name: str) -> None:
        for port in self.output_ports:
            if port.is_extended and name.startswith(port.name + '_') and name[len(port.name + '_'):].isdigit():
                self.output_ports.append(Port(name=name, type=port.type, node=port.node, port=port.port, value=port.value, default=port.default, is_extended=False, is_extended_generated=True))

    def num_input_ports(self) -> int:
        return sum(1 for port in self.input_ports if not port.is_extended)
    
    def is_ready(self) -> bool:
        return self.num_activated_input_edges == self.num_input_ports()

    def fill_input_by_name(self, port_name: str, value: Any) -> None:
        self.try_create_extended_input_port(port_name)
        port = self.get_input_port_by_name(port_name)
        if port is None:
            raise ValueError(f'{port_name} is not a valid input port.')
        self.fill_input(port, value)
    
    def fill_input(self, port: Port, value: Any) -> None:
        port.activate(value)

    def activate_output_edges(self, port: str | Port, data: Any) -> None:
        if isinstance(port, str):
            port = self.get_output_port_by_name(port)
        for output_edge in self.output_edges:
            if output_edge.start_port == port:
                output_edge.end_port.activate(data)

    # for trigger nodes
    def prepare_output_edges(self, port: Port, data: Any) -> None:
        if isinstance(port, str):
            port = self.get_output_port_by_name(port)
        for output_edge in self.output_edges:
            if output_edge.start_port == port:
                output_edge.end_port.prepare(data)
    
    def trigger_output_edges(self, port: Port) -> None:
        if isinstance(port, str):
            port = self.get_output_port_by_name(port)
        for output_edge in self.output_edges:
            if output_edge.start_port == port:
                output_edge.end_port.trigger()

    # TODO: the result is outputed to the trigger now, maybe we should add a new function to output the result to the workflow
    def output_to_workflow(self, data: Any) -> None:
        self.workflow._handle_workflow_output(self.name, data)

    def extended_output_name(self, name: str, index: int) -> str:
        return name + '_' + str(index)

    def _clone(self, context: Context) -> Node:
        return node_clone(self, context)

    async def stream_output(self, data: Any) -> None:
         await self.workflow.call_callbacks(CallbackEvent.ON_NODE_STREAM_OUTPUT, node=self, output=data)

node_register = Register[Node]()