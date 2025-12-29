from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class RecordGroup(_message.Message):
    __slots__ = ("proto_id", "user_id", "group_id", "title", "description")
    PROTO_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    proto_id: str
    user_id: int
    group_id: int
    title: str
    description: str
    def __init__(self, proto_id: _Optional[str] = ..., user_id: _Optional[int] = ..., group_id: _Optional[int] = ..., title: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...
