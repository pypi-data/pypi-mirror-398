from zepben.protobuf.cim.iec61970.base.core import ConductingEquipment_pb2 as _ConductingEquipment_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EarthFaultCompensator(_message.Message):
    __slots__ = ("ce", "rNull", "rSet")
    CE_FIELD_NUMBER: _ClassVar[int]
    RNULL_FIELD_NUMBER: _ClassVar[int]
    RSET_FIELD_NUMBER: _ClassVar[int]
    ce: _ConductingEquipment_pb2.ConductingEquipment
    rNull: _struct_pb2.NullValue
    rSet: float
    def __init__(self, ce: _Optional[_Union[_ConductingEquipment_pb2.ConductingEquipment, _Mapping]] = ..., rNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., rSet: _Optional[float] = ...) -> None: ...
