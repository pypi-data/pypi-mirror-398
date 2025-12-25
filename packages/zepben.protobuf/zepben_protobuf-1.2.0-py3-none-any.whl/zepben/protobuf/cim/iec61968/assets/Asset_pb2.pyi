from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Asset(_message.Message):
    __slots__ = ("io", "organisationRoleMRIDs", "locationMRID", "powerSystemResourceMRIDs")
    IO_FIELD_NUMBER: _ClassVar[int]
    ORGANISATIONROLEMRIDS_FIELD_NUMBER: _ClassVar[int]
    LOCATIONMRID_FIELD_NUMBER: _ClassVar[int]
    POWERSYSTEMRESOURCEMRIDS_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    organisationRoleMRIDs: _containers.RepeatedScalarFieldContainer[str]
    locationMRID: str
    powerSystemResourceMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., organisationRoleMRIDs: _Optional[_Iterable[str]] = ..., locationMRID: _Optional[str] = ..., powerSystemResourceMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
