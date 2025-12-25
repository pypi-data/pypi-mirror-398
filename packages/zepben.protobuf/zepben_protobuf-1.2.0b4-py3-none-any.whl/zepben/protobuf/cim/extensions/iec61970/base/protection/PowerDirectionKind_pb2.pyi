from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class PowerDirectionKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    POWER_DIRECTION_KIND_UNKNOWN: _ClassVar[PowerDirectionKind]
    POWER_DIRECTION_KIND_UNDIRECTED: _ClassVar[PowerDirectionKind]
    POWER_DIRECTION_KIND_FORWARD: _ClassVar[PowerDirectionKind]
    POWER_DIRECTION_KIND_REVERSE: _ClassVar[PowerDirectionKind]
POWER_DIRECTION_KIND_UNKNOWN: PowerDirectionKind
POWER_DIRECTION_KIND_UNDIRECTED: PowerDirectionKind
POWER_DIRECTION_KIND_FORWARD: PowerDirectionKind
POWER_DIRECTION_KIND_REVERSE: PowerDirectionKind
