# Service Forge

Automated service creation and maintenance tool.

## Install

```bash
pip install -e .
```

## CLI Usage (sft)

Service Forge 提供了命令行工具 `sft` 用于服务管理。

### 服务上传和部署

```bash
# 上传服务（打包并上传到服务器）
sft upload [project_path]

# 列出本地已打包的服务包
sft list

# 部署服务（只在服务器上使用）
sft deploy <name> <version>
```

### 配置管理

```bash
# 列出所有配置项
sft config list

# 获取指定配置项的值
sft config get <key>

# 设置配置项的值
sft config set <key> <value>
```

### 服务管理

```bash
# 列出所有服务
sft service list

# 删除服务（只在服务器上使用）
sft service delete <service_name> [--force, -f]

# 查看服务日志（只在服务器上使用）
sft service logs <service_name> [--container, -c] [--tail, -n] [--follow, -f] [--previous, -p]
```

## TODO

- [x] 多次 trigger 并行执行
- [x] 支持 websocket 来做 trigger、输入和输出
- [x] 优化 websocket 客户端映射和重连支持
- [x] 节点和 workflow 运行情况的回调函数
- [ ] 支持 a2a
- [ ] workflow 执行异常处理
