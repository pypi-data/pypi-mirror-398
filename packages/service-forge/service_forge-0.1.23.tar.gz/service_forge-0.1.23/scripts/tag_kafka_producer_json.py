import json
import asyncio
import argparse
from aiokafka import AIOKafkaProducer

async def send_message(bootstrap_servers: str, topic: str, message: dict):
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()
    try:
        await producer.send_and_wait(topic, message)
        print(f"✅ 已发送到 {topic}: {message}")
    finally:
        await producer.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default="tag.request")
    parser.add_argument("--message", type=str, default="kafka message!")
    args = parser.parse_args()

    asyncio.run(send_message("localhost:9092", args.topic, {
        "proto_id": "123",
        "id": 34,
        "name": "example name",
        "text": "我明天早上八点有个会议",
        "type": "example type",
        "user_id": 58,
        "group_id": 10,
        "file_id": "example file id",
        "is_recognized": True,
        "is_deleted": False,
        "timestamp": "2021-01-01 00:00:00",
        "role": "user",
        "is_stream": True,
        "is_stream_done": False,
        "force_reply": False,
        "tags": [],
        "status": "",
    }))
