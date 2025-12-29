from __future__ import annotations
import uuid
import asyncio
import json
from loguru import logger
from service_forge.workflow.trigger import Trigger
from typing import AsyncIterator, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from service_forge.workflow.port import Port
from google.protobuf.message import Message
from google.protobuf.json_format import MessageToJson

class WebSocketAPITrigger(Trigger):
    DEFAULT_INPUT_PORTS = [
        Port("app", FastAPI),
        Port("path", str),
        Port("data_type", type),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("trigger", bool),
        Port("data", Any),
    ]

    def __init__(self, name: str):
        super().__init__(name)
        self.events = {}
        self.is_setup_websocket = False

    @staticmethod
    def serialize_result(result: Any):
        if isinstance(result, Message):
            return MessageToJson(
                result,
                preserving_proto_field_name=True
            )
        return result

    async def handle_stream_output(
        self,
        websocket: WebSocket,
        task_id: uuid.UUID,
    ):
        try:
            while True:
                item = await self.stream_queues[task_id].get()

                if item.is_error:
                    error_response = {
                        "type": "stream_error",
                        "task_id": str(task_id),
                        "detail": str(item.result)
                    }
                    await websocket.send_text(json.dumps(error_response))
                    break
                
                if item.is_end:
                    # Stream ended, send final result if available
                    if item.result is not None:
                        serialized = self.serialize_result(item.result)
                        if isinstance(serialized, str):
                            try:
                                data = json.loads(serialized)
                            except json.JSONDecodeError:
                                data = serialized
                        else:
                            data = serialized
                        
                        end_response = {
                            "type": "stream_end",
                            "task_id": str(task_id),
                            "data": data
                        }
                    else:
                        end_response = {
                            "type": "stream_end",
                            "task_id": str(task_id)
                        }
                    await websocket.send_text(json.dumps(end_response))
                    break

                # Send stream data
                serialized = self.serialize_result(item.result)
                if isinstance(serialized, str):
                    try:
                        data = json.loads(serialized)
                    except json.JSONDecodeError:
                        data = serialized
                else:
                    data = serialized
                
                stream_response = {
                    "type": "stream",
                    "task_id": str(task_id),
                    "data": data
                }
                await websocket.send_text(json.dumps(stream_response))
        except Exception as e:
            logger.error(f"Error handling stream output for task {task_id}: {e}")
            error_response = {
                "type": "stream_error",
                "task_id": str(task_id),
                "detail": str(e)
            }
            try:
                await websocket.send_text(json.dumps(error_response))
            except Exception:
                pass
        finally:
            if task_id in self.stream_queues:
                del self.stream_queues[task_id]

    async def handle_websocket_message(
        self,
        websocket: WebSocket,
        data_type: type,
        message_data: dict,
    ):
        task_id = uuid.uuid4()
        self.result_queues[task_id] = asyncio.Queue()
        self.stream_queues[task_id] = asyncio.Queue()

        if data_type is Any:
            converted_data = message_data
        else:
            try:
                # TODO: message_data is Message, need to convert to dict
                converted_data = data_type(**message_data)
            except Exception as e:
                error_msg = {"error": f"Failed to convert data: {str(e)}"}
                await websocket.send_text(json.dumps(error_msg))
                return

        # Always start background task to handle stream output
        asyncio.create_task(self.handle_stream_output(websocket, task_id))

        self.trigger_queue.put_nowait({
            "id": task_id,
            "data": converted_data,
        })

        # The stream handler will send all messages including stream_end when workflow completes

    def _setup_websocket(self, app: FastAPI, path: str, data_type: type) -> None:
        async def websocket_handler(websocket: WebSocket):
            await websocket.accept()
            
            try:
                while True:
                    data = await websocket.receive()
                    try:
                        # message = json.loads(data)
                        # Handle the message and trigger workflow
                        await self.handle_websocket_message(
                            websocket,
                            data_type,
                            data
                        )
                    except json.JSONDecodeError:
                        error_msg = {"error": "Invalid JSON format"}
                        await websocket.send_text(json.dumps(error_msg))
                    except Exception as e:
                        logger.error(f"Error handling websocket message: {e}")
                        error_msg = {"error": str(e)}
                        await websocket.send_text(json.dumps(error_msg))
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")

        app.websocket(path)(websocket_handler)

    async def _run(self, app: FastAPI, path: str, data_type: type) -> AsyncIterator[bool]:
        if not self.is_setup_websocket:
            self._setup_websocket(app, path, data_type)
            self.is_setup_websocket = True

        while True:
            try:
                trigger = await self.trigger_queue.get()
                self.prepare_output_edges(self.get_output_port_by_name('data'), trigger['data'])
                yield self.trigger(trigger['id'])
            except Exception as e:
                logger.error(f"Error in WebSocketAPITrigger._run: {e}")
                continue

    async def _stop(self) -> AsyncIterator[bool]:
        pass