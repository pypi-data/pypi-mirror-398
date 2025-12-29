from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class IntentResponseType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TEXT: _ClassVar[IntentResponseType]
    MARKDOWN: _ClassVar[IntentResponseType]
    IMAGE: _ClassVar[IntentResponseType]
    VIDEO: _ClassVar[IntentResponseType]
    COMMAND: _ClassVar[IntentResponseType]
    SCHEDULE: _ClassVar[IntentResponseType]
TEXT: IntentResponseType
MARKDOWN: IntentResponseType
IMAGE: IntentResponseType
VIDEO: IntentResponseType
COMMAND: IntentResponseType
SCHEDULE: IntentResponseType

class IntentResponse(_message.Message):
    __slots__ = ("proto_id", "type", "user_id", "record_id", "group_id", "mode", "index", "count", "is_end", "content", "file_id", "response_message_id", "status")
    PROTO_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    RECORD_ID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    IS_END_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    FILE_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    proto_id: str
    type: str
    user_id: int
    record_id: int
    group_id: int
    mode: int
    index: int
    count: int
    is_end: bool
    content: str
    file_id: str
    response_message_id: str
    status: str
    def __init__(self, proto_id: _Optional[str] = ..., type: _Optional[str] = ..., user_id: _Optional[int] = ..., record_id: _Optional[int] = ..., group_id: _Optional[int] = ..., mode: _Optional[int] = ..., index: _Optional[int] = ..., count: _Optional[int] = ..., is_end: bool = ..., content: _Optional[str] = ..., file_id: _Optional[str] = ..., response_message_id: _Optional[str] = ..., status: _Optional[str] = ...) -> None: ...
