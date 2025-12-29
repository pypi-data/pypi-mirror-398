# Kafka Topics Reference

# 说明

topics.yaml 里记录了每个微服务**发出**的topic事件及对应的protobuf数据结构描述

ref是引用的数据名称，name是topic字符串，name命令规则：service.entity.event

所有topic如下：


## `entry.record.preprocess`
- 📄 Schema: `entryService/record.proto`
- 🧩 Message: `entryService.Record`
- 🧷 Ref: `EntryRecordPreprocess`
- 📝 Description: 用户记录预处理，如asr/ocr等
- 🏷  Versions: v1

## `entry.record.preprocess.reply`
- 📄 Schema: `entryService/record.proto`
- 🧩 Message: `entryService.Record`
- 🧷 Ref: `EntryRecordPreprocessReply`
- 📝 Description: 用户记录预处理完成
- 🏷  Versions: v1

## `entry.record.process`
- 📄 Schema: `entryService/record.proto`
- 🧩 Message: `entryService.Record`
- 🧷 Ref: `EntryRecordProcess`
- 📝 Description: 给总agent使用
- 🏷  Versions: v1

## `entry.record.update`
- 📄 Schema: `entryService/record.proto`
- 🧩 Message: `entryService.Record`
- 🧷 Ref: `EntryRecordUpdate`
- 📝 Description: 用户记录更新
- 🏷  Versions: v1

## `intent.response`
- 📄 Schema: `intentService/intent_response.proto`
- 🧩 Message: `intentService.IntentResponse`
- 🧷 Ref: `IntentResponse`
- 📝 Description: 用户意图解析完成
- 🏷  Versions: v1

## `intent.record.group`
- 📄 Schema: `intentService/record_group.proto`
- 🧩 Message: `intentService.RecordGroup`
- 🧷 Ref: `IntentRecordGroup`
- 📝 Description: 用户记录组
- 🏷  Versions: v1

## `chat.request`
- 📄 Schema: `entryService/chat_message.proto`
- 🧩 Message: `entryService.ChatHistory`
- 🧷 Ref: `ChatRequest`
- 📝 Description: 用户对话请求
- 🏷  Versions: v1

## `chat.response`
- 📄 Schema: `entryService/chat_message.proto`
- 🧩 Message: `entryService.ChatMessage`
- 🧷 Ref: `ChatResponse`
- 📝 Description: 用户对话结果返回
- 🏷  Versions: v1

## `schedule.request`
- 📄 Schema: `entryService/record.proto`
- 🧩 Message: `entryService.Record`
- 🧷 Ref: `ScheduleRequest`
- 📝 Description: 用户记录调度请求
- 🏷  Versions: v1

## `schedule.response`
- 📄 Schema: `scheduleService/schedule.proto`
- 🧩 Message: `scheduleService.Schedule`
- 🧷 Ref: `ScheduleResponse`
- 📝 Description: 用户记录调度结果
- 🏷  Versions: v1

## `feedback.request`
- 📄 Schema: `entryService/record.proto`
- 🧩 Message: `entryService.Record`
- 🧷 Ref: `FeedbackRequest`
- 📝 Description: 用户反馈请求
- 🏷  Versions: v1

## `feedback.response`
- 📄 Schema: `entryService/record.proto`
- 🧩 Message: `entryService.Record`
- 🧷 Ref: `FeedbackResponse`
- 📝 Description: 用户反馈结果
- 🏷  Versions: v1

## `tag.request`
- 📄 Schema: `entryService/record.proto`
- 🧩 Message: `entryService.Record`
- 🧷 Ref: `TagRequest`
- 📝 Description: 用户标签请求
- 🏷  Versions: v1

## `tag.response`
- 📄 Schema: `tagService/tag.proto`
- 🧩 Message: `tagService.Tag`
- 🧷 Ref: `TagResponse`
- 📝 Description: 用户标签结果
- 🏷  Versions: v1

