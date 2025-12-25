from zepben.protobuf.cim.iec61970.base.wires import ProtectedSwitch_pb2 as _ProtectedSwitch_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Breaker(_message.Message):
    __slots__ = ("sw", "inTransitTimeNull", "inTransitTimeSet")
    SW_FIELD_NUMBER: _ClassVar[int]
    INTRANSITTIMENULL_FIELD_NUMBER: _ClassVar[int]
    INTRANSITTIMESET_FIELD_NUMBER: _ClassVar[int]
    sw: _ProtectedSwitch_pb2.ProtectedSwitch
    inTransitTimeNull: _struct_pb2.NullValue
    inTransitTimeSet: float
    def __init__(self, sw: _Optional[_Union[_ProtectedSwitch_pb2.ProtectedSwitch, _Mapping]] = ..., inTransitTimeNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., inTransitTimeSet: _Optional[float] = ...) -> None: ...
