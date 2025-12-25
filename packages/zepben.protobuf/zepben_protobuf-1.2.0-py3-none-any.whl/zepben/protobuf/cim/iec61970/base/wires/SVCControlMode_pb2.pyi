from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class SVCControlMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SVC_CONTROL_MODE_UNKNOWN: _ClassVar[SVCControlMode]
    SVC_CONTROL_MODE_REACTIVE_POWER: _ClassVar[SVCControlMode]
    SVC_CONTROL_MODE_VOLTAGE: _ClassVar[SVCControlMode]
SVC_CONTROL_MODE_UNKNOWN: SVCControlMode
SVC_CONTROL_MODE_REACTIVE_POWER: SVCControlMode
SVC_CONTROL_MODE_VOLTAGE: SVCControlMode
