from google.protobuf import any_pb2 as _any_pb2
from zepben.protobuf.cim.iec61970.base.diagramlayout import Diagram_pb2 as _Diagram_pb2
from zepben.protobuf.cim.iec61970.base.diagramlayout import DiagramObject_pb2 as _DiagramObject_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DiagramIdentifiedObject(_message.Message):
    __slots__ = ("diagram", "diagramObject", "other")
    DIAGRAM_FIELD_NUMBER: _ClassVar[int]
    DIAGRAMOBJECT_FIELD_NUMBER: _ClassVar[int]
    OTHER_FIELD_NUMBER: _ClassVar[int]
    diagram: _Diagram_pb2.Diagram
    diagramObject: _DiagramObject_pb2.DiagramObject
    other: _any_pb2.Any
    def __init__(self, diagram: _Optional[_Union[_Diagram_pb2.Diagram, _Mapping]] = ..., diagramObject: _Optional[_Union[_DiagramObject_pb2.DiagramObject, _Mapping]] = ..., other: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
