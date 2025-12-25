from google.protobuf import struct_pb2 as _struct_pb2
from zepben.protobuf.cim.iec61970.base.core import PowerSystemResource_pb2 as _PowerSystemResource_pb2
from zepben.protobuf.cim.iec61970.base.wires import SinglePhaseKind_pb2 as _SinglePhaseKind_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AcLineSegmentPhase(_message.Message):
    __slots__ = ("psr", "phase", "sequenceNumberNull", "sequenceNumberSet", "acLineSegmentMRID")
    PSR_FIELD_NUMBER: _ClassVar[int]
    PHASE_FIELD_NUMBER: _ClassVar[int]
    SEQUENCENUMBERNULL_FIELD_NUMBER: _ClassVar[int]
    SEQUENCENUMBERSET_FIELD_NUMBER: _ClassVar[int]
    ACLINESEGMENTMRID_FIELD_NUMBER: _ClassVar[int]
    psr: _PowerSystemResource_pb2.PowerSystemResource
    phase: _SinglePhaseKind_pb2.SinglePhaseKind
    sequenceNumberNull: _struct_pb2.NullValue
    sequenceNumberSet: int
    acLineSegmentMRID: str
    def __init__(self, psr: _Optional[_Union[_PowerSystemResource_pb2.PowerSystemResource, _Mapping]] = ..., phase: _Optional[_Union[_SinglePhaseKind_pb2.SinglePhaseKind, str]] = ..., sequenceNumberNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., sequenceNumberSet: _Optional[int] = ..., acLineSegmentMRID: _Optional[str] = ...) -> None: ...
