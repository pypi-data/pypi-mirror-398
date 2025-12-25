from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Loop(_message.Message):
    __slots__ = ("io", "circuitMRIDs", "substationMRIDs", "normalEnergizingSubstationMRIDs")
    IO_FIELD_NUMBER: _ClassVar[int]
    CIRCUITMRIDS_FIELD_NUMBER: _ClassVar[int]
    SUBSTATIONMRIDS_FIELD_NUMBER: _ClassVar[int]
    NORMALENERGIZINGSUBSTATIONMRIDS_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    circuitMRIDs: _containers.RepeatedScalarFieldContainer[str]
    substationMRIDs: _containers.RepeatedScalarFieldContainer[str]
    normalEnergizingSubstationMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., circuitMRIDs: _Optional[_Iterable[str]] = ..., substationMRIDs: _Optional[_Iterable[str]] = ..., normalEnergizingSubstationMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
