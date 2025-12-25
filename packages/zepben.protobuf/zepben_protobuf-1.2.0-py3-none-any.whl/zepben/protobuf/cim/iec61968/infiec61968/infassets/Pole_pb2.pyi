from zepben.protobuf.cim.iec61968.assets import Structure_pb2 as _Structure_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Pole(_message.Message):
    __slots__ = ("st", "streetlightMRIDs", "classificationNull", "classificationSet")
    ST_FIELD_NUMBER: _ClassVar[int]
    STREETLIGHTMRIDS_FIELD_NUMBER: _ClassVar[int]
    CLASSIFICATIONNULL_FIELD_NUMBER: _ClassVar[int]
    CLASSIFICATIONSET_FIELD_NUMBER: _ClassVar[int]
    st: _Structure_pb2.Structure
    streetlightMRIDs: _containers.RepeatedScalarFieldContainer[str]
    classificationNull: _struct_pb2.NullValue
    classificationSet: str
    def __init__(self, st: _Optional[_Union[_Structure_pb2.Structure, _Mapping]] = ..., streetlightMRIDs: _Optional[_Iterable[str]] = ..., classificationNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., classificationSet: _Optional[str] = ...) -> None: ...
