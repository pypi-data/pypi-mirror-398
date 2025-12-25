from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class CheckConnectionRequest(_message.Message):
    __slots__ = ("messageId",)
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    messageId: int
    def __init__(self, messageId: _Optional[int] = ...) -> None: ...
