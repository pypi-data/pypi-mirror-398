#!/usr/bin/env python3
"""
WebSocket客户端脚本，用于调用 test_websocket_workflow
"""
import asyncio
import json
import websockets
from typing import Optional
import sys


async def call_websocket_workflow(
    url: str = "ws://localhost:37200/test_websocket",
    message: str = "Hello, WebSocket!"
):
    """
    调用 WebSocket 工作流（默认流式模式）
    
    Args:
        url: WebSocket 服务器地址
        message: 要发送的消息内容
    """
    try:
        print(f"正在连接到 WebSocket 服务器: {url}")
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket 连接已建立")
            
            # 准备要发送的数据（符合 TestSSEModel 格式）
            data = {
                "message": message
            }
            
            # 发送第一条消息
            message_json = json.dumps(data)
            print(f"\n📤 发送第一条消息: {message_json}")
            print("📡 流式模式（默认）")
            await websocket.send(message_json)
            
            # 等待0.5秒后发送第二条消息
            await asyncio.sleep(0.5)
            
            # 发送第二条消息
            data2 = {
                "message": f"{message} (消息2)"
            }
            message_json2 = json.dumps(data2)
            print(f"\n📤 发送第二条消息: {message_json2}")
            await websocket.send(message_json2)
            
            # 流式模式：持续接收消息直到收到 stream_end
            print("\n⏳ 等待流式响应...")
            task_responses = {}  # 用于跟踪不同任务的响应
            
            while True:
                response = await websocket.recv()
                try:
                    response_data = json.loads(response)
                    msg_type = response_data.get("type")
                    task_id = response_data.get("task_id", "unknown")
                    
                    # 初始化任务响应缓冲区
                    if task_id not in task_responses:
                        task_responses[task_id] = []
                    
                    if msg_type == "stream":
                        # 接收流式数据
                        stream_data = response_data.get("data", "")
                        task_responses[task_id].append(str(stream_data))
                        print(f"📥 [任务 {task_id[:8]}...] [流式数据] {stream_data}", end="", flush=True)
                        
                    elif msg_type == "stream_end":
                        # 流式结束
                        print(f"\n\n✅ 任务 {task_id[:8]}... 流式传输完成!")
                        if response_data.get("data") is not None:
                            print(f"最终结果: {response_data.get('data')}")
                        if task_responses[task_id]:
                            complete_message = ''.join(task_responses[task_id])
                            print(f"完整流式消息: {complete_message}")
                        # 移除已完成的任务
                        del task_responses[task_id]
                        # 如果所有任务都完成了，退出循环
                        if not task_responses:
                            break
                        
                    elif msg_type == "stream_error":
                        # 流式错误
                        print(f"\n\n❌ 任务 {task_id[:8]}... 流式传输出错!")
                        print(f"错误详情: {response_data.get('detail')}")
                        # 移除出错的任务
                        if task_id in task_responses:
                            del task_responses[task_id]
                        # 如果所有任务都完成了，退出循环
                        if not task_responses:
                            break
                        
                    else:
                        print(f"\n📥 [任务 {task_id[:8]}...] 收到响应: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                        if msg_type in ["error"]:
                            if task_id in task_responses:
                                del task_responses[task_id]
                            if not task_responses:
                                break
                            
                except json.JSONDecodeError:
                    print(f"\n📥 收到非JSON响应: {response}")
                    break
                
    except websockets.exceptions.ConnectionClosed:
        print("\n❌ WebSocket 连接已关闭")
    except websockets.exceptions.InvalidURI:
        print(f"\n❌ 无效的 WebSocket URL: {url}")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="WebSocket客户端，用于调用 test_websocket_workflow"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="ws://localhost:37200/test_websocket",
        help="WebSocket 服务器地址 (默认: ws://localhost:37200/test_websocket)"
    )
    parser.add_argument(
        "--message",
        type=str,
        default="Hello, WebSocket!",
        help="要发送的消息内容 (默认: Hello, WebSocket!)"
    )
    
    args = parser.parse_args()
    
    await call_websocket_workflow(url=args.url, message=args.message)


if __name__ == "__main__":
    asyncio.run(main())

