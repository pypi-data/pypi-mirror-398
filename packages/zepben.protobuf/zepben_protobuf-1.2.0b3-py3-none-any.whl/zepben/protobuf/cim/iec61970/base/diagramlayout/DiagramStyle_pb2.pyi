from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class DiagramStyle(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DIAGRAM_STYLE_SCHEMATIC: _ClassVar[DiagramStyle]
    DIAGRAM_STYLE_GEOGRAPHIC: _ClassVar[DiagramStyle]
DIAGRAM_STYLE_SCHEMATIC: DiagramStyle
DIAGRAM_STYLE_GEOGRAPHIC: DiagramStyle
