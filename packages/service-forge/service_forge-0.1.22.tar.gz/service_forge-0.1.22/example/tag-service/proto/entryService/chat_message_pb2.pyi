from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ChatMessage(_message.Message):
    __slots__ = ("proto_id", "id", "content", "role", "session_id", "user_id", "is_stream", "is_stream_done")
    PROTO_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    IS_STREAM_FIELD_NUMBER: _ClassVar[int]
    IS_STREAM_DONE_FIELD_NUMBER: _ClassVar[int]
    proto_id: str
    id: int
    content: str
    role: str
    session_id: int
    user_id: int
    is_stream: bool
    is_stream_done: bool
    def __init__(self, proto_id: _Optional[str] = ..., id: _Optional[int] = ..., content: _Optional[str] = ..., role: _Optional[str] = ..., session_id: _Optional[int] = ..., user_id: _Optional[int] = ..., is_stream: bool = ..., is_stream_done: bool = ...) -> None: ...

class ChatHistory(_message.Message):
    __slots__ = ("proto_id", "messages")
    PROTO_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    proto_id: str
    messages: _containers.RepeatedCompositeFieldContainer[ChatMessage]
    def __init__(self, proto_id: _Optional[str] = ..., messages: _Optional[_Iterable[_Union[ChatMessage, _Mapping]]] = ...) -> None: ...
