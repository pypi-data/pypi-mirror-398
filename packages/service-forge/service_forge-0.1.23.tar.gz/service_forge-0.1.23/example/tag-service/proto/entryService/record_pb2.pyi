from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Record(_message.Message):
    __slots__ = ("proto_id", "id", "name", "text", "type", "user_id", "group_id", "file_id", "is_recognized", "is_deleted", "timestamp", "role", "is_stream", "is_stream_done", "force_reply", "tags", "status")
    PROTO_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    FILE_ID_FIELD_NUMBER: _ClassVar[int]
    IS_RECOGNIZED_FIELD_NUMBER: _ClassVar[int]
    IS_DELETED_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    IS_STREAM_FIELD_NUMBER: _ClassVar[int]
    IS_STREAM_DONE_FIELD_NUMBER: _ClassVar[int]
    FORCE_REPLY_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    proto_id: str
    id: int
    name: str
    text: str
    type: str
    user_id: int
    group_id: int
    file_id: str
    is_recognized: bool
    is_deleted: bool
    timestamp: str
    role: str
    is_stream: bool
    is_stream_done: bool
    force_reply: bool
    tags: _containers.RepeatedScalarFieldContainer[str]
    status: str
    def __init__(self, proto_id: _Optional[str] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., text: _Optional[str] = ..., type: _Optional[str] = ..., user_id: _Optional[int] = ..., group_id: _Optional[int] = ..., file_id: _Optional[str] = ..., is_recognized: bool = ..., is_deleted: bool = ..., timestamp: _Optional[str] = ..., role: _Optional[str] = ..., is_stream: bool = ..., is_stream_done: bool = ..., force_reply: bool = ..., tags: _Optional[_Iterable[str]] = ..., status: _Optional[str] = ...) -> None: ...
