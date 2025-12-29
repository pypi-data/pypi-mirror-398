from __future__ import annotations
from loguru import logger
from service_forge.workflow.trigger import Trigger
from typing import AsyncIterator, Any
from service_forge.workflow.port import Port
from google.protobuf.message import Message
from google.protobuf.json_format import MessageToJson
from fastapi import FastAPI
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.utils.constants import DEFAULT_RPC_URL, EXTENDED_AGENT_CARD_PATH, AGENT_CARD_WELL_KNOWN_PATH

import json
import uuid
import asyncio
from service_forge.workflow.workflow_event import WorkflowResult

class A2AAgentExecutor(AgentExecutor):
    def __init__(self, trigger: A2AAPITrigger):
        self.trigger = trigger

    @staticmethod
    def serialize_result(result: Any) -> str:
        if isinstance(result, Message):
            return MessageToJson(
                result,
                preserving_proto_field_name=True
            )
        return json.dumps(result)

    async def send_event(self, event_queue: EventQueue, item: WorkflowResult) -> None:
        if item.is_error:
            result = {
                'event': 'error',
                'detail': str(item.result)
            }
            await event_queue.enqueue_event(new_agent_text_message(json.dumps(result)))

        if item.is_end:
            result = {
                'event': 'end',
                'detail': self.serialize_result(item.result)
            }
            await event_queue.enqueue_event(new_agent_text_message(json.dumps(result)))

        result = {
            'event': 'data',
            'data': self.serialize_result(item.result)
        }
        await event_queue.enqueue_event(new_agent_text_message(json.dumps(result)))

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task_id = uuid.uuid4()
        self.trigger.result_queues[task_id] = asyncio.Queue()

        self.trigger.trigger_queue.put_nowait({
            'id': task_id,
            'context': context,
        })

        # TODO: support stream output
        if False:
            self.trigger.stream_queues[task_id] = asyncio.Queue()
            while True:
                item = await self.trigger.stream_queues[task_id].get()
                await self.send_event(event_queue, item)

                if item.is_error or item.is_end:
                    break

            if task_id in self.trigger.stream_queues:
                del self.trigger.stream_queues[task_id]
        else:
            result = await self.trigger.result_queues[task_id].get()
            await self.send_event(event_queue, result)

        if task_id in self.trigger.result_queues:
            del self.trigger.result_queues[task_id]

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')


class A2AAPITrigger(Trigger):
    DEFAULT_INPUT_PORTS = [
        Port("app", FastAPI),
        Port("path", str),
        Port("skill_id", str, is_extended=True),
        Port("skill_name", str, is_extended=True),
        Port("skill_description", str, is_extended=True),
        Port("skill_tags", list[str], is_extended=True),
        Port("skill_examples", list[str], is_extended=True),
        Port("agent_name", str),
        Port("agent_url", str),
        Port("agent_description", str),
        Port("agent_version", str),
    ]

    DEFAULT_OUTPUT_PORTS = [
        Port("trigger", bool),
        Port("context", RequestContext),
    ]

    def __init__(self, name: str):
        super().__init__(name)
        self.events = {}
        self.is_setup_handler = False
        self.agent_card: AgentCard | None = None

    @staticmethod
    def serialize_result(result: Any):
        if isinstance(result, Message):
            return MessageToJson(
                result,
                preserving_proto_field_name=True
            )
        return result

    def _setup_handler(
        self,
        app: FastAPI,
        path: str,
        skill_id: list[tuple[int, str]],
        skill_name: list[tuple[int, str]],
        skill_description: list[tuple[int, str]],
        skill_tags: list[tuple[int, list[str]]],
        skill_examples: list[tuple[int, list[str]]],
        agent_name: str,
        agent_url: str,
        agent_description: str,
        agent_version: str,
    ) -> None:
    
        skills_config = []
        for i in range(len(skill_id)):
            skills_config.append({
                'id': '',
                'name': '',
                'description': '',
                'tags': [],
                'examples': [],
            })

        for i in range(len(skill_id)):
            skills_config[skill_id[i][0]]['id'] = skill_id[i][1]
            skills_config[skill_name[i][0]]['name'] = skill_name[i][1]
            skills_config[skill_description[i][0]]['description'] = skill_description[i][1]
            skills_config[skill_tags[i][0]]['tags'] = skill_tags[i][1]
            skills_config[skill_examples[i][0]]['examples'] = skill_examples[i][1]
    
        skills = []
        for config in skills_config:
            skills.append(AgentSkill(
                id=config['id'],
                name=config['name'],
                description=config['description'],
                tags=config['tags'],
                examples=config['examples'],
            ))

        agent_card = AgentCard(
            name=agent_name,
            description=agent_description,
            url=agent_url,
            version=agent_version,
            default_input_modes=['text'],
            default_output_modes=['text'],
            capabilities=AgentCapabilities(streaming=True),
            skills=skills,
            supports_authenticated_extended_card=False,
        )
        
        self.agent_card = agent_card

        request_handler = DefaultRequestHandler(
            agent_executor=A2AAgentExecutor(self),
            task_store=InMemoryTaskStore(),
        )

        try:
            server = A2AStarletteApplication(
                agent_card=agent_card,
                http_handler=request_handler,
            )
            
            server.add_routes_to_app(
                app,
                agent_card_url="/a2a" + path + AGENT_CARD_WELL_KNOWN_PATH,
                rpc_url="/a2a" + path + DEFAULT_RPC_URL,
                extended_agent_card_url="/a2a" + path + EXTENDED_AGENT_CARD_PATH,
            )

        except Exception as e:
            logger.error(f"Error adding A2A routes: {e}")
            raise

    async def _run(
        self,
        app: FastAPI,
        path: str,
        skill_id: list[tuple[int, str]],
        skill_name: list[tuple[int, str]],
        skill_description: list[tuple[int, str]],
        skill_tags: list[tuple[int, list[str]]],
        skill_examples: list[tuple[int, list[str]]],
        agent_name: str,
        agent_url: str,
        agent_description: str,
        agent_version: str,
    ) -> AsyncIterator[bool]:
        if len(skill_id) != len(skill_name) or len(skill_id) != len(skill_description) or len(skill_id) != len(skill_tags) or len(skill_id) != len(skill_examples):
            raise ValueError("skill_id, skill_name, skill_description, skill_tags, skill_examples must have the same length")

        if not self.is_setup_handler:
            self._setup_handler(
                app,
                path,
                skill_id,
                skill_name,
                skill_description,
                skill_tags,
                skill_examples,
                agent_name,
                agent_url,
                agent_description,
                agent_version,
            )
            self.is_setup_handler = True

        logger.info(f"A2A Trigger {self.name} is running")

        while True:
            try:
                trigger = await self.trigger_queue.get()
                self.prepare_output_edges('context', trigger['context'])
                yield self.trigger(trigger['id'])
            except Exception as e:
                logger.error(f"Error in A2AAPITrigger._run: {e}")
                continue

    async def _stop(self) -> AsyncIterator[bool]:
        pass
