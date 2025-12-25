from zepben.protobuf.cim.iec61970.base.auxiliaryequipment import Sensor_pb2 as _Sensor_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CurrentTransformer(_message.Message):
    __slots__ = ("sn", "coreBurdenNull", "coreBurdenSet")
    SN_FIELD_NUMBER: _ClassVar[int]
    COREBURDENNULL_FIELD_NUMBER: _ClassVar[int]
    COREBURDENSET_FIELD_NUMBER: _ClassVar[int]
    sn: _Sensor_pb2.Sensor
    coreBurdenNull: _struct_pb2.NullValue
    coreBurdenSet: int
    def __init__(self, sn: _Optional[_Union[_Sensor_pb2.Sensor, _Mapping]] = ..., coreBurdenNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., coreBurdenSet: _Optional[int] = ...) -> None: ...
