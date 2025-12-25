from zepben.protobuf.cim.iec61970.base.diagramlayout import DiagramObjectPoint_pb2 as _DiagramObjectPoint_pb2
from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DiagramObject(_message.Message):
    __slots__ = ("io", "diagramMRID", "identifiedObjectMRID", "diagramObjectStyleNull", "diagramObjectStyleSet", "rotation", "diagramObjectPoints")
    IO_FIELD_NUMBER: _ClassVar[int]
    DIAGRAMMRID_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIEDOBJECTMRID_FIELD_NUMBER: _ClassVar[int]
    DIAGRAMOBJECTSTYLENULL_FIELD_NUMBER: _ClassVar[int]
    DIAGRAMOBJECTSTYLESET_FIELD_NUMBER: _ClassVar[int]
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    DIAGRAMOBJECTPOINTS_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    diagramMRID: str
    identifiedObjectMRID: str
    diagramObjectStyleNull: _struct_pb2.NullValue
    diagramObjectStyleSet: str
    rotation: float
    diagramObjectPoints: _containers.RepeatedCompositeFieldContainer[_DiagramObjectPoint_pb2.DiagramObjectPoint]
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., diagramMRID: _Optional[str] = ..., identifiedObjectMRID: _Optional[str] = ..., diagramObjectStyleNull: _Optional[_Union[_struct_pb2.NullValue, str]] = ..., diagramObjectStyleSet: _Optional[str] = ..., rotation: _Optional[float] = ..., diagramObjectPoints: _Optional[_Iterable[_Union[_DiagramObjectPoint_pb2.DiagramObjectPoint, _Mapping]]] = ...) -> None: ...
