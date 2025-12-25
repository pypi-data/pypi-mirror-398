from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class PhaseShuntConnectionKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PHASE_SHUNT_CONNECTION_KIND_UNKNOWN: _ClassVar[PhaseShuntConnectionKind]
    PHASE_SHUNT_CONNECTION_KIND_D: _ClassVar[PhaseShuntConnectionKind]
    PHASE_SHUNT_CONNECTION_KIND_Y: _ClassVar[PhaseShuntConnectionKind]
    PHASE_SHUNT_CONNECTION_KIND_YN: _ClassVar[PhaseShuntConnectionKind]
    PHASE_SHUNT_CONNECTION_KIND_I: _ClassVar[PhaseShuntConnectionKind]
    PHASE_SHUNT_CONNECTION_KIND_G: _ClassVar[PhaseShuntConnectionKind]
PHASE_SHUNT_CONNECTION_KIND_UNKNOWN: PhaseShuntConnectionKind
PHASE_SHUNT_CONNECTION_KIND_D: PhaseShuntConnectionKind
PHASE_SHUNT_CONNECTION_KIND_Y: PhaseShuntConnectionKind
PHASE_SHUNT_CONNECTION_KIND_YN: PhaseShuntConnectionKind
PHASE_SHUNT_CONNECTION_KIND_I: PhaseShuntConnectionKind
PHASE_SHUNT_CONNECTION_KIND_G: PhaseShuntConnectionKind
