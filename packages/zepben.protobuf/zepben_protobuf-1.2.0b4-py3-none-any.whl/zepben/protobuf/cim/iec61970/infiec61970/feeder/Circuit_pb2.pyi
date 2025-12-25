from zepben.protobuf.cim.iec61970.base.wires import Line_pb2 as _Line_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Circuit(_message.Message):
    __slots__ = ("l", "endTerminalMRIDs", "loopMRID", "endSubstationMRIDs")
    L_FIELD_NUMBER: _ClassVar[int]
    ENDTERMINALMRIDS_FIELD_NUMBER: _ClassVar[int]
    LOOPMRID_FIELD_NUMBER: _ClassVar[int]
    ENDSUBSTATIONMRIDS_FIELD_NUMBER: _ClassVar[int]
    l: _Line_pb2.Line
    endTerminalMRIDs: _containers.RepeatedScalarFieldContainer[str]
    loopMRID: str
    endSubstationMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, l: _Optional[_Union[_Line_pb2.Line, _Mapping]] = ..., endTerminalMRIDs: _Optional[_Iterable[str]] = ..., loopMRID: _Optional[str] = ..., endSubstationMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
