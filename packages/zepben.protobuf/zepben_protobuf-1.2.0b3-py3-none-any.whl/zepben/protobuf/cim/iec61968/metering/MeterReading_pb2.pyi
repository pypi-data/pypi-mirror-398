from zepben.protobuf.cim.iec61968.metering import Reading_pb2 as _Reading_pb2
from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MeterReading(_message.Message):
    __slots__ = ("io", "meterMRIDNull", "meterMRIDSet", "readings")
    IO_FIELD_NUMBER: _ClassVar[int]
    METERMRIDNULL_FIELD_NUMBER: _ClassVar[int]
    METERMRIDSET_FIELD_NUMBER: _ClassVar[int]
    READINGS_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    meterMRIDNull: _struct_pb2.NullValue
    meterMRIDSet: str
    readings: _containers.RepeatedCompositeFieldContainer[_Reading_pb2.Reading]
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., meterMRIDNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., meterMRIDSet: _Optional[str] = ..., readings: _Optional[_Iterable[_Union[_Reading_pb2.Reading, _Mapping]]] = ...) -> None: ...
