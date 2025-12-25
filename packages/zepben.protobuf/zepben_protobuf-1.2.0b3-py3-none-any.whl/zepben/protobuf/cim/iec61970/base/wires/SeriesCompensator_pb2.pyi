from zepben.protobuf.cim.iec61970.base.core import ConductingEquipment_pb2 as _ConductingEquipment_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SeriesCompensator(_message.Message):
    __slots__ = ("ce", "rNull", "rSet", "r0Null", "r0Set", "xNull", "xSet", "x0Null", "x0Set", "varistorRatedCurrentNull", "varistorRatedCurrentSet", "varistorVoltageThresholdNull", "varistorVoltageThresholdSet")
    CE_FIELD_NUMBER: _ClassVar[int]
    RNULL_FIELD_NUMBER: _ClassVar[int]
    RSET_FIELD_NUMBER: _ClassVar[int]
    R0NULL_FIELD_NUMBER: _ClassVar[int]
    R0SET_FIELD_NUMBER: _ClassVar[int]
    XNULL_FIELD_NUMBER: _ClassVar[int]
    XSET_FIELD_NUMBER: _ClassVar[int]
    X0NULL_FIELD_NUMBER: _ClassVar[int]
    X0SET_FIELD_NUMBER: _ClassVar[int]
    VARISTORRATEDCURRENTNULL_FIELD_NUMBER: _ClassVar[int]
    VARISTORRATEDCURRENTSET_FIELD_NUMBER: _ClassVar[int]
    VARISTORVOLTAGETHRESHOLDNULL_FIELD_NUMBER: _ClassVar[int]
    VARISTORVOLTAGETHRESHOLDSET_FIELD_NUMBER: _ClassVar[int]
    ce: _ConductingEquipment_pb2.ConductingEquipment
    rNull: _struct_pb2.NullValue
    rSet: float
    r0Null: _struct_pb2.NullValue
    r0Set: float
    xNull: _struct_pb2.NullValue
    xSet: float
    x0Null: _struct_pb2.NullValue
    x0Set: float
    varistorRatedCurrentNull: _struct_pb2.NullValue
    varistorRatedCurrentSet: int
    varistorVoltageThresholdNull: _struct_pb2.NullValue
    varistorVoltageThresholdSet: int
    def __init__(self, ce: _Optional[_Union[_ConductingEquipment_pb2.ConductingEquipment, _Mapping]] = ..., rNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., rSet: _Optional[float] = ..., r0Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., r0Set: _Optional[float] = ..., xNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., xSet: _Optional[float] = ..., x0Null: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., x0Set: _Optional[float] = ..., varistorRatedCurrentNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., varistorRatedCurrentSet: _Optional[int] = ..., varistorVoltageThresholdNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., varistorVoltageThresholdSet: _Optional[int] = ...) -> None: ...
