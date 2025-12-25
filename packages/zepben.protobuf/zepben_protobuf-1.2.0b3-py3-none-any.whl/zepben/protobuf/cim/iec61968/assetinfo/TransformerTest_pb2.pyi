from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TransformerTest(_message.Message):
    __slots__ = ("io", "basePowerNull", "basePowerSet", "temperatureNull", "temperatureSet")
    IO_FIELD_NUMBER: _ClassVar[int]
    BASEPOWERNULL_FIELD_NUMBER: _ClassVar[int]
    BASEPOWERSET_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURENULL_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURESET_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    basePowerNull: _struct_pb2.NullValue
    basePowerSet: int
    temperatureNull: _struct_pb2.NullValue
    temperatureSet: float
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., basePowerNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., basePowerSet: _Optional[int] = ..., temperatureNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., temperatureSet: _Optional[float] = ...) -> None: ...
