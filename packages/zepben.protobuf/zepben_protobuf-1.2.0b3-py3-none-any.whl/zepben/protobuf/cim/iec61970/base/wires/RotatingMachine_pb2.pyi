from zepben.protobuf.cim.iec61970.base.wires import RegulatingCondEq_pb2 as _RegulatingCondEq_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RotatingMachine(_message.Message):
    __slots__ = ("rce", "ratedPowerFactorNull", "ratedPowerFactorSet", "ratedSNull", "ratedSSet", "ratedUNull", "ratedUSet", "pNull", "pSet", "qNull", "qSet")
    RCE_FIELD_NUMBER: _ClassVar[int]
    RATEDPOWERFACTORNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDPOWERFACTORSET_FIELD_NUMBER: _ClassVar[int]
    RATEDSNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDSSET_FIELD_NUMBER: _ClassVar[int]
    RATEDUNULL_FIELD_NUMBER: _ClassVar[int]
    RATEDUSET_FIELD_NUMBER: _ClassVar[int]
    PNULL_FIELD_NUMBER: _ClassVar[int]
    PSET_FIELD_NUMBER: _ClassVar[int]
    QNULL_FIELD_NUMBER: _ClassVar[int]
    QSET_FIELD_NUMBER: _ClassVar[int]
    rce: _RegulatingCondEq_pb2.RegulatingCondEq
    ratedPowerFactorNull: _struct_pb2.NullValue
    ratedPowerFactorSet: float
    ratedSNull: _struct_pb2.NullValue
    ratedSSet: float
    ratedUNull: _struct_pb2.NullValue
    ratedUSet: int
    pNull: _struct_pb2.NullValue
    pSet: float
    qNull: _struct_pb2.NullValue
    qSet: float
    def __init__(self, rce: _Optional[_Union[_RegulatingCondEq_pb2.RegulatingCondEq, _Mapping]] = ..., ratedPowerFactorNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedPowerFactorSet: _Optional[float] = ..., ratedSNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedSSet: _Optional[float] = ..., ratedUNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., ratedUSet: _Optional[int] = ..., pNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., pSet: _Optional[float] = ..., qNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., qSet: _Optional[float] = ...) -> None: ...
