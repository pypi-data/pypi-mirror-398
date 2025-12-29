import asyncio
from service_forge.api.kafka_api import KafkaApp
from pydantic import BaseModel

class FooInput(BaseModel):
    user_id: int
    data: str

app = KafkaApp("localhost:9092")

@app.kafka_input("test_topic")
async def handle_message(input: FooInput, metadata: dict):
    print(f"Received message: {input}, metadata: {metadata}")

if __name__ == "__main__":
    asyncio.run(app.start())
