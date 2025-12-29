# 配置格式文档

本文档描述了 Service Forge 项目中 Service 和 Workflow 配置文件的格式规范。

## 目录

1. [Service 配置文件](#service-配置文件)
2. [Workflow 配置文件](#workflow-配置文件)
   - [基础结构](#基础结构)
   - [节点配置](#节点配置)
   - [触发器节点](#触发器节点)
   - [控制流节点](#控制流节点)
   - [输出节点](#输出节点)
   - [子工作流](#子工作流)

---

## Service 配置文件

Service 配置文件定义了服务的整体配置，包括服务名称、工作流列表以及 HTTP 和 Kafka 的连接设置。

### 基本结构

```yaml
name: <服务名称>
workflows:
  - <工作流配置文件的相对路径或绝对路径>

enable_http: <true|false>
http_host: <主机地址>
http_port: <端口号>

enable_kafka: <true|false>
kafka_host: <主机地址>
kafka_port: <端口号>
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 服务的名称 |
| `workflows` | array | 是 | 工作流配置文件路径列表 |
| `enable_http` | boolean | 否 | 是否启用 HTTP 服务 |
| `http_host` | string | 否 | HTTP 服务的主机地址（默认: 0.0.0.0） |
| `http_port` | integer | 否 | HTTP 服务的端口号（默认: 8000） |
| `enable_kafka` | boolean | 否 | 是否启用 Kafka 服务 |
| `kafka_host` | string | 否 | Kafka 的主机地址（默认: localhost） |
| `kafka_port` | integer | 否 | Kafka 的端口号（默认: 9092） |

### 示例

```yaml
name: example_service
workflows:
  - configs/workflow/kafka_workflow.yaml
  - configs/workflow/query_tags_workflow.yaml
  - configs/workflow/create_tag_workflow.yaml
  - configs/workflow/update_tag_workflow.yaml
  - configs/workflow/delete_tag_workflow.yaml

enable_http: true
http_host: 0.0.0.0
http_port: 8000
enable_kafka: true
kafka_host: localhost
kafka_port: 9092
```

---

## Workflow 配置文件

Workflow 配置文件定义了工作流的节点、连接关系和数据流向。

### 单workflow

```yaml
name: <工作流名称>

nodes:
  - name: <节点名称>
    type: <节点类型>
    args:
      <参数名>: <参数值>
    outputs:
      <输出端口名>: <目标节点名>|<目标端口名>

inputs:
  - name: <输入端口名称>
    port: <连接到节点端口>
    value: <注入值>

outputs:
  - name: <输出端口名称>
    port: <来自于节点端口>
```

### 多workflow

```yaml
main: <主工作流名称>

workflows:
  - name: <工作流名称>
    inputs:
      - name: <输入名称>
        port: <节点名>|<端口名>
        value: <初始值>
    outputs:
      - name: <输出名称>
        port: <节点名>|<端口名>
    nodes:
      - name: <节点名称>
        type: <节点类型>
        args:
          <参数名>: <参数值>
        outputs:
          <输出端口名>: <目标节点名>|<目标端口名>
```

只有主workflow会被执行，其他workflow作为主workflow中嵌套的子workflow。

---

## 节点配置

### 节点字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 节点的唯一标识符 |
| `type` | string | 是 | 节点的类型（如：FastAPITrigger, PrintNode 等） |
| `args` | object | 否 | 节点的输入参数 |
| `outputs` | object | 否 | 节点的输出连接，格式为 `目标节点名|端口名` |

### 端口连接格式

输出连接的格式为：`目标节点名|目标端口名`

例如：
```yaml
outputs:
  data: http_query_tags|query
  user_id: http_query_tags|user_id
```

这表示当前节点的 `data` 输出连接到 `http_query_tags` 节点的 `query` 输入端口。

---

## 触发器节点

触发器节点用于启动工作流的执行。

### 1. FastAPITrigger

用于通过 FastAPI 路由触发工作流执行。

**输入参数：**
- `app`: FastAPI 应用对象
- `path`: API 路由路径
- `method`: HTTP 方法（GET, POST, PUT, DELETE）
- `data_type`: 数据类型（用于请求数据的类型转换）

**输出端口：**
- `trigger`: 触发信号
- `user_id`: 用户ID
- `data`: 请求数据

**示例：**
```yaml
- name: fast_api_server
  type: FastAPITrigger
  args:
    app: app
    path: /api/v1/tags
    method: GET
    data_type: <{QUERY_TAGS_MODEL}>
  outputs:
    data: http_query_tags|query
    user_id: http_query_tags|user_id
```

### 2. KafkaAPITrigger

用于通过 Kafka 消息触发工作流执行。

**输入参数：**
- `app`: Kafka 应用对象
- `topic`: Kafka 主题名称
- `data_type`: 数据类型
- `group_id`: Kafka 消费者组ID（可选）

**输出端口：**
- `trigger`: 触发信号
- `data`: 消息数据

**示例：**
```yaml
- name: kafka_server
  type: KafkaAPITrigger
  args:
    app: kafka_app
    topic: test_topic
    data_type: FooInput
    group_id: <{KAFKA_GROUP_ID}>
  outputs:
    data: print_0|message
```

### 3. PeriodTrigger

周期性触发器，按指定时间间隔触发指定次数。

**输入参数：**
- `TRIGGER`: 初始触发信号（布尔值）
- `period`: 时间间隔（秒）
- `times`: 触发次数

**输出端口：**
- `trigger`: 触发信号

**示例：**
```yaml
- name: trigger
  type: PeriodTrigger
  args:
    times: 2
    period: 0.05
  outputs:
    trigger: if_0|TRIGGER
```

### 4. OnceTrigger

单次触发器，只在启动时触发一次。

**输入参数：**
无

**输出端口：**
- `trigger`: 触发信号

**示例：**
```yaml
- name: trigger
  type: OnceTrigger
  args:
  outputs:
    trigger: if_0|TRIGGER
```

---

## 控制流节点

### 1. IfNode

条件判断节点，根据条件表达式判断执行路径。

**输入参数：**
- `TRIGGER`: 触发信号
- `condition`: Python 表达式字符串，返回布尔值

**输出端口：**
- `true`: 条件为真时的输出
- `false`: 条件为假时的输出

**示例：**
```yaml
- name: if_0
  type: IfNode
  args:
    condition: "1 == 1"
  outputs:
    'true': if_1|TRIGGER
    'false': print_1|message
```

### 2. IfConsoleInputNode

交互式条件判断节点，从控制台获取用户输入。

**输入参数：**
- `TRIGGER`: 触发信号
- `condition`: 提示用户的问题字符串

**输出端口：**
- `true`: 用户回答为真时的输出
- `false`: 用户回答为假时的输出

**示例：**
```yaml
- name: if_0
  type: IfConsoleInputNode
  args:
    TRIGGER: true
    condition: "Do you agree with this? [y/n]"
  outputs:
    'true': print|message
    'false': print|message
```

---

## 输出节点

### 1. PrintNode

打印输出节点，将数据打印到控制台。

**输入参数：**
- `message`: 要打印的消息

**输出端口：**
无

**示例：**
```yaml
- name: print_0
  type: PrintNode
  args:
```

### 2. KafkaOutputNode

Kafka 输出节点，将数据发送到 Kafka 主题。

**输入参数：**
- `app`: Kafka 应用对象
- `topic`: Kafka 主题名称
- `data_type`: 数据类型（可选）
- `data`: 要发送的数据

**输出端口：**
无

**示例：**
```yaml
- name: kafka_output
  type: KafkaOutputNode
  args:
    app: kafka_app
    topic: tag.response
    data_type: str
  outputs: []
```

---

## LLM 节点

### QueryLLMNode

LLM 查询节点，用于查询大语言模型。

**输入参数：**
- `prompt`: 提示词文件路径
- `system_prompt`: 系统提示词文件路径（可选）
- `temperature`: 温度参数（可选）

**输出端口：**
- 自定义输出端口

**示例：**
```yaml
- name: query_llm
  type: QueryLLMNode
  args:
    prompt: prompt/test_query_llm_prompt.txt
    system_prompt: prompt/test_query_llm_system_prompt.txt
    temperature: 0.8
  outputs:
```

---

## 子工作流

### WorkflowNode

工作流节点，用于嵌套执行子工作流。

**输入参数：**
- `workflow`: 子工作流的名称

**输出端口：**
根据子工作流的输出定义

**示例：**
```yaml
- name: sub_workflow_node
  type: WorkflowNode
  sub_workflows:
    - name: sub_workflow

  sub_workflows_input_ports:
    - name: message
      port: sub_workflow|message

  sub_workflows_output_ports:

  args:
    workflow: sub_workflow
```

### 完整子工作流示例

```yaml
main: main

workflows:
  - name: sub_workflow
    inputs:
      - name: message
        port: print|message
        value:

    outputs: []

    nodes:
      - name: print
        type: PrintNode
        args:

  - name: main
    inputs:
    outputs:

    nodes:
      - name: if_0
        type: IfConsoleInputNode
        args:
          TRIGGER: true
          condition: "Do you agree with this? [y/n]"
        outputs:
          'true': sub_workflow_node|message
          'false': sub_workflow_node|message

      - name: sub_workflow_node
        type: WorkflowNode
        sub_workflows:
          - name: sub_workflow

        sub_workflows_input_ports:
          - name: message
            port: sub_workflow|message

        sub_workflows_output_ports:

        args:
          workflow: sub_workflow
```

---

## 工作流输出

在工作流配置中，可以定义工作流的输出端口，这些端口将作为整个工作流的返回值。

```yaml
outputs:
  - name: result
    port: http_query_tags|tags
```

**字段说明：**
- `name`: 输出端口的名称
- `port`: 输出数据的来源，格式为 `节点名|端口名`

---

## 变量引用

在配置文件中，可以使用 `<{变量名}>` 的格式引用变量。这些变量通常在运行时通过环境变量或其他配置文件提供。

**示例：**
```yaml
args:
  topic: <{INPUT_TOPIC}>
  data_type: <{INPUT_TOPIC_TYPE}>
```

---

## 注意事项

1. **节点名称唯一性**：每个节点的 `name` 字段在同一个工作流中必须是唯一的。

2. **输出连接格式**：输出连接的格式必须严格遵守 `目标节点名|端口名` 的格式。

3. **端口名称**：布尔类型的触发端口建议使用大写 `TRIGGER`，其他端口使用小写。

4. **数据类型**：对于需要类型转换的数据（如 FastAPITrigger 的 `data_type`），需要使用导入的数据类型。

5. **空输出**：如果节点没有输出连接，可以使用空对象 `outputs: {}` 或不包含该字段。

6. **布尔值输出**：对于包含特殊字符的输出端口（如 `'true'`, `'false'`），需要使用引号包裹。

---

## 常用模式

### 1. HTTP API 工作流

```yaml
name: http_api_workflow
nodes:
  - name: fast_api_server
    type: FastAPITrigger
    args:
      app: app
      path: /api/v1/endpoint
      method: POST
      data_type: DataModel
    outputs:
      data: process_node|input
      user_id: process_node|user_id

  - name: process_node
    type: ProcessNode
    args:
    outputs: []

outputs:
  - name: result
    port: process_node|output
```

### 2. Kafka 消息处理工作流

```yaml
name: kafka_workflow
nodes:
  - name: kafka_server
    type: KafkaAPITrigger
    args:
      app: kafka_app
      topic: input_topic
      data_type: InputModel
    outputs:
      data: process_node|input

  - name: process_node
    type: ProcessNode
    args:
    outputs:
      result: kafka_output|data

  - name: kafka_output
    type: KafkaOutputNode
    args:
      app: kafka_app
      topic: output_topic
      data_type: OutputModel
    outputs: []
```

### 3. 条件分支工作流

```yaml
name: conditional_workflow
nodes:
  - name: trigger
    type: OnceTrigger
    args:
    outputs:
      trigger: if_0|TRIGGER

  - name: if_0
    type: IfNode
    args:
      condition: "some_condition"
    outputs:
      'true': process_a|input
      'false': process_b|input

  - name: process_a
    type: ProcessNode
    args:
    outputs: []

  - name: process_b
    type: ProcessNode
    args:
    outputs: []
```

