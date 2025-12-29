import asyncio
import json
import uuid
import websockets
import requests
import threading
import time
import os
from pathlib import Path

# 用于存储客户端ID的文件路径
CLIENT_ID_FILE = Path("client_id.txt")

def save_client_id(client_id):
    """保存客户端ID到文件"""
    try:
        with open(CLIENT_ID_FILE, "w") as f:
            f.write(client_id)
        print(f"客户端ID已保存到 {CLIENT_ID_FILE}")
    except Exception as e:
        print(f"保存客户端ID失败: {e}")

def load_client_id():
    """从文件加载客户端ID"""
    try:
        if CLIENT_ID_FILE.exists():
            with open(CLIENT_ID_FILE, "r") as f:
                client_id = f.read().strip()
                if client_id:
                    print(f"从 {CLIENT_ID_FILE} 加载客户端ID: {client_id}")
                    return client_id
    except Exception as e:
        print(f"加载客户端ID失败: {e}")
    return None

def trigger_workflow(client_id):
    """发送HTTP请求触发工作流"""
    try:
        # 等待一秒，确保WebSocket连接已建立
        time.sleep(1)

        # 发送HTTP请求触发工作流
        url = f"http://localhost:8000/api/trigger?client_id={client_id}"
        print(f"发送HTTP请求到 {url}...")
        response = requests.get(url)

        if response.status_code == 200:
            print("工作流触发成功")
            print(f"响应: {response}")
        else:
            print(f"工作流触发失败，状态码: {response.status_code}")
            print(f"响应: {response}")
    except Exception as e:
        print(f"HTTP请求错误: {e}")

async def connect_without_client_id():
    """不带客户端ID连接并触发工作流"""
    # 构建WebSocket URL，不传入客户端ID
    uri = f"ws://localhost:8000/ws/connect"
    print("使用新客户端ID连接")
    print(f"正在连接到 {uri}...")

    client_id = None

    try:
        async with websockets.connect(uri) as websocket:
            print("已连接到WebSocket服务器，等待连接确认...")

            # 等待接收连接确认消息
            first_message = await websocket.recv()
            data = json.loads(first_message)
            print(f"收到消息: {json.dumps(data, indent=2)}")

            # 获取服务器分配的客户端ID
            if data.get("type") == "connection established":
                client_id = data.get("client_id")
                if client_id:
                    # 保存客户端ID到文件
                    save_client_id(client_id)
                    print(f"获得客户端ID: {client_id}")

                    # 显示恢复的订阅
                    if "restored_subscriptions" in data and data["restored_subscriptions"]:
                        print(f"已恢复以下订阅: {data['restored_subscriptions']}")

                # 启动一个线程发送HTTP请求触发工作流
                print("准备触发工作流...")
                trigger_thread = threading.Thread(target=trigger_workflow, args=(client_id,))
                trigger_thread.daemon = True
                trigger_thread.start()

            # 持续接收消息一段时间
            print("监听任务更新...")
            start_time = time.time()
            timeout = 50  # 监听5秒后断开连接

            try:
                while time.time() - start_time < timeout:
                    try:
                        # 等待消息，但设置较短的超时
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        print(f"收到更新: {json.dumps(data, indent=2)}")

                        # 根据消息类型进行不同处理
                        msg_type = data.get("type")
                        if msg_type == "execution start":
                            task_id = data.get("task_id")
                            print(f"任务 {task_id} 开始执行")
                        elif msg_type == "executing":
                            node = data.get("node")
                            print(f"节点 {node} 开始执行")
                        elif msg_type == "progress":
                            node = data.get("node")
                            progress = data.get("progress")
                            print(f"节点 {node} 执行进度: {progress*100:.1f}%")
                        elif msg_type == "executed":
                            node = data.get("node")
                            result = data.get("result")
                            if node:
                                print(f"节点 {node} 执行完成")
                                if result:
                                    print(f"结果: {result}")
                            else:
                                print("工作流执行完成")
                        elif msg_type == "execution error":
                            node = data.get("node")
                            error = data.get("error")
                            if node:
                                print(f"节点 {node} 执行出错: {error}")
                            else:
                                print(f"工作流执行出错: {error}")
                    except asyncio.TimeoutError:
                        # 短暂超时，继续循环检查总超时
                        continue

                print(f"监听超时，主动断开连接...")
            except Exception as e:
                print(f"接收消息时出错: {e}")

            return client_id

    except Exception as e:
        print(f"WebSocket连接错误: {e}")
        return None

