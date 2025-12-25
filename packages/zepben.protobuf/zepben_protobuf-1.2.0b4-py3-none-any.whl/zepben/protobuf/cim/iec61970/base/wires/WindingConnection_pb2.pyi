from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class WindingConnection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WINDING_CONNECTION_UNKNOWN: _ClassVar[WindingConnection]
    WINDING_CONNECTION_D: _ClassVar[WindingConnection]
    WINDING_CONNECTION_Y: _ClassVar[WindingConnection]
    WINDING_CONNECTION_Z: _ClassVar[WindingConnection]
    WINDING_CONNECTION_YN: _ClassVar[WindingConnection]
    WINDING_CONNECTION_ZN: _ClassVar[WindingConnection]
    WINDING_CONNECTION_A: _ClassVar[WindingConnection]
    WINDING_CONNECTION_I: _ClassVar[WindingConnection]
WINDING_CONNECTION_UNKNOWN: WindingConnection
WINDING_CONNECTION_D: WindingConnection
WINDING_CONNECTION_Y: WindingConnection
WINDING_CONNECTION_Z: WindingConnection
WINDING_CONNECTION_YN: WindingConnection
WINDING_CONNECTION_ZN: WindingConnection
WINDING_CONNECTION_A: WindingConnection
WINDING_CONNECTION_I: WindingConnection
