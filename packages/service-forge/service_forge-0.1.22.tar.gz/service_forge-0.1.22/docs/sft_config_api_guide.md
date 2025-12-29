# SFT 配置 API 使用指南

本指南介绍如何通过 Python API 修改 Service Forge (SFT) 的配置，适用于导入了 service-forge 仓库的项目。

## 概述

SFT 配置系统提供了两种方式修改配置：
1. 命令行工具 (`sft config` 命令)
2. Python API (直接在代码中操作)

本指南专注于 Python API 的使用方法。

## 基本用法

### 1. 导入配置模块

```python
from service_forge.sft.config.sft_config import sft_config, SftConfig
```

### 2. 读取配置

```python
# 获取单个配置项
sft_file_root = sft_config.get("sft_file_root")
print(f"SFT 文件根目录: {sft_file_root}")

# 获取所有配置项
config_dict = sft_config.to_dict()
for key, value in config_dict.items():
    print(f"{key}: {value}")

# 直接访问配置属性
k8s_namespace = sft_config.k8s_namespace
service_center = sft_config.service_center_address
```

### 3. 修改配置

```python
# 设置单个配置项
sft_config.set("sft_file_root", "/new/path/to/sft")
sft_config.set("k8s_namespace", "new-namespace")

# 批量更新配置
updates = {
    "k8s_namespace": "production",
    "inject_http_port": 8080,
    "inject_kafka_host": "kafka.example.com"
}
sft_config.update(updates)

# 保存配置到文件
sft_config.save()
```

### 4. 创建新的配置实例

```python
# 创建新的配置实例
new_config = SftConfig(
    sft_file_root="/custom/path",
    k8s_namespace="custom-namespace",
    service_center_address="http://custom.service.center"
)

# 保存新配置
new_config.save()

# 加载指定配置文件
custom_config = SftConfig()
custom_config.from_file("/path/to/custom/config.yaml")
```

## 高级用法

### 1. 配置文件位置操作

```python
# 获取配置文件路径
config_path = sft_config.config_file_path
print(f"配置文件位置: {config_path}")

# 确保配置目录存在
sft_config.ensure_config_dir()
```

### 2. 配置验证

```python
# 检查配置项是否存在
if hasattr(sft_config, 'k8s_namespace'):
    print(f"K8s 命名空间: {sft_config.k8s_namespace}")

# 获取所有可用的配置键
available_keys = SftConfig.get_config_keys()
print("可用的配置项:", available_keys)
```

### 3. 配置描述信息

```python
# 获取配置项的描述
key = "k8s_namespace"
description = SftConfig.CONFIG_DESCRIPTIONS.get(key, "无描述")
print(f"{key}: {description}")

# 显示所有配置项及其描述
for key, description in SftConfig.CONFIG_DESCRIPTIONS.items():
    value = getattr(sft_config, key, "未设置")
    print(f"{key}: {value} - {description}")
```

## 实际应用示例

### 示例 1: 环境特定配置

```python
from service_forge.sft.config.sft_config import sft_config
import os

def setup_environment_config():
    """根据环境变量设置配置"""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        updates = {
            "k8s_namespace": "prod",
            "inject_http_port": 80,
            "inject_kafka_host": "kafka.prod.example.com"
        }
    elif env == "staging":
        updates = {
            "k8s_namespace": "staging",
            "inject_http_port": 8080,
            "inject_kafka_host": "kafka.staging.example.com"
        }
    else:  # development
        updates = {
            "k8s_namespace": "dev",
            "inject_http_port": 8000,
            "inject_kafka_host": "localhost"
        }
    
    sft_config.update(updates)
    sft_config.save()
    print(f"已应用 {env} 环境配置")

# 使用示例
setup_environment_config()
```

### 示例 2: 配置备份和恢复

```python
from service_forge.sft.config.sft_config import sft_config, SftConfig
import shutil
from datetime import datetime

def backup_config():
    """备份当前配置"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"~/.sft/config_backup_{timestamp}.yaml"
    backup_path = shutil.copy2(sft_config.config_file_path, backup_path)
    print(f"配置已备份到: {backup_path}")
    return backup_path

def restore_config(backup_path):
    """从备份恢复配置"""
    shutil.copy2(backup_path, sft_config.config_file_path)
    # 重新加载配置
    global sft_config
    sft_config = SftConfig.load()
    print(f"配置已从 {backup_path} 恢复")

# 使用示例
backup_path = backup_config()
# ... 进行一些配置修改 ...
# restore_config(backup_path)  # 恢复配置
```

### 示例 3: 配置模板应用

```python
from service_forge.sft.config.sft_config import sft_config

def apply_config_template(template_name):
    """应用预定义的配置模板"""
    templates = {
        "local": {
            "k8s_namespace": "local",
            "inject_kafka_host": "localhost",
            "inject_postgres_host": "localhost",
            "inject_redis_host": "localhost"
        },
        "cloud": {
            "k8s_namespace": "production",
            "inject_kafka_host": "kafka.cloud.example.com",
            "inject_postgres_host": "postgres.cloud.example.com",
            "inject_redis_host": "redis.cloud.example.com"
        },
        "minimal": {
            "sft_file_root": "/tmp/sft-minimal",
            "k8s_namespace": "minimal"
        }
    }
    
    if template_name not in templates:
        raise ValueError(f"未知的模板: {template_name}")
    
    sft_config.update(templates[template_name])
    sft_config.save()
    print(f"已应用 '{template_name}' 配置模板")

# 使用示例
apply_config_template("local")
```

## 注意事项

1. **配置持久化**: 修改配置后必须调用 `sft_config.save()` 才能持久化到文件
2. **只读配置**: `config_root` 是只读配置，不能通过 API 修改
3. **配置验证**: 设置配置时会验证配置项是否存在，不存在的配置项会抛出异常
4. **线程安全**: 配置操作不是线程安全的，多线程环境下需要加锁
5. **配置覆盖**: 每次保存都会覆盖整个配置文件

## 错误处理

```python
from service_forge.sft.config.sft_config import sft_config

try:
    # 尝试设置不存在的配置项
    sft_config.set("invalid_key", "value")
except ValueError as e:
    print(f"配置错误: {e}")

try:
    # 尝试设置只读配置
    sft_config.set("config_root", "/new/path")
except ValueError as e:
    print(f"只读配置错误: {e}")

try:
    # 保存配置时的错误处理
    sft_config.save()
except Exception as e:
    print(f"保存配置失败: {e}")
```

## 与命令行工具的对比

| 操作 | Python API | 命令行工具 |
|------|------------|------------|
| 查看所有配置 | `sft_config.to_dict()` | `sft config list` |
| 获取单个配置 | `sft_config.get(key)` | `sft config get <key>` |
| 设置配置 | `sft_config.set(key, value)` | `sft config set <key> <value>` |
| 保存配置 | `sft_config.save()` | 自动保存 |

Python API 提供了更灵活的配置管理方式，特别适合在应用程序中动态调整配置。