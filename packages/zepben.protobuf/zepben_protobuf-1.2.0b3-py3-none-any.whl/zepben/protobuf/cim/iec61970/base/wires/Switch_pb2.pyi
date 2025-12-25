from zepben.protobuf.cim.iec61970.base.core import ConductingEquipment_pb2 as _ConductingEquipment_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Switch(_message.Message):
    __slots__ = ("ce", "normalOpen", "open", "ratedCurrentNull", "ratedCurrentSet")
    CE_FIELD_NUMBER: _ClassVar[int]
    NORMALOPEN_FIELD_NUMBER: _ClassVar[int]
    OPEN_FIELD_NUMBER: _ClassVar[int]
    RATEDCURRENTNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDCURRENTSET_FIELD_NUMBER: _ClassVar[int]
    ce: _ConductingEquipment_pb2.ConductingEquipment
    normalOpen: bool
    open: bool
    ratedCurrentNull: _struct_pb2.NullValue
    ratedCurrentSet: float
    def __init__(self, ce: _Optional[_Union[_ConductingEquipment_pb2.ConductingEquipment, _Mapping]] = ..., normalOpen: bool = ..., open: bool = ..., ratedCurrentNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedCurrentSet: _Optional[float] = ...) -> None: ...
