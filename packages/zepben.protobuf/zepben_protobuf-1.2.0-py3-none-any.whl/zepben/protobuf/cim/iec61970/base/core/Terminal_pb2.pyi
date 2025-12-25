from zepben.protobuf.cim.iec61970.base.core import AcDcTerminal_pb2 as _AcDcTerminal_pb2
from zepben.protobuf.cim.iec61970.base.core import PhaseCode_pb2 as _PhaseCode_pb2
from zepben.protobuf.network.model import FeederDirection_pb2 as _FeederDirection_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Terminal(_message.Message):
    __slots__ = ("ad", "conductingEquipmentMRID", "connectivityNodeMRID", "phases", "tracedPhases", "sequenceNumber", "normalFeederDirection", "currentFeederDirection")
    AD_FIELD_NUMBER: _ClassVar[int]
    CONDUCTINGEQUIPMENTMRID_FIELD_NUMBER: _ClassVar[int]
    CONNECTIVITYNODEMRID_FIELD_NUMBER: _ClassVar[int]
    PHASES_FIELD_NUMBER: _ClassVar[int]
    TRACEDPHASES_FIELD_NUMBER: _ClassVar[int]
    SEQUENCENUMBER_FIELD_NUMBER: _ClassVar[int]
    NORMALFEEDERDIRECTION_FIELD_NUMBER: _ClassVar[int]
    CURRENTFEEDERDIRECTION_FIELD_NUMBER: _ClassVar[int]
    ad: _AcDcTerminal_pb2.AcDcTerminal
    conductingEquipmentMRID: str
    connectivityNodeMRID: str
    phases: _PhaseCode_pb2.PhaseCode
    tracedPhases: int
    sequenceNumber: int
    normalFeederDirection: _FeederDirection_pb2.FeederDirection
    currentFeederDirection: _FeederDirection_pb2.FeederDirection
    def __init__(self, ad: _Optional[_Union[_AcDcTerminal_pb2.AcDcTerminal, _Mapping]] = ..., conductingEquipmentMRID: _Optional[str] = ..., connectivityNodeMRID: _Optional[str] = ..., phases: _Optional[_Union[_PhaseCode_pb2.PhaseCode, str]] = ..., tracedPhases: _Optional[int] = ..., sequenceNumber: _Optional[int] = ..., normalFeederDirection: _Optional[_Union[_FeederDirection_pb2.FeederDirection, str]] = ..., currentFeederDirection: _Optional[_Union[_FeederDirection_pb2.FeederDirection, str]] = ...) -> None: ...
