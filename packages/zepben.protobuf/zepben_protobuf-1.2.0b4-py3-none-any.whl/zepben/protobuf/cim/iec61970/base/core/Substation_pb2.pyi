from zepben.protobuf.cim.iec61970.base.core import EquipmentContainer_pb2 as _EquipmentContainer_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Substation(_message.Message):
    __slots__ = ("ec", "subGeographicalRegionMRID", "normalEnergizedFeederMRIDs", "loopMRIDs", "circuitMRIDs", "normalEnergizedLoopMRIDs")
    EC_FIELD_NUMBER: _ClassVar[int]
    SUBGEOGRAPHICALREGIONMRID_FIELD_NUMBER: _ClassVar[int]
    NORMALENERGIZEDFEEDERMRIDS_FIELD_NUMBER: _ClassVar[int]
    LOOPMRIDS_FIELD_NUMBER: _ClassVar[int]
    CIRCUITMRIDS_FIELD_NUMBER: _ClassVar[int]
    NORMALENERGIZEDLOOPMRIDS_FIELD_NUMBER: _ClassVar[int]
    ec: _EquipmentContainer_pb2.EquipmentContainer
    subGeographicalRegionMRID: str
    normalEnergizedFeederMRIDs: _containers.RepeatedScalarFieldContainer[str]
    loopMRIDs: _containers.RepeatedScalarFieldContainer[str]
    circuitMRIDs: _containers.RepeatedScalarFieldContainer[str]
    normalEnergizedLoopMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, ec: _Optional[_Union[_EquipmentContainer_pb2.EquipmentContainer, _Mapping]] = ..., subGeographicalRegionMRID: _Optional[str] = ..., normalEnergizedFeederMRIDs: _Optional[_Iterable[str]] = ..., loopMRIDs: _Optional[_Iterable[str]] = ..., circuitMRIDs: _Optional[_Iterable[str]] = ..., normalEnergizedLoopMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
