import json
import asyncio
import argparse
from aiokafka import AIOKafkaProducer
import sys
import os

# 添加proto模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'example', 'tag-service', 'proto'))
from entryService import record_pb2

async def send_message(bootstrap_servers: str, topic: str, record: record_pb2.Record):
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: v.SerializeToString(),
    )
    await producer.start()
    try:
        await producer.send_and_wait(topic, record)
        print(f"✅ 已发送protobuf Record到 {topic}: {record}")
    finally:
        await producer.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default="tag.request")
    parser.add_argument("--text", type=str, default="我明天早上有个会议")
    args = parser.parse_args()

    # 创建Record实例
    record = record_pb2.Record(
        proto_id="123",
        id=34,
        name="example name",
        text=args.text,
        type="example type",
        user_id=58,
        group_id=10,
        file_id="example file id",
        is_recognized=True,
        is_deleted=False,
        timestamp="2021-01-01 00:00:00",
        role="user",
        is_stream=True,
        is_stream_done=False,
        force_reply=False,
        tags=[],
        status="",
    )

    asyncio.run(send_message("localhost:9092", args.topic, record))
