from zepben.protobuf.cim.iec61970.base.auxiliaryequipment import Sensor_pb2 as _Sensor_pb2
from zepben.protobuf.cim.iec61970.base.auxiliaryequipment import PotentialTransformerKind_pb2 as _PotentialTransformerKind_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PotentialTransformer(_message.Message):
    __slots__ = ("sn", "type")
    SN_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    sn: _Sensor_pb2.Sensor
    type: _PotentialTransformerKind_pb2.PotentialTransformerKind
    def __init__(self, sn: _Optional[_Union[_Sensor_pb2.Sensor, _Mapping]] = ..., type: _Optional[_Union[_PotentialTransformerKind_pb2.PotentialTransformerKind, str]] = ...) -> None: ...
