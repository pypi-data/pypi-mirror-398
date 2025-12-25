from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PositionPoint(_message.Message):
    __slots__ = ("xPosition", "yPosition")
    XPOSITION_FIELD_NUMBER: _ClassVar[int]
    YPOSITION_FIELD_NUMBER: _ClassVar[int]
    xPosition: float
    yPosition: float
    def __init__(self, xPosition: _Optional[float] = ..., yPosition: _Optional[float] = ...) -> None: ...
