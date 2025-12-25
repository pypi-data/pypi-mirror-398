from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class PotentialTransformerKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    POTENTIAL_TRANSFORMER_KIND_UNKNOWN: _ClassVar[PotentialTransformerKind]
    POTENTIAL_TRANSFORMER_KIND_INDUCTIVE: _ClassVar[PotentialTransformerKind]
    POTENTIAL_TRANSFORMER_KIND_CAPACITIVE_COUPLING: _ClassVar[PotentialTransformerKind]
POTENTIAL_TRANSFORMER_KIND_UNKNOWN: PotentialTransformerKind
POTENTIAL_TRANSFORMER_KIND_INDUCTIVE: PotentialTransformerKind
POTENTIAL_TRANSFORMER_KIND_CAPACITIVE_COUPLING: PotentialTransformerKind
