from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Schedule(_message.Message):
    __slots__ = ("proto_id", "record_id", "user_id", "result")
    PROTO_ID_FIELD_NUMBER: _ClassVar[int]
    RECORD_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    proto_id: str
    record_id: int
    user_id: int
    result: str
    def __init__(self, proto_id: _Optional[str] = ..., record_id: _Optional[int] = ..., user_id: _Optional[int] = ..., result: _Optional[str] = ...) -> None: ...
