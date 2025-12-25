from zepben.protobuf.cim.iec61970.base.core import Name_pb2 as _Name_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class IdentifiedObject(_message.Message):
    __slots__ = ("mRID", "nameNull", "nameSet", "numDiagramObjectsNull", "numDiagramObjectsSet", "descriptionNull", "descriptionSet", "names")
    MRID_FIELD_NUMBER: _ClassVar[int]
    NAMENULL_FIELD_NUMBER: _ClassVar[int]
    NAMESET_FIELD_NUMBER: _ClassVar[int]
    NUMDIAGRAMOBJECTSNULL_FIELD_NUMBER: _ClassVar[int]
    NUMDIAGRAMOBJECTSSET_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTIONNULL_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTIONSET_FIELD_NUMBER: _ClassVar[int]
    NAMES_FIELD_NUMBER: _ClassVar[int]
    mRID: str
    nameNull: _struct_pb2.NullValue
    nameSet: str
    numDiagramObjectsNull: _struct_pb2.NullValue
    numDiagramObjectsSet: int
    descriptionNull: _struct_pb2.NullValue
    descriptionSet: str
    names: _containers.RepeatedCompositeFieldContainer[_Name_pb2.Name]
    def __init__(self, mRID: _Optional[str] = ..., nameNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., nameSet: _Optional[str] = ..., numDiagramObjectsNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., numDiagramObjectsSet: _Optional[int] = ..., descriptionNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., descriptionSet: _Optional[str] = ..., names: _Optional[_Iterable[_Union[_Name_pb2.Name, _Mapping]]] = ...) -> None: ...