async def reconnect_with_client_id(client_id):
    """使用已有客户端ID重连，不触发新工作流"""
    # 构建WebSocket URL，传入客户端ID
    uri = f"ws://localhost:8000/ws/connect?client_id={client_id}"
    print(f"使用已有客户端ID连接: {client_id}")
    print(f"正在连接到 {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("已连接到WebSocket服务器，等待连接确认...")

            # 等待接收连接确认消息
            first_message = await websocket.recv()
            data = json.loads(first_message)
            print(f"收到消息: {json.dumps(data, indent=2)}")

            # 获取服务器分配的客户端ID
            if data.get("type") == "connection established":
                received_client_id = data.get("client_id")
                if received_client_id == client_id:
                    print(f"成功使用客户端ID {client_id} 重新连接")

                    # 显示恢复的订阅
                    if "restored_subscriptions" in data and data["restored_subscriptions"]:
                        print(f"已恢复以下订阅: {data['restored_subscriptions']}")
                        print("订阅恢复成功！")
                    else:
                        print("没有恢复任何订阅")
                else:
                    print(f"客户端ID不匹配: 期望 {client_id}, 收到 {received_client_id}")

            # 持续接收消息，但不触发新工作流
            print("监听任务更新（不触发新工作流）...")
            async for message in websocket:
                data = json.loads(message)
                print(f"收到更新: {json.dumps(data, indent=2)}")

                # 根据消息类型进行不同处理
                msg_type = data.get("type")
                if msg_type == "execution start":
                    task_id = data.get("task_id")
                    print(f"任务 {task_id} 开始执行")
                elif msg_type == "executing":
                    node = data.get("node")
                    print(f"节点 {node} 开始执行")
                elif msg_type == "progress":
                    node = data.get("node")
                    progress = data.get("progress")
                    print(f"节点 {node} 执行进度: {progress*100:.1f}%")
                elif msg_type == "executed":
                    node = data.get("node")
                    result = data.get("result")
                    if node:
                        print(f"节点 {node} 执行完成")
                        if result:
                            print(f"结果: {result}")
                    else:
                        print("工作流执行完成")
                elif msg_type == "execution error":
                    node = data.get("node")
                    error = data.get("error")
                    if node:
                        print(f"节点 {node} 执行出错: {error}")
                    else:
                        print(f"工作流执行出错: {error}")

    except Exception as e:
        print(f"WebSocket连接错误: {e}")

async def test_disconnect_and_reconnect():
    """测试断线重连功能"""
    print("=" * 60)
    print("测试断线重连功能 - 先触发工作流，然后断联重新连接")
    print("=" * 60)

    # 第一次连接，不传入客户端ID
    print("\n第一次连接（不传入客户端ID）...")
    client_id = await connect_without_client_id()

    if not client_id:
        print("无法获取客户端ID，测试失败")
        return
    
    # 断开连接
    print("\n断开连接...")
    # await asyncio.sleep(2)


    # 第二次重连，使用已有客户端ID
    print("\n第二次重连（使用已有客户端ID，不触发新工作流）...")
    await reconnect_with_client_id(client_id)

if __name__ == "__main__":
    print("WebSocket客户端测试 - 断线重连和客户端ID持久化")
    print("此脚本将测试WebSocket连接的断线重连和客户端ID持久化功能")
    print("测试流程：第一次连接不传入ID，第二次重连使用已有ID")
    print("请确保服务已启动并运行在 http://localhost:8000")
    print()

    # 选择测试模式
    print("请选择测试模式:")
    print("1. 正常连接测试（不传入ID）")
    print("2. 断线重连测试（先不传入ID连接，再使用已有ID重连）")

    choice = input("请输入选项 (1 或 2): ").strip()

    if choice == "2":
        asyncio.run(test_disconnect_and_reconnect())
    else:
        asyncio.run(connect_without_client_id())
