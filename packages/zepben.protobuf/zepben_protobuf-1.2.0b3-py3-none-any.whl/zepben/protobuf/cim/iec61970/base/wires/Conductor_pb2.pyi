from zepben.protobuf.cim.iec61970.base.core import ConductingEquipment_pb2 as _ConductingEquipment_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Conductor(_message.Message):
    __slots__ = ("ce", "lengthNull", "lengthSet", "designTemperatureNull", "designTemperatureSet", "designRatingNull", "designRatingSet")
    CE_FIELD_NUMBER: _ClassVar[int]
    LENGTHNULL_FIELD_NUMBER: _ClassVar[int]
    LENGTHSET_FIELD_NUMBER: _ClassVar[int]
    DESIGNTEMPERATURENULL_FIELD_NUMBER: _ClassVar[int]
    DESIGNTEMPERATURESET_FIELD_NUMBER: _ClassVar[int]
    DESIGNRATINGNULL_FIELD_NUMBER: _ClassVar[int]
    DESIGNRATINGSET_FIELD_NUMBER: _ClassVar[int]
    ce: _ConductingEquipment_pb2.ConductingEquipment
    lengthNull: _struct_pb2.NullValue
    lengthSet: float
    designTemperatureNull: _struct_pb2.NullValue
    designTemperatureSet: int
    designRatingNull: _struct_pb2.NullValue
    designRatingSet: float
    def __init__(self, ce: _Optional[_Union[_ConductingEquipment_pb2.ConductingEquipment, _Mapping]] = ..., lengthNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lengthSet: _Optional[float] = ..., designTemperatureNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., designTemperatureSet: _Optional[int] = ..., designRatingNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., designRatingSet: _Optional[float] = ...) -> None: ...
