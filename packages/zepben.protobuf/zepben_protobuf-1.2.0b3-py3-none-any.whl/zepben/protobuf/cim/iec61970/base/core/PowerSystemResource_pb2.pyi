from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PowerSystemResource(_message.Message):
    __slots__ = ("io", "assetInfoMRID", "locationMRID", "numControlsNull", "numControlsSet", "assetMRIDs")
    IO_FIELD_NUMBER: _ClassVar[int]
    ASSETINFOMRID_FIELD_NUMBER: _ClassVar[int]
    LOCATIONMRID_FIELD_NUMBER: _ClassVar[int]
    NUMCONTROLSNULL_FIELD_NUMBER: _ClassVar[int]
    NUMCONTROLSSET_FIELD_NUMBER: _ClassVar[int]
    ASSETMRIDS_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    assetInfoMRID: str
    locationMRID: str
    numControlsNull: _struct_pb2.NullValue
    numControlsSet: int
    assetMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., assetInfoMRID: _Optional[str] = ..., locationMRID: _Optional[str] = ..., numControlsNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., numControlsSet: _Optional[int] = ..., assetMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
