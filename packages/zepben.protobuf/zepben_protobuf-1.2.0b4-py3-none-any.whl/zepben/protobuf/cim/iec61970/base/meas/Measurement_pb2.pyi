from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from zepben.protobuf.cim.iec61970.base.core import PhaseCode_pb2 as _PhaseCode_pb2
from zepben.protobuf.cim.iec61970.base.domain import UnitSymbol_pb2 as _UnitSymbol_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Measurement(_message.Message):
    __slots__ = ("io", "powerSystemResourceMRID", "remoteSourceMRID", "terminalMRID", "phases", "unitSymbol")
    IO_FIELD_NUMBER: _ClassVar[int]
    POWERSYSTEMRESOURCEMRID_FIELD_NUMBER: _ClassVar[int]
    REMOTESOURCEMRID_FIELD_NUMBER: _ClassVar[int]
    TERMINALMRID_FIELD_NUMBER: _ClassVar[int]
    PHASES_FIELD_NUMBER: _ClassVar[int]
    UNITSYMBOL_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    powerSystemResourceMRID: str
    remoteSourceMRID: str
    terminalMRID: str
    phases: _PhaseCode_pb2.PhaseCode
    unitSymbol: _UnitSymbol_pb2.UnitSymbol
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., powerSystemResourceMRID: _Optional[str] = ..., remoteSourceMRID: _Optional[str] = ..., terminalMRID: _Optional[str] = ..., phases: _Optional[_Union[_PhaseCode_pb2.PhaseCode, str]] = ..., unitSymbol: _Optional[_Union[_UnitSymbol_pb2.UnitSymbol, str]] = ...) -> None: ...
