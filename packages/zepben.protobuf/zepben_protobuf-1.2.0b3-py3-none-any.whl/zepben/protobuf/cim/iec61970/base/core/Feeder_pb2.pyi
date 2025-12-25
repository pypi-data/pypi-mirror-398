from zepben.protobuf.cim.iec61970.base.core import EquipmentContainer_pb2 as _EquipmentContainer_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Feeder(_message.Message):
    __slots__ = ("ec", "normalHeadTerminalMRID", "normalEnergizingSubstationMRID", "normalEnergizedLvFeederMRIDs", "currentlyEnergizedLvFeedersMRIDs")
    EC_FIELD_NUMBER: _ClassVar[int]
    NORMALHEADTERMINALMRID_FIELD_NUMBER: _ClassVar[int]
    NORMALENERGIZINGSUBSTATIONMRID_FIELD_NUMBER: _ClassVar[int]
    NORMALENERGIZEDLVFEEDERMRIDS_FIELD_NUMBER: _ClassVar[int]
    CURRENTLYENERGIZEDLVFEEDERSMRIDS_FIELD_NUMBER: _ClassVar[int]
    ec: _EquipmentContainer_pb2.EquipmentContainer
    normalHeadTerminalMRID: str
    normalEnergizingSubstationMRID: str
    normalEnergizedLvFeederMRIDs: _containers.RepeatedScalarFieldContainer[str]
    currentlyEnergizedLvFeedersMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, ec: _Optional[_Union[_EquipmentContainer_pb2.EquipmentContainer, _Mapping]] = ..., normalHeadTerminalMRID: _Optional[str] = ..., normalEnergizingSubstationMRID: _Optional[str] = ..., normalEnergizedLvFeederMRIDs: _Optional[_Iterable[str]] = ..., currentlyEnergizedLvFeedersMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
