from zepben.protobuf.cim.iec61970.base.core import ConductingEquipment_pb2 as _ConductingEquipment_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Clamp(_message.Message):
    __slots__ = ("ce", "lengthFromTerminal1Null", "lengthFromTerminal1Set", "acLineSegmentMRID")
    CE_FIELD_NUMBER: _ClassVar[int]
    LENGTHFROMTERMINAL1NULL_FIELD_NUMBER: _ClassVar[int]
    LENGTHFROMTERMINAL1SET_FIELD_NUMBER: _ClassVar[int]
    ACLINESEGMENTMRID_FIELD_NUMBER: _ClassVar[int]
    ce: _ConductingEquipment_pb2.ConductingEquipment
    lengthFromTerminal1Null: _struct_pb2.NullValue
    lengthFromTerminal1Set: float
    acLineSegmentMRID: str
    def __init__(self, ce: _Optional[_Union[_ConductingEquipment_pb2.ConductingEquipment, _Mapping]] = ..., lengthFromTerminal1Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., lengthFromTerminal1Set: _Optional[float] = ..., acLineSegmentMRID: _Optional[str] = ...) -> None: ...
