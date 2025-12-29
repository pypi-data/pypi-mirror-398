from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Tag(_message.Message):
    __slots__ = ("proto_id", "record_id", "user_id", "tags")
    PROTO_ID_FIELD_NUMBER: _ClassVar[int]
    RECORD_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    proto_id: str
    record_id: int
    user_id: int
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, proto_id: _Optional[str] = ..., record_id: _Optional[int] = ..., user_id: _Optional[int] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...
