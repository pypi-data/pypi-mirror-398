#!/usr/bin/env python3
"""
测试 SDK WebSocket 接口的脚本
服务运行在 0.0.0.0:37200 端口上
"""

import asyncio
import json
import uuid
import websockets
from typing import Optional


class SDKWebSocketClient:
    """SDK WebSocket 客户端测试类"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 37200):
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}/sdk/ws"
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.subscribed_tasks: set = set()
    
    async def connect(self):
        """连接到 WebSocket 服务器"""
        print(f"正在连接到 {self.uri}...")
        try:
            self.websocket = await websockets.connect(self.uri)
            print("✓ 已成功连接到 WebSocket 服务器")
            return True
        except Exception as e:
            print(f"✗ 连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            print("已断开连接")
    
    async def subscribe(self, task_id: str) -> bool:
        """订阅指定的 task_id，支持 'all' 来订阅所有任务"""
        if not self.websocket:
            print("✗ 未连接到服务器")
            return False
        
        # 允许 task_id 为 "all" 来订阅所有任务
        if task_id.lower() != "all":
            try:
                # 验证 task_id 格式（如果不是 "all"）
                uuid.UUID(task_id)
            except ValueError:
                print(f"✗ 无效的 task_id 格式: {task_id} (必须是有效的 UUID 或 'all')")
                return False
        
        message = {
            "type": "subscribe",
            "task_id": task_id
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print(f"✓ 已发送订阅请求: task_id={task_id}")
            
            # 等待响应
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "subscribe_response" and data.get("success"):
                self.subscribed_tasks.add(task_id)
                print(f"✓ 订阅成功: task_id={task_id}")
                return True
            else:
                print(f"✗ 订阅失败: {data}")
                return False
        except Exception as e:
            print(f"✗ 订阅时出错: {e}")
            return False
    
    async def unsubscribe(self, task_id: str) -> bool:
        """取消订阅指定的 task_id，支持 'all' 来取消订阅所有任务"""
        if not self.websocket:
            print("✗ 未连接到服务器")
            return False
        
        message = {
            "type": "unsubscribe",
            "task_id": task_id
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print(f"✓ 已发送取消订阅请求: task_id={task_id}")
            
            # 等待响应
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "unsubscribe_response" and data.get("success"):
                self.subscribed_tasks.discard(task_id)
                print(f"✓ 取消订阅成功: task_id={task_id}")
                return True
            else:
                print(f"✗ 取消订阅失败: {data}")
                return False
        except Exception as e:
            print(f"✗ 取消订阅时出错: {e}")
            return False
    
    async def listen(self, timeout: float = 30.0):
        """监听消息"""
        if not self.websocket:
            print("✗ 未连接到服务器")
            return
        
        print(f"\n开始监听消息 (超时: {timeout}秒)...")
        print("=" * 60)
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            while True:
                # 检查超时
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    print(f"\n监听超时 ({timeout}秒)，停止监听")
                    break
                
                try:
                    # 设置较短的超时以便检查总超时
                    remaining_timeout = timeout - elapsed
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=min(remaining_timeout, 1.0)
                    )
                    
                    data = json.loads(message)
                    await self._handle_message(data)
                    
                except asyncio.TimeoutError:
                    # 短暂超时，继续循环检查总超时
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("\n连接已关闭")
                    break
                    
        except KeyboardInterrupt:
            print("\n用户中断，停止监听")
        except Exception as e:
            print(f"\n监听消息时出错: {e}")
    
    async def _handle_message(self, data: dict):
        """处理接收到的消息"""
        msg_type = data.get("type")
        task_id = data.get("task_id", "unknown")
        
        print(f"\n收到消息:")
        print(f"  类型: {msg_type}")
        print(f"  任务ID: {task_id}")
        
        if msg_type == "workflow_end":
            result = data.get("result")
            print(f"  工作流执行完成")
            print(f"  结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
        elif msg_type == "workflow_error":
            error = data.get("error")
            print(f"  工作流执行出错")
            print(f"  错误: {json.dumps(error, indent=2, ensure_ascii=False)}")
            
        elif msg_type == "node_stream_output":
            node = data.get("node", "unknown")
            output = data.get("output")
            print(f"  节点流式输出")
            print(f"  节点: {node}")
            print(f"  输出: {json.dumps(output, indent=2, ensure_ascii=False)}")
            
        elif msg_type == "subscribe_response":
            success = data.get("success")
            print(f"  订阅响应: {'成功' if success else '失败'}")
            
        elif msg_type == "unsubscribe_response":
            success = data.get("success")
            print(f"  取消订阅响应: {'成功' if success else '失败'}")
            
        elif msg_type == "error":
            error_msg = data.get("error", "未知错误")
            print(f"  错误: {error_msg}")
            
        else:
            print(f"  完整消息: {json.dumps(data, indent=2, ensure_ascii=False)}")


async def test_basic_connection():
    """测试基本连接功能"""
    print("=" * 60)
    print("测试 1: 基本连接测试")
    print("=" * 60)
    
    client = SDKWebSocketClient()
    
    if await client.connect():
        await asyncio.sleep(1)
        await client.disconnect()
        print("✓ 基本连接测试通过\n")
    else:
        print("✗ 基本连接测试失败\n")


async def test_subscribe_unsubscribe():
    """测试订阅和取消订阅功能"""
    print("=" * 60)
    print("测试 2: 订阅和取消订阅测试")
    print("=" * 60)
    
    client = SDKWebSocketClient()
    
    if not await client.connect():
        print("✗ 连接失败，跳过测试\n")
        return
    
    # 生成测试用的 task_id
    test_task_id = str(uuid.uuid4())
    print(f"使用测试 task_id: {test_task_id}\n")
    
    # 测试订阅
    if await client.subscribe(test_task_id):
        print()
        
        # 测试取消订阅
        await asyncio.sleep(1)
        await client.unsubscribe(test_task_id)
    
    await client.disconnect()
    print("\n✓ 订阅和取消订阅测试完成\n")


async def test_listen_messages():
    """测试监听消息功能"""
    print("=" * 60)
    print("测试 3: 监听消息测试")
    print("=" * 60)
    print("此测试将订阅一个 task_id 并监听消息")
    print("如果服务端有对应的 workflow 执行，将收到消息")
    print()
    
    client = SDKWebSocketClient()
    
    if not await client.connect():
        print("✗ 连接失败，跳过测试\n")
        return
    
    # 让用户输入 task_id，或使用随机生成的
    print("请输入要订阅的 task_id (直接回车将使用随机生成的 UUID，或输入 'all' 订阅所有任务):")
    task_id_input = input().strip()
    
    if task_id_input:
        if task_id_input.lower() == "all":
            task_id = "all"
        else:
            try:
                uuid.UUID(task_id_input)  # 验证格式
                task_id = task_id_input
            except ValueError:
                print(f"✗ 无效的 task_id 格式，使用随机生成的 UUID")
                task_id = str(uuid.uuid4())
    else:
        task_id = str(uuid.uuid4())
    
    print(f"\n使用 task_id: {task_id}\n")
    
    # 订阅
    if await client.subscribe(task_id):
        print("\n开始监听消息...")
        print("提示: 如果服务端有对应的 workflow 执行，将收到消息")
        print("按 Ctrl+C 可以停止监听\n")
        
        # 监听消息（30秒超时）
        await client.listen(timeout=30.0)
    
    await client.disconnect()
    print("\n✓ 监听消息测试完成\n")


async def interactive_mode():
    """交互式测试模式"""
    print("=" * 60)
    print("交互式测试模式")
    print("=" * 60)
    print("可用命令:")
    print("  subscribe <task_id>  - 订阅任务 (task_id 可以是 UUID 或 'all' 来订阅所有任务)")
    print("  unsubscribe <task_id> - 取消订阅任务 (task_id 可以是 UUID 或 'all')")
    print("  listen [timeout]     - 监听消息（可选超时时间，默认30秒）")
    print("  list                 - 显示已订阅的任务")
    print("  quit                 - 退出")
    print()
    
    client = SDKWebSocketClient()
    
    if not await client.connect():
        print("✗ 连接失败")
        return
    
    # 启动后台监听任务，持续接收消息
    listen_task = None
    should_listen = True
    
    async def background_listen():
        """后台持续监听消息"""
        while should_listen and client.websocket:
            try:
                # 使用较短的超时，以便能够响应 should_listen 的变化
                message = await asyncio.wait_for(
                    client.websocket.recv(),
                    timeout=1.0
                )
                data = json.loads(message)
                await client._handle_message(data)
            except asyncio.TimeoutError:
                # 超时继续循环
                continue
            except websockets.exceptions.ConnectionClosed:
                print("\n连接已关闭")
                break
            except Exception as e:
                if should_listen:  # 只在应该监听时打印错误
                    print(f"\n监听消息时出错: {e}")
    
    # 启动后台监听
    listen_task = asyncio.create_task(background_listen())
    
    try:
        # 使用 run_in_executor 在单独的线程中运行 input，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # 在单独的线程中运行 input，避免阻塞事件循环
                command = await loop.run_in_executor(None, input, "> ")
                command = command.strip().split()
                
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd == "quit" or cmd == "exit":
                    break
                
                elif cmd == "subscribe":
                    if len(command) < 2:
                        print("✗ 用法: subscribe <task_id>")
                        continue
                    task_id = command[1]
                    await client.subscribe(task_id)
                
                elif cmd == "unsubscribe":
                    if len(command) < 2:
                        print("✗ 用法: unsubscribe <task_id>")
                        continue
                    task_id = command[1]
                    await client.unsubscribe(task_id)
                
                elif cmd == "listen":
                    timeout = float(command[1]) if len(command) > 1 else 30.0
                    # 在后台监听，不阻塞输入
                    asyncio.create_task(client.listen(timeout))
                
                elif cmd == "list":
                    if client.subscribed_tasks:
                        print("已订阅的任务:")
                        for task_id in client.subscribed_tasks:
                            print(f"  - {task_id}")
                    else:
                        print("没有已订阅的任务")
                
                else:
                    print(f"✗ 未知命令: {cmd}")
                    print("可用命令: subscribe, unsubscribe, listen, list, quit")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"✗ 错误: {e}")
    
    finally:
        should_listen = False
        if listen_task:
            listen_task.cancel()
            try:
                await listen_task
            except asyncio.CancelledError:
                pass
        await client.disconnect()
        print("\n已断开连接")


async def main():
    """主函数"""
    print("=" * 60)
    print("SDK WebSocket 接口测试脚本")
    print("=" * 60)
    print(f"服务地址: ws://0.0.0.0:37200/sdk/ws")
    print()
    
    print("请选择测试模式:")
    print("1. 基本连接测试")
    print("2. 订阅和取消订阅测试")
    print("3. 监听消息测试")
    print("4. 交互式测试模式")
    print()
    
    try:
        choice = input("请输入选项 (1-4): ").strip()
        
        if choice == "1":
            await test_basic_connection()
        elif choice == "2":
            await test_subscribe_unsubscribe()
        elif choice == "3":
            await test_listen_messages()
        elif choice == "4":
            await interactive_mode()
        else:
            print("✗ 无效的选项")
    
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

