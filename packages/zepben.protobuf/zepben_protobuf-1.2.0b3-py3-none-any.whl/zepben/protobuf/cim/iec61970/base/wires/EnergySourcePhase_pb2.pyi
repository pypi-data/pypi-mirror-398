from zepben.protobuf.cim.iec61970.base.core import PowerSystemResource_pb2 as _PowerSystemResource_pb2
from zepben.protobuf.cim.iec61970.base.wires import SinglePhaseKind_pb2 as _SinglePhaseKind_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EnergySourcePhase(_message.Message):
    __slots__ = ("psr", "energySourceMRID", "phase")
    PSR_FIELD_NUMBER: _ClassVar[int]
    ENERGYSOURCEMRID_FIELD_NUMBER: _ClassVar[int]
    PHASE_FIELD_NUMBER: _ClassVar[int]
    psr: _PowerSystemResource_pb2.PowerSystemResource
    energySourceMRID: str
    phase: _SinglePhaseKind_pb2.SinglePhaseKind
    def __init__(self, psr: _Optional[_Union[_PowerSystemResource_pb2.PowerSystemResource, _Mapping]] = ..., energySourceMRID: _Optional[str] = ..., phase: _Optional[_Union[_SinglePhaseKind_pb2.SinglePhaseKind, str]] = ...) -> None: ...
