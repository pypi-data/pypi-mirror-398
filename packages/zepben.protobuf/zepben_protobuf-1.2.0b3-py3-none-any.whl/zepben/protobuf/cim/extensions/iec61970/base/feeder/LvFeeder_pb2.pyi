from zepben.protobuf.cim.iec61970.base.core import EquipmentContainer_pb2 as _EquipmentContainer_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LvFeeder(_message.Message):
    __slots__ = ("ec", "normalHeadTerminalMRID", "normalEnergizingFeederMRIDs", "currentlyEnergizingFeederMRIDs")
    EC_FIELD_NUMBER: _ClassVar[int]
    NORMALHEADTERMINALMRID_FIELD_NUMBER: _ClassVar[int]
    NORMALENERGIZINGFEEDERMRIDS_FIELD_NUMBER: _ClassVar[int]
    CURRENTLYENERGIZINGFEEDERMRIDS_FIELD_NUMBER: _ClassVar[int]
    ec: _EquipmentContainer_pb2.EquipmentContainer
    normalHeadTerminalMRID: str
    normalEnergizingFeederMRIDs: _containers.RepeatedScalarFieldContainer[str]
    currentlyEnergizingFeederMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, ec: _Optional[_Union[_EquipmentContainer_pb2.EquipmentContainer, _Mapping]] = ..., normalHeadTerminalMRID: _Optional[str] = ..., normalEnergizingFeederMRIDs: _Optional[_Iterable[str]] = ..., currentlyEnergizingFeederMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
