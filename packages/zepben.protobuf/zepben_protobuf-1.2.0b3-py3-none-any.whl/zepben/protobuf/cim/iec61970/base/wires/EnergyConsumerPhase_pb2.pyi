from zepben.protobuf.cim.iec61970.base.core import PowerSystemResource_pb2 as _PowerSystemResource_pb2
from zepben.protobuf.cim.iec61970.base.wires import SinglePhaseKind_pb2 as _SinglePhaseKind_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EnergyConsumerPhase(_message.Message):
    __slots__ = ("psr", "energyConsumerMRID", "pNull", "pSet", "pFixedNull", "pFixedSet", "phase", "qNull", "qSet", "qFixedNull", "qFixedSet")
    PSR_FIELD_NUMBER: _ClassVar[int]
    ENERGYCONSUMERMRID_FIELD_NUMBER: _ClassVar[int]
    PNULL_FIELD_NUMBER: _ClassVar[int]
    PSET_FIELD_NUMBER: _ClassVar[int]
    PFIXEDNULL_FIELD_NUMBER: _ClassVar[int]
    PFIXEDSET_FIELD_NUMBER: _ClassVar[int]
    PHASE_FIELD_NUMBER: _ClassVar[int]
    QNULL_FIELD_NUMBER: _ClassVar[int]
    QSET_FIELD_NUMBER: _ClassVar[int]
    QFIXEDNULL_FIELD_NUMBER: _ClassVar[int]
    QFIXEDSET_FIELD_NUMBER: _ClassVar[int]
    psr: _PowerSystemResource_pb2.PowerSystemResource
    energyConsumerMRID: str
    pNull: _struct_pb2.NullValue
    pSet: float
    pFixedNull: _struct_pb2.NullValue
    pFixedSet: float
    phase: _SinglePhaseKind_pb2.SinglePhaseKind
    qNull: _struct_pb2.NullValue
    qSet: float
    qFixedNull: _struct_pb2.NullValue
    qFixedSet: float
    def __init__(self, psr: _Optional[_Union[_PowerSystemResource_pb2.PowerSystemResource, _Mapping]] = ..., energyConsumerMRID: _Optional[str] = ..., pNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., pSet: _Optional[float] = ..., pFixedNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., pFixedSet: _Optional[float] = ..., phase: _Optional[_Union[_SinglePhaseKind_pb2.SinglePhaseKind, str]] = ..., qNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., qSet: _Optional[float] = ..., qFixedNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., qFixedSet: _Optional[float] = ...) -> None: ...
