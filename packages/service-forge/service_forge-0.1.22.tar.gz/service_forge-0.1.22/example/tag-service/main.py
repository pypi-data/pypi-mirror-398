import os
import asyncio
from dotenv import load_dotenv
from loguru import logger

from service_forge.service import Service
from service_forge.sft.config.sf_metadata import load_metadata
from proto.topics import TAG_REQUEST, TAG_RESPONSE
from proto.entryService.record_pb2 import Record
from proto.tagService.tag_pb2 import Tag

from model.http.test_sse_model import TestSSEModel
from model.http.query_tags_model import QueryTagsModel
from model.http.create_tag_model import CreateTagModel
from model.http.update_tag_model import UpdateTagModel
from model.http.delete_tag_model import DeleteTagModel

from nodes import *

async def main():
    metadata = load_metadata("./sf-meta.yaml")
    service = Service.from_config(
        metadata,
        service_env={
            'INPUT_TOPIC': TAG_REQUEST,
            'INPUT_TOPIC_TYPE': Record,
            'OUTPUT_TOPIC': TAG_RESPONSE,
            'OUTPUT_TOPIC_TYPE': Tag,
            'KAFKA_GROUP_ID': os.getenv('KAFKA_GROUP_ID'),
            'QUERY_TAGS_MODEL': QueryTagsModel,
            'CREATE_TAGS_MODEL': CreateTagModel,
            'UPDATE_TAG_MODEL': UpdateTagModel,
            'DELETE_TAG_MODEL': DeleteTagModel,
            'GET_TAGS_MODEL': Record,
            'TEST_SSE_MODEL': TestSSEModel,
        }
    )
    await service.start()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
