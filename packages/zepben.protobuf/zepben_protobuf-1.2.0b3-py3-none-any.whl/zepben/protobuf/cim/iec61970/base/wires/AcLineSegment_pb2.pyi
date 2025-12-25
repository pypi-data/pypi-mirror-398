from zepben.protobuf.cim.iec61970.base.wires import Conductor_pb2 as _Conductor_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AcLineSegment(_message.Message):
    __slots__ = ("cd", "perLengthImpedanceMRID", "cutMRIDs", "clampMRIDs")
    CD_FIELD_NUMBER: _ClassVar[int]
    PERLENGTHIMPEDANCEMRID_FIELD_NUMBER: _ClassVar[int]
    CUTMRIDS_FIELD_NUMBER: _ClassVar[int]
    CLAMPMRIDS_FIELD_NUMBER: _ClassVar[int]
    cd: _Conductor_pb2.Conductor
    perLengthImpedanceMRID: str
    cutMRIDs: _containers.RepeatedScalarFieldContainer[str]
    clampMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, cd: _Optional[_Union[_Conductor_pb2.Conductor, _Mapping]] = ..., perLengthImpedanceMRID: _Optional[str] = ..., cutMRIDs: _Optional[_Iterable[str]] = ..., clampMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
