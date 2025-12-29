from __future__ import annotations
import uuid
import asyncio
import json
from loguru import logger
from service_forge.workflow.trigger import Trigger
from typing import AsyncIterator, Any
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from service_forge.workflow.port import Port
from service_forge.utils.default_type_converter import type_converter
from service_forge.api.routers.websocket.websocket_manager import websocket_manager
from fastapi import HTTPException
from google.protobuf.message import Message
from google.protobuf.json_format import MessageToJson

class FastAPITrigger(Trigger):
    DEFAULT_INPUT_PORTS = [
        Port("app", FastAPI),
        Port("path", str),
        Port("method", str),
        Port("data_type", type),
        Port("is_stream", bool),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("trigger", bool),
        Port("user_id", int),
        Port("data", Any),
    ]

    def __init__(self, name: str):
        super().__init__(name)
        self.events = {}
        self.is_setup_route = False
        self.app = None
        self.route_path = None
        self.route_method = None

    @staticmethod
    def serialize_result(result: Any):
        if isinstance(result, Message):
            return MessageToJson(
                result,
                preserving_proto_field_name=True
            )
        return result

    async def handle_request(
        self,
        request: Request,
        data_type: type,
        extract_data_fn: callable[[Request], dict],
        is_stream: bool,
    ):
        task_id = uuid.uuid4()
        self.result_queues[task_id] = asyncio.Queue()

        body_data = await extract_data_fn(request)
        converted_data = data_type(**body_data)

        client_id = (
            body_data.get("client_id")
            or request.query_params.get("client_id")
            or request.headers.get("X-Client-ID")
        )
        if client_id:
            workflow_name = getattr(self.workflow, "name", "Unknown")
            steps = len(self.workflow.nodes) if hasattr(self.workflow, "nodes") else 1
            websocket_manager.create_task_with_client(task_id, client_id, workflow_name, steps)

        self.trigger_queue.put_nowait({
            "id": task_id,
            "user_id": getattr(request.state, "user_id", None),
            "data": converted_data,
        })

        if is_stream:
            self.stream_queues[task_id] = asyncio.Queue()

            async def generate_sse():
                try:
                    while True:
                        item = await self.stream_queues[task_id].get()

                        if item.is_error:
                            yield f"event: error\ndata: {json.dumps({'detail': str(item.result)})}\n\n"
                            break
                        
                        if item.is_end:
                            # TODO: send the result?
                            break

                        # TODO: modify
                        serialized = self.serialize_result(item.result)
                        if isinstance(serialized, str):
                            data = serialized
                        else:
                            data = json.dumps(serialized)
                        
                        yield f"data: {data}\n\n"
                    
                except Exception as e:
                    yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"
                finally:
                    if task_id in self.stream_queues:
                        del self.stream_queues[task_id]
                    if task_id in self.result_queues:
                        del self.result_queues[task_id]
            
            return StreamingResponse(
                generate_sse(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        else:
            result = await self.result_queues[task_id].get()
            del self.result_queues[task_id]

            if result.is_error:
                if isinstance(result.result, HTTPException):
                    raise result.result
                else:
                    raise HTTPException(status_code=500, detail=str(result.result))

            return self.serialize_result(result.result)

    def _setup_route(self, app: FastAPI, path: str, method: str, data_type: type, is_stream: bool) -> None:
        async def get_data(request: Request) -> dict:
            return dict(request.query_params)

        async def body_data(request: Request) -> dict:
            raw = await request.body()
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))

        extractor = get_data if method == "GET" else body_data

        async def handler(request: Request):
            return await self.handle_request(request, data_type, extractor, is_stream)

        # Save route information for cleanup
        self.app = app
        self.route_path = path
        self.route_method = method.upper()

        if method == "GET":
            app.get(path)(handler)
        elif method == "POST":
            app.post(path)(handler)
        elif method == "PUT":
            app.put(path)(handler)
        elif method == "DELETE":
            app.delete(path)(handler)
        else:
            raise ValueError(f"Invalid method {method}")

    async def _run(self, app: FastAPI, path: str, method: str, data_type: type, is_stream: bool = False) -> AsyncIterator[bool]:
        if not self.is_setup_route:
            self._setup_route(app, path, method, data_type, is_stream)
            self.is_setup_route = True

        while True:
            try:
                trigger = await self.trigger_queue.get()
                self.prepare_output_edges(self.get_output_port_by_name('user_id'), trigger['user_id'])
                self.prepare_output_edges(self.get_output_port_by_name('data'), trigger['data'])
                yield self.trigger(trigger['id'])
            except Exception as e:
                logger.error(f"Error in FastAPITrigger._run: {e}")
                continue

    async def _stop(self) -> AsyncIterator[bool]:
        if self.is_setup_route:
            # Remove the route from the app
            if self.app and self.route_path and self.route_method:
                # Find and remove matching route
                routes_to_remove = []
                for route in self.app.routes:
                    if hasattr(route, "path") and hasattr(route, "methods"):
                        if route.path == self.route_path and self.route_method in route.methods:
                            routes_to_remove.append(route)
                
                # Remove found routes
                for route in routes_to_remove:
                    try:
                        self.app.routes.remove(route)
                        logger.info(f"Removed route {self.route_method} {self.route_path} from FastAPI app")
                    except ValueError:
                        logger.warning(f"Route {self.route_method} {self.route_path} not found in app.routes")
            
            # Reset route information
            self.app = None
            self.route_path = None
            self.route_method = None
            self.is_setup_route = False