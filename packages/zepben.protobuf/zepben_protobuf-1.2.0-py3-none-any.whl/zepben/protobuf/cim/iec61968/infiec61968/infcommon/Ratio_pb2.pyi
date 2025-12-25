from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Ratio(_message.Message):
    __slots__ = ("denominator", "numerator")
    DENOMINATOR_FIELD_NUMBER: _ClassVar[int]
    NUMERATOR_FIELD_NUMBER: _ClassVar[int]
    denominator: float
    numerator: float
    def __init__(self, denominator: _Optional[float] = ..., numerator: _Optional[float] = ...) -> None: ...
