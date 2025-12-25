from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class StreetlightLampKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STREETLIGHT_LAMP_KIND_UNKNOWN: _ClassVar[StreetlightLampKind]
    STREETLIGHT_LAMP_KIND_HIGH_PRESSURE_SODIUM: _ClassVar[StreetlightLampKind]
    STREETLIGHT_LAMP_KIND_MERCURY_VAPOR: _ClassVar[StreetlightLampKind]
    STREETLIGHT_LAMP_KIND_METAL_HALIDE: _ClassVar[StreetlightLampKind]
    STREETLIGHT_LAMP_KIND_OTHER: _ClassVar[StreetlightLampKind]
STREETLIGHT_LAMP_KIND_UNKNOWN: StreetlightLampKind
STREETLIGHT_LAMP_KIND_HIGH_PRESSURE_SODIUM: StreetlightLampKind
STREETLIGHT_LAMP_KIND_MERCURY_VAPOR: StreetlightLampKind
STREETLIGHT_LAMP_KIND_METAL_HALIDE: StreetlightLampKind
STREETLIGHT_LAMP_KIND_OTHER: StreetlightLampKind
