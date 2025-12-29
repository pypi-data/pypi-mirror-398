import json
import asyncio
import argparse
from aiokafka import AIOKafkaConsumer
import google.protobuf.message
from google.protobuf import descriptor_pool
import sys
import os

# 添加项目路径以导入protobuf模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'example', 'tag-service', 'proto'))

def detect_and_parse_data(raw_data: bytes) -> tuple[str, dict | None]:
    """自动检测数据格式并解析，返回格式类型和解析后的数据"""
    try:
        # 首先尝试JSON格式
        body = json.loads(raw_data.decode("utf-8"))
        return "JSON", body
    except json.JSONDecodeError:
        pass
    
    # 尝试protobuf格式 - 尝试多种已知的protobuf消息类型
    protobuf_types = [
        "tagService.tag_pb2.Tag",
    ]
    
    for pb_type_str in protobuf_types:
        try:
            # 动态导入protobuf类型
            module_name, class_name = pb_type_str.rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            pb_class = getattr(module, class_name)
            
            # 尝试解析
            pb_obj = pb_class()
            pb_obj.ParseFromString(raw_data)
            body = protobuf_to_dict(pb_obj)
            return f"Protobuf ({pb_type_str})", body
        except Exception:
            continue
    
    # 如果都失败了，返回原始数据
    return "Unknown", {"raw_data": raw_data.hex(), "size": len(raw_data)}

def protobuf_to_dict(pb_obj: google.protobuf.message.Message) -> dict:
    """将protobuf对象转换为字典"""
    result = {}
    for field_descriptor in pb_obj.DESCRIPTOR.fields:
        field_name = field_descriptor.name
        field_value = getattr(pb_obj, field_name)
        
        if field_descriptor.label == field_descriptor.LABEL_REPEATED:
            # 处理重复字段
            result[field_name] = list(field_value)
        elif field_descriptor.type == field_descriptor.TYPE_MESSAGE:
            # 处理嵌套消息
            if field_value:
                result[field_name] = protobuf_to_dict(field_value)
        else:
            # 处理基本类型
            result[field_name] = field_value
    return result

async def consume_messages(bootstrap_servers: str, topic: str, group_id: str = "test_group", format_mode: str = "auto"):
    # TODO: proper config
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        session_timeout_ms=300000,
        heartbeat_interval_ms=10000,
        max_poll_interval_ms=3000000,
    )
    
    await consumer.start()
    try:
        print(f"🎧 开始监听 topic: {topic}, group_id: {group_id}")
        print("按 Ctrl+C 停止消费...")
        
        async for message in consumer:
            print(f"📨 收到消息:")
            print(f"  Topic: {message.topic}")
            print(f"  Partition: {message.partition}")
            print(f"  Offset: {message.offset}")
            print(f"  Timestamp: {message.timestamp}")
            print(f"  Key: {message.key}")
            
            # 根据格式模式解析数据
            if format_mode == "json":
                try:
                    parsed_data = json.loads(message.value.decode("utf-8"))
                    data_format = "JSON"
                except json.JSONDecodeError:
                    data_format = "JSON Parse Error"
                    parsed_data = {"error": "无法解析为JSON格式"}
            elif format_mode == "protobuf":
                # 尝试protobuf格式
                data_format, parsed_data = detect_and_parse_data(message.value)
                if not data_format.startswith("Protobuf"):
                    data_format = "Protobuf Parse Error"
                    parsed_data = {"error": "无法解析为Protobuf格式"}
            else:  # auto
                data_format, parsed_data = detect_and_parse_data(message.value)
            
            print(f"  Format: {data_format}")
            print(f"  Value: {json.dumps(parsed_data, indent=2, ensure_ascii=False)}")
            print("-" * 50)
            
    except KeyboardInterrupt:
        print("\n⏹️  停止消费...")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kafka Consumer Script - 支持 JSON 和 Protobuf 格式")
    parser.add_argument("--topic", type=str, default="test_topic", help="要消费的 topic 名称")
    parser.add_argument("--group-id", type=str, default="test_group", help="消费者组 ID")
    parser.add_argument("--bootstrap-servers", type=str, default="localhost:9092", help="Kafka 服务器地址")
    parser.add_argument("--format", type=str, choices=["auto", "json", "protobuf"], default="auto", 
                       help="数据格式 (auto: 自动检测, json: 仅JSON, protobuf: 仅Protobuf)")
    args = parser.parse_args()

    print(f"🚀 启动 Kafka Consumer")
    print(f"  Topic: {args.topic}")
    print(f"  Group ID: {args.group_id}")
    print(f"  Bootstrap Servers: {args.bootstrap_servers}")
    print(f"  Format: {args.format}")
    print()

    asyncio.run(consume_messages(args.bootstrap_servers, args.topic, args.group_id, args.format))
