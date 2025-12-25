from zepben.protobuf.cim.iec61970.base.wires import PerLengthImpedance_pb2 as _PerLengthImpedance_pb2
from zepben.protobuf.cim.iec61970.base.wires import PhaseImpedanceData_pb2 as _PhaseImpedanceData_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PerLengthPhaseImpedance(_message.Message):
    __slots__ = ("pli", "phaseImpedanceData")
    PLI_FIELD_NUMBER: _ClassVar[int]
    PHASEIMPEDANCEDATA_FIELD_NUMBER: _ClassVar[int]
    pli: _PerLengthImpedance_pb2.PerLengthImpedance
    phaseImpedanceData: _containers.RepeatedCompositeFieldContainer[_PhaseImpedanceData_pb2.PhaseImpedanceData]
    def __init__(self, pli: _Optional[_Union[_PerLengthImpedance_pb2.PerLengthImpedance, _Mapping]] = ..., phaseImpedanceData: _Optional[_Iterable[_Union[_PhaseImpedanceData_pb2.PhaseImpedanceData, _Mapping]]] = ...) -> None: ...
