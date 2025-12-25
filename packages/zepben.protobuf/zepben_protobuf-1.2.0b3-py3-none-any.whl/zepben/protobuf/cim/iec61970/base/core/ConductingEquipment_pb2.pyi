from zepben.protobuf.cim.iec61970.base.core import Equipment_pb2 as _Equipment_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ConductingEquipment(_message.Message):
    __slots__ = ("eq", "baseVoltageMRID", "terminalMRIDs")
    EQ_FIELD_NUMBER: _ClassVar[int]
    BASEVOLTAGEMRID_FIELD_NUMBER: _ClassVar[int]
    TERMINALMRIDS_FIELD_NUMBER: _ClassVar[int]
    eq: _Equipment_pb2.Equipment
    baseVoltageMRID: str
    terminalMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, eq: _Optional[_Union[_Equipment_pb2.Equipment, _Mapping]] = ..., baseVoltageMRID: _Optional[str] = ..., terminalMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
