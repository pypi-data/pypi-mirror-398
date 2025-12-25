from zepben.protobuf.cim.iec61970.base.core import IdentifiedObject_pb2 as _IdentifiedObject_pb2
from zepben.protobuf.cim.iec61970.base.diagramlayout import DiagramStyle_pb2 as _DiagramStyle_pb2
from zepben.protobuf.cim.iec61970.base.diagramlayout import OrientationKind_pb2 as _OrientationKind_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Diagram(_message.Message):
    __slots__ = ("io", "diagramStyle", "orientationKind", "diagramObjectMRIDs")
    IO_FIELD_NUMBER: _ClassVar[int]
    DIAGRAMSTYLE_FIELD_NUMBER: _ClassVar[int]
    ORIENTATIONKIND_FIELD_NUMBER: _ClassVar[int]
    DIAGRAMOBJECTMRIDS_FIELD_NUMBER: _ClassVar[int]
    io: _IdentifiedObject_pb2.IdentifiedObject
    diagramStyle: _DiagramStyle_pb2.DiagramStyle
    orientationKind: _OrientationKind_pb2.OrientationKind
    diagramObjectMRIDs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, io: _Optional[_Union[_IdentifiedObject_pb2.IdentifiedObject, _Mapping]] = ..., diagramStyle: _Optional[_Union[_DiagramStyle_pb2.DiagramStyle, str]] = ..., orientationKind: _Optional[_Union[_OrientationKind_pb2.OrientationKind, str]] = ..., diagramObjectMRIDs: _Optional[_Iterable[str]] = ...) -> None: ...
