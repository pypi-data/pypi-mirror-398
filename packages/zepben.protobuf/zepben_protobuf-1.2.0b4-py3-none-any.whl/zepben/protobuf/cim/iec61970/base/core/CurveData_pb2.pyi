from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CurveData(_message.Message):
    __slots__ = ("xValue", "y1Value", "y2ValueNull", "y2ValueSet", "y3ValueNull", "y3ValueSet")
    XVALUE_FIELD_NUMBER: _ClassVar[int]
    Y1VALUE_FIELD_NUMBER: _ClassVar[int]
    Y2VALUENULL_FIELD_NUMBER: _ClassVar[int]
    Y2VALUESET_FIELD_NUMBER: _ClassVar[int]
    Y3VALUENULL_FIELD_NUMBER: _ClassVar[int]
    Y3VALUESET_FIELD_NUMBER: _ClassVar[int]
    xValue: float
    y1Value: float
    y2ValueNull: _struct_pb2.NullValue
    y2ValueSet: float
    y3ValueNull: _struct_pb2.NullValue
    y3ValueSet: float
    def __init__(self, xValue: _Optional[float] = ..., y1Value: _Optional[float] = ..., y2ValueNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., y2ValueSet: _Optional[float] = ..., y3ValueNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., y3ValueSet: _Optional[float] = ...) -> None: ...
