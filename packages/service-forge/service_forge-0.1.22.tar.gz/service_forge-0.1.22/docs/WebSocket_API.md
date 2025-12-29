# WebSocket API 文档

本文档描述了Service Forge中客户端和服务器通过WebSocket进行交互的接口规范，包括消息格式、连接方式和使用方法。

## 目录

- [概述](#概述)
- [连接方式](#连接方式)
- [消息格式](#消息格式)
- [消息类型](#消息类型)
  - [连接确认消息](#1-连接确认消息)
  - [订阅消息](#2-订阅消息)
  - [取消订阅消息](#3-取消订阅消息)
  - [执行开始消息](#4-执行开始消息)
  - [节点开始执行消息](#5-节点开始执行消息)
  - [节点进度更新消息](#6-节点进度更新消息)
  - [节点执行完成消息](#7-节点执行完成消息)
  - [节点输出结果消息](#71-节点输出结果消息)
  - [执行错误消息](#8-执行错误消息)
  - [任务状态消息](#9-任务状态消息)
  - [触发工作流](#10-触发工作流)
- [客户端示例](#客户端示例)
- [错误处理](#错误处理)
- [客户端ID持久化](#客户端id持久化)

## 概述

Service Forge通过WebSocket提供实时工作流执行状态更新，使客户端能够实时监控工作流中各个节点的执行情况。客户端可以订阅特定任务，接收任务执行过程中的各种状态更新。

### 消息传递机制

Service Forge的WebSocket API采用基于客户端ID的消息传递机制：

1. **客户端ID持久化**：客户端可以使用之前保存的客户端ID重新连接，服务器会恢复该客户端之前的订阅信息。

2. **任务与客户端关联**：当通过HTTP请求触发工作流时，服务器会自动将任务与触发该任务的客户端ID关联起来。

3. **定向消息传递**：所有与任务相关的消息（包括`execution start`、`executing`、`progress`、`executed`和`execution error`）只发送给触发该任务的客户端，而不是广播给所有客户端。

4. **订阅恢复**：当客户端使用之前保存的ID重新连接时，服务器会自动恢复该客户端之前的订阅关系，无需客户端重新订阅。

5. **任务队列管理**：服务器维护全局任务队列和客户端任务列表，提供详细的任务状态和队列位置信息。

这种设计的好处是：
- 减少不必要的网络流量，只向相关客户端发送消息
- 支持客户端断线重连后自动恢复订阅
- 提高安全性，确保客户端只能看到自己触发的任务状态
- 支持多客户端并发执行不同任务，互不干扰
- 提供详细的任务队列信息，便于客户端了解任务执行进度

### 任务执行流程

典型的任务执行流程如下：
1. 客户端连接到WebSocket服务器，可以使用之前保存的客户端ID或获取新ID
2. 如果使用之前的ID，服务器会自动恢复该客户端之前的订阅
3. 客户端使用获得的客户端ID发送HTTP请求触发工作流
4. 服务器创建任务，并将任务与客户端ID关联
5. 服务器自动向该客户端发送所有任务相关的消息，无需客户端订阅
6. 消息中包含详细的任务队列信息和客户端任务列表

**重要提示**：
- 客户端可以保存客户端ID到本地存储，以便在重连时使用
- 服务器会自动恢复客户端之前的订阅关系
- 一个客户端可以同时触发多个任务，并接收所有任务的状态更新
- 不同客户端触发的任务互不干扰，各自只能看到自己触发的任务状态
- 每个状态消息都包含全局队列信息和客户端任务列表，便于客户端了解整体执行情况

## 连接方式

### 连接端点

```
ws://<服务器地址>:<端口>/ws/connect?client_id=<客户端ID>
```

- `<服务器地址>`: 服务器的IP地址或域名
- `<端口>`: 服务器监听的端口（默认为8000）
- `<客户端ID>`: 可选参数，如果提供，服务器会尝试使用该ID恢复之前的订阅

**注意**：客户端ID是可选的，如果不提供，服务器会生成一个新的唯一客户端ID，并在连接确认消息中返回给客户端。

### 连接示例

```javascript
// 使用已有客户端ID连接
const clientId = localStorage.getItem('websocket_client_id') || null;
const wsUrl = clientId ? 
    `ws://localhost:8000/ws/connect?client_id=${clientId}` : 
    "ws://localhost:8000/ws/connect";

const ws = new WebSocket(wsUrl);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "connection established") {
        // 保存服务器分配的客户端ID
        const clientId = data.client_id;
        localStorage.setItem('websocket_client_id', clientId);
        console.log(`连接成功，客户端ID: ${clientId}`);

        // 显示恢复的订阅
        if (data.restored_subscriptions && data.restored_subscriptions.length > 0) {
            console.log("已恢复以下订阅:", data.restored_subscriptions);
        }
    }
    // 处理其他消息...
};
```

## 消息格式

所有WebSocket消息都使用JSON格式，具有以下基本结构：

```json
{
  "type": "消息类型",
  "task_id": "任务ID（可选）",
  "timestamp": "时间戳（可选）",
  // 其他字段根据消息类型而定
}
```

## 消息类型

### 1. 连接确认消息

服务器在客户端连接成功后发送此消息，包含服务器分配的客户端ID和恢复的订阅信息。

```json
{
  "type": "connection established",
  "client_id": "client_abc123def456",
  "timestamp": "2023-11-15T10:29:55Z",
  "restored_subscriptions": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

### 2. 订阅消息

客户端发送此消息以订阅特定任务的更新。

```json
{
  "type": "subscribe",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

服务器响应：

```json
{
  "success": true
}
```

### 3. 取消订阅消息

客户端发送此消息以取消订阅特定任务的更新。

```json
{
  "type": "unsubscribe",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

服务器响应：

```json
{
  "success": true
}
```

### 4. 执行开始消息

服务器在任务开始执行时发送此消息，包含任务队列信息和客户端任务列表。

```json
{
  "type": "execution start",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_tasks": {
    "total": 2,
    "tasks": [
      {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "workflow_name": "example_workflow",
        "status": "running",
        "created_at": "2023-11-15T10:30:00Z",
        "started_at": "2023-11-15T10:30:05Z",
        "steps": 3,
        "current_step": 1
      }
    ]
  },
  "global_queue": {
    "total": 5,
    "waiting": 4,
    "running": 1
  },
  "queue_position": -1
}
```

### 5. 节点开始执行消息

服务器在节点开始执行时发送此消息，包含任务队列信息和客户端任务列表。

```json
{
  "type": "executing",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "node": "task1",
  "client_tasks": {
    "total": 2,
    "tasks": [
      {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "workflow_name": "example_workflow",
        "status": "running",
        "created_at": "2023-11-15T10:30:00Z",
        "started_at": "2023-11-15T10:30:05Z",
        "steps": 3,
        "current_step": 1
      }
    ]
  },
  "global_queue": {
    "total": 5,
    "waiting": 4,
    "running": 1
  },
  "queue_position": -1
}
```

### 6. 节点进度更新消息

服务器在节点执行过程中定期发送此消息，用于更新执行进度，包含任务队列信息和客户端任务列表。

```json
{
  "type": "progress",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "node": "task1",
  "progress": 0.5,
  "client_tasks": {
    "total": 2,
    "tasks": [
      {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "workflow_name": "example_workflow",
        "status": "running",
        "created_at": "2023-11-15T10:30:00Z",
        "started_at": "2023-11-15T10:30:05Z",
        "steps": 3,
        "current_step": 1
      }
    ]
  },
  "global_queue": {
    "total": 5,
    "waiting": 4,
    "running": 1
  },
  "queue_position": -1
}
```

### 7. 节点执行完成消息

服务器在节点执行完成时发送此消息，包含任务队列信息和客户端任务列表。

```json
{
  "type": "executed",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "node": "task1",
  "result": "Completed task1 after 3.0 seconds",
  "client_tasks": {
    "total": 2,
    "tasks": [
      {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "workflow_name": "example_workflow",
        "status": "running",
        "created_at": "2023-11-15T10:30:00Z",
        "started_at": "2023-11-15T10:30:05Z",
        "steps": 3,
        "current_step": 2
      }
    ]
  },
  "global_queue": {
    "total": 5,
    "waiting": 4,
    "running": 1
  },
  "queue_position": -1
}
```

### 7.1. 节点输出结果消息

服务器在节点的每个输出端口有值时发送此消息，用于传递节点的具体输出结果。

```json
{
  "type": "node output",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "node": "task1",
  "port": "output",
  "value": "Completed task1 after 3.0 seconds"
}
```

**注意**：
- `value` 字段会根据输出值的类型进行不同的处理：
  - 基本类型（字符串、数字、布尔值、null）：直接使用原值
  - 可序列化的复杂对象：保持对象结构，客户端可直接解析为JSON对象
  - 不可序列化的对象：转换为字符串表示
- 客户端应准备好处理不同类型的 `value` 值，包括字符串、数字、布尔值、对象和数组

### 8. 执行错误消息

服务器在任务或节点执行出错时发送此消息，包含任务队列信息和客户端任务列表。

```json
{
  "type": "execution error",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "node": "task2",
  "error": "Connection timeout",
  "client_tasks": {
    "total": 2,
    "tasks": [
      {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "workflow_name": "example_workflow",
        "status": "failed",
        "created_at": "2023-11-15T10:30:00Z",
        "started_at": "2023-11-15T10:30:05Z",
        "failed_at": "2023-11-15T10:30:20Z",
        "error": "Connection timeout",
        "steps": 3,
        "current_step": 2
      }
    ]
  },
  "global_queue": {
    "total": 5,
    "waiting": 4,
    "running": 0
  },
  "queue_position": -1
}
```

### 9. 任务状态消息

服务器发送任务状态更新消息。

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "status",
  "status": "completed"
}
```

### 10. 触发工作流

客户端发送HTTP请求以触发工作流执行，使用从服务器获得的客户端ID。

```
GET http://<服务器地址>:<端口>/api/trigger?client_id=<客户端ID>
```

响应示例：
```json
{
  "status": "success",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "工作流已触发"
}
```

## 客户端示例

### JavaScript客户端示例

请参考 [websocket_client_with_persistence.js](websocket_client_with_persistence.js) 文件获取完整的JavaScript客户端示例代码。

该示例展示了如何：
1. 连接到WebSocket服务器，支持使用已有客户端ID
2. 保存和恢复客户端ID
3. 处理订阅恢复
4. 实现自动重连机制
5. 接收并处理任务执行状态更新
6. 显示任务队列信息和客户端任务列表

## 客户端ID持久化

### 概述

客户端ID持久化功能允许客户端在断线重连后保持其身份标识和订阅关系，提供更好的用户体验。

### 实现原理

1. **客户端ID保存**：客户端在首次连接后，将服务器分配的客户端ID保存到本地存储（如localStorage）。

2. **重连时使用已有ID**：当客户端重新连接时，将之前保存的客户端ID作为查询参数添加到WebSocket URL中。

3. **服务器恢复订阅**：服务器接收到带有客户端ID的连接请求后，会自动恢复该客户端之前的订阅关系。

4. **连接确认消息**：服务器在连接确认消息中包含恢复的订阅列表，使客户端了解哪些订阅已被恢复。

5. **过期清理机制**：服务器定期清理长时间未活动的客户端记录，默认过期时间为0.5小时。

### 实现步骤

1. **保存客户端ID**：
   ```javascript
   // 在收到连接确认消息后保存客户端ID
   if (data.type === "connection established") {
       const clientId = data.client_id;
       localStorage.setItem('websocket_client_id', clientId);
   }
   ```

2. **使用已有ID连接**：
   ```javascript
   // 获取保存的客户端ID
   const clientId = localStorage.getItem('websocket_client_id') || null;

   // 构建WebSocket URL
   const wsUrl = clientId ? 
       `ws://localhost:8000/ws/connect?client_id=${clientId}` : 
       "ws://localhost:8000/ws/connect";

   // 连接WebSocket
   const ws = new WebSocket(wsUrl);
   ```

3. **处理恢复的订阅**：
   ```javascript
   // 在连接确认消息中处理恢复的订阅
   if (data.type === "connection established") {
       if (data.restored_subscriptions && data.restored_subscriptions.length > 0) {
           console.log("已恢复以下订阅:", data.restored_subscriptions);
       }
   }
   ```

### 最佳实践

1. **安全存储**：考虑使用安全的方式存储客户端ID，特别是在敏感应用中。

2. **过期处理**：实现客户端ID的过期机制，定期更新客户端ID以提高安全性。

3. **错误处理**：妥善处理使用已有ID连接失败的情况，例如ID已被服务器清除。

4. **状态同步**：在重连后，考虑请求任务的当前状态，以弥补断线期间可能错过的更新。

## 错误处理

### 连接错误

当WebSocket连接失败时，客户端应该处理以下错误：

- 连接超时
- 服务器不可用
- 认证失败
- 客户端ID无效

### 消息错误

客户端应该处理以下消息错误：

- 无效的消息格式
- 未知的消息类型
- 缺少必要的字段

### 重连机制

建议实现自动重连机制，在连接断开后自动尝试重新连接：

```javascript
let ws;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connect() {
    const clientId = localStorage.getItem('websocket_client_id') || null;
    const wsUrl = clientId ? 
        `ws://localhost:8000/ws/connect?client_id=${clientId}` : 
        "ws://localhost:8000/ws/connect";

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("连接成功");
        reconnectAttempts = 0;
    };

    ws.onclose = () => {
        console.log("连接关闭");
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`尝试重新连接 (${reconnectAttempts}/${maxReconnectAttempts})...`);
            setTimeout(connect, 2000 * reconnectAttempts);
        }
    };

    ws.onerror = (error) => {
        console.error("连接错误:", error);
    };

    ws.onmessage = (event) => {
        // 处理消息
    };
}

// 初始连接
connect();
```