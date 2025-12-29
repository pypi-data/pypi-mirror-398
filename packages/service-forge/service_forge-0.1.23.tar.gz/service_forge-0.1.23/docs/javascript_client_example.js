// WebSocket 客户端示例，支持客户端ID持久化

class PersistentWebSocketClient {
    constructor(url) {
        this.url = url;
        this.clientId = this.getClientId() || null;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // 初始重连延迟1秒
        this.messageHandlers = {};

        // 注册默认消息处理器
        this.registerMessageHandler("connection established", this.handleConnectionEstablished.bind(this));
        this.registerMessageHandler("execution start", this.handleExecutionStart.bind(this));
        this.registerMessageHandler("executing", this.handleExecuting.bind(this));
        this.registerMessageHandler("progress", this.handleProgress.bind(this));
        this.registerMessageHandler("executed", this.handleExecuted.bind(this));
        this.registerMessageHandler("execution error", this.handleExecutionError.bind(this));
    }

    // 获取本地存储的客户端ID
    getClientId() {
        return localStorage.getItem('websocket_client_id');
    }

    // 保存客户端ID到本地存储
    saveClientId(clientId) {
        localStorage.setItem('websocket_client_id', clientId);
    }

    // 注册消息处理器
    registerMessageHandler(messageType, handler) {
        this.messageHandlers[messageType] = handler;
    }

    // 连接到WebSocket服务器
    connect() {
        let wsUrl = this.url;

        // 如果有客户端ID，添加到URL中
        if (this.clientId) {
            wsUrl += `?client_id=${this.clientId}`;
            console.log(`使用已有客户端ID连接: ${this.clientId}`);
        } else {
            console.log("使用新客户端ID连接");
        }

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log("WebSocket连接已建立");
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000; // 重置重连延迟
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            // 调用对应的消息处理器
            const handler = this.messageHandlers[data.type];
            if (handler) {
                handler(data);
            } else {
                console.log("未处理的消息类型:", data.type, data);
            }
        };

        this.ws.onclose = () => {
            console.log("WebSocket连接已关闭");
            this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
            console.error("WebSocket错误:", error);
        };
    }

    // 尝试重新连接
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`尝试重新连接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})，延迟${this.reconnectDelay}ms`);

            setTimeout(() => {
                this.connect();
                // 指数退避策略，增加重连延迟
                this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
            }, this.reconnectDelay);
        } else {
            console.error("已达到最大重连次数，停止尝试");
        }
    }

    // 发送消息
    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
            return true;
        } else {
            console.error("WebSocket未连接，无法发送消息");
            return false;
        }
    }

    // 订阅任务
    subscribeToTask(taskId) {
        return this.sendMessage({
            type: "subscribe",
            task_id: taskId
        });
    }

    // 取消订阅任务
    unsubscribeFromTask(taskId) {
        return this.sendMessage({
            type: "unsubscribe",
            task_id: taskId
        });
    }

    // 消息处理器
    handleConnectionEstablished(data) {
        console.log("连接已建立，服务器分配的客户端ID:", data.client_id);

        // 保存客户端ID
        this.clientId = data.client_id;
        this.saveClientId(this.clientId);

        // 显示恢复的订阅
        if (data.restored_subscriptions && data.restored_subscriptions.length > 0) {
            console.log("已恢复以下订阅:", data.restored_subscriptions);
        }
    }

    handleExecutionStart(data) {
        console.log(`任务 ${data.task_id} 开始执行`);
    }

    handleExecuting(data) {
        console.log(`节点 ${data.node} 开始执行`);
    }

    handleProgress(data) {
        console.log(`节点 ${data.node} 执行进度: ${data.progress * 100}%`);
    }

    handleExecuted(data) {
        if (data.node) {
            console.log(`节点 ${data.node} 执行完成`);
            if (data.result) {
                console.log(`结果: ${data.result}`);
            }
        } else {
            console.log("工作流执行完成");
        }
    }

    handleExecutionError(data) {
        if (data.node) {
            console.error(`节点 ${data.node} 执行出错: ${data.error}`);
        } else {
            console.error(`工作流执行出错: ${data.error}`);
        }
    }
}

// 使用示例
const client = new PersistentWebSocketClient("ws://localhost:8000/ws/connect");

// 连接到WebSocket服务器
client.connect();

// 触发工作流（需要在连接建立后执行）
setTimeout(() => {
    if (client.clientId) {
        fetch(`http://localhost:8000/api/trigger?client_id=${client.clientId}`)
            .then(response => response.json())
            .then(data => console.log("工作流触发成功:", data))
            .catch(error => console.error("工作流触发失败:", error));
    } else {
        console.error("客户端ID尚未获取");
    }
}, 2000);
